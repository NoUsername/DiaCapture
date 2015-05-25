#!/usr/bin/env python

from __future__ import print_function

import logging
import os
import re
import six
import subprocess
import sys
import termios
import time
import yaml
from multiprocessing import Process, Queue

import gphoto2 as gp

MIN_WAIT_TRIGGER = 10
TRIGGER_SEC_AFTER_SHOOT = 2
ASK_FOR_BASEPATH = False
SERIAL = "/dev/ttyUSB0"
SETTINGS_FILE = "./settings.yaml"

context = None
camera = None
lastPath = "~/dias/uncropped/"
lastFolderName = "firstBatch"
lastCount = 50
autoTrigger = True
trigger = None

def readSettings():
	global lastPath, lastFolderName, lastCount
	if os.path.exists(SETTINGS_FILE):
		with open(SETTINGS_FILE, 'r') as f:
			settings = yaml.load(f)
			lastPath = settings.get('basePath', lastPath)
			lastFolderName = settings.get('folderName', lastFolderName)
			lastCount = settings.get('lastCount', lastCount)

readSettings()

# send via q how long to wait before next trigger (in seconds) or x to quit
def triggerNextDia(qIn, qOut):
	SERIAL_FILE = open(SERIAL, 'w')
	# give arduino time to boot
	time.sleep(2)
	SERIAL_FILE.write(" ")
	SERIAL_FILE.flush()
	print("trigger process started")
	v = qIn.get()
	first = True
	while v != 'x':
		print("sleeping for %s"%v)
		if first:
			# for some reason first time needs to be longer, probably serial/arduino related
			v += 2
			first = False
		time.sleep(v)
		if autoTrigger:
			print("triggering 'next' button on projector")
			SERIAL_FILE.write("c")
			SERIAL_FILE.flush()
		qOut.put("done")
		v = qIn.get()
	SERIAL_FILE.close()
	print("trigger process gone")

class Trigger:

	def __init__(self):
		self.q = Queue()
		self.qRet = Queue()
		self.p = Process(target=triggerNextDia, args=(self.q, self.qRet))
		self.p.start()

	def trigger(self, delay):
		self.q.put(delay)

	def wait(self):
		self.qRet.get()

	def close(self):
		self.q.put("x")
		self.p.join()

def initCam():
	global context, camera
	logging.basicConfig(
		format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
	gp.check_result(gp.use_python_logging())
	context = gp.gp_context_new()
	camera = gp.check_result(gp.gp_camera_new())
	gp.check_result(gp.gp_camera_init(camera, context))

def closeCam():
	global context, camera
	gp.check_result(gp.gp_camera_exit(camera, context))
	context = None
	camera = None

def takePic():
	global context, camera
	print('Capturing image')
	file_path = gp.check_result(gp.gp_camera_capture(
		camera, gp.GP_CAPTURE_IMAGE, context))
	print('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
	return file_path

def isJpg(name):
	return bool(re.match(".+\.(jpe?g)", name.lower()))

def copyFromCam(toFolder, file_path):
	global context, camera
	file_name = file_path.name
	target = os.path.join(toFolder, file_name)
	if not isJpg(file_name):
		print("encountered RAW file, putting in 'raw' subdir")
		target = os.path.join(toFolder, "raw", file_name)
		mkdirP(os.path.join(toFolder, "raw"))
	print('Copying image to', target)
	camera_file = gp.check_result(gp.gp_camera_file_get(
			camera, file_path.folder, file_name,
			gp.GP_FILE_TYPE_NORMAL, context))
	gp.check_result(gp.gp_file_save(camera_file, target))

def getVal(desc, default):
	# discard any previos input (prevent old input from answering the question)
	termios.tcflush(sys.stdin, termios.TCIOFLUSH)
	value = raw_input("%s [%s]:"%(desc, default))
	if value.strip() == "":
		return default
	return value

def persistSettings(basePath, folderName, lastCount):
	with open(SETTINGS_FILE, 'w') as f:
		f.write(yaml.dump(dict(basePath=basePath, folderName=folderName, lastCount=lastCount), default_flow_style=False))

def batchSetup():
	global lastFolderName, lastPath, lastCount
	if ASK_FOR_BASEPATH:
		lastPath = getVal("base path", lastPath)
	basePath = lastPath
	folderName = lastFolderName = getVal("folder name", lastFolderName)
	numOfPics = getVal("number of pictures", repr(lastCount))
	lastCount = int(numOfPics)
	persistSettings(basePath, folderName, lastCount)
	return (os.path.expanduser(basePath), folderName, lastCount)

def askMore():
	return getVal("take more pictures? (y/n)", "y").lower() == "y"

def takePics(numOfPics, toFolder):
	for i in xrange(numOfPics):
		print("picture %s/%s"%(i+1, numOfPics))
		trigger.trigger(TRIGGER_SEC_AFTER_SHOOT)
		timeBefore = time.time()
		name = takePic()
		copyFromCam(toFolder, name)
		# make sure triggering was done
		trigger.wait()
		delay = time.time() - timeBefore
		if delay < MIN_WAIT_TRIGGER:
			print("additional waiting...")
			time.sleep(MIN_WAIT_TRIGGER - delay)

def mkdirP(folder):
	if not os.path.exists(folder):
		os.makedirs(folder)

def mainLoop():
	global trigger
	trigger = Trigger()
	time.sleep(2)
	initCam()
	takeMore = True
	while takeMore:
		basePath, folderName, numOfPics = batchSetup()
		toFolder = os.path.join(basePath, folderName)
		mkdirP(toFolder)
		print("taking %s pictures to %s"%(numOfPics, toFolder))
		takePics(numOfPics, toFolder)
		print("%s pictures saved to %s"%(numOfPics, toFolder))
		takeMore = askMore()
	closeCam()
	trigger.close()
	return 0

def cameraTestLoop():
	global autoTrigger, trigger
	print("=== CAMERA SETUP MODE ===\n\ntake pictures of same image repeatedly to find best settings for your camera\n\n")
	initCam()
	autoTrigger = False
	trigger = Trigger()
	takeMore = True
	toFolder = os.path.expanduser("~/testpics")
	mkdirP(toFolder)
	while takeMore:
		takePics(1, toFolder)
		takeMore = getVal("more (y/n)", "y").lower() == "y"
	closeCam()
	trigger.close()

def switchTestLoop():
	print("=== SWITCH TEST MODE ===\n\ntrigger switching images, no photographing\n\n")
	trigger = Trigger()
	more = True
	while more:
		more = getVal("again (y/n)", "y").lower() == "y"
		trigger.trigger(1)
	trigger.close()

if __name__ == "__main__":
	if "setup" in sys.argv:
		cameraTestLoop()
	elif "switch" in sys.argv:
		switchTestLoop()
	else:
		sys.exit(mainLoop())
