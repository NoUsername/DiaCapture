#!/bin/bash
set -e

function nextDia() {
  read -e -p "Please push 'next' on projector and press [enter]" ignored
}

function takePic() {
  gphoto2 --capture-image
}

function getPic() {
  # fetch all files to current dir
  gphoto2 --get-all-files
  # delete all files from camera
  gphoto2 -D -R
}

while true; do
	nextDia
	takePic
	getPic
done
