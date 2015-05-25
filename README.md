# DiaCapture

Want to capture lots of slides ("Dias" in German) with a DSLr and projector? Then this is the project for you.

My final setup:
- Projector projecting onto white A2 cardboard (canvases for projection are rough to smoothen the image, you don't want that for capturing).
- Arduino controlling a servo to trigger "next slide" button of projector.
- Python script to control Arduino and camera and give you a nice interactive shell (lets you specify folder-name, image-count etc.)
- Shellscript that generate JPEGs from cameras RAW files (to have more post-processing options)
- Shellscript that auto-crops and compresses imagse (they have big black bars around them after capturing)

What you need to replicate this:
- A camera which could be controlled via USB (which is most DSLRs these days)
- An Arduino and a servo to trigger your projectors "next slide" button
- Computer running Linux (tested with Ubuntu 15.04 and 12.04)

## Features

- automatic capturing, if your projector doesn't crap out you can capture entire slide magazines without intervention
- remembers last inputs (foldernames / image counts) through restarts
- uses python multiprocesses to work for you while libgphoto blocks your process
- semi-automatic cropping (separate shellscript)

## Installation

- check out this repo
- assemble arduino stuff, upload project from `buttonPresser` subfolder
- install dependencies (see below)
- create a virtualenv for python and enter it (if you want - you should!)
- run `pip install -r requirements.txt`

```
# install dependencies in Ubuntu
sudo apt-get install gphoto2 libgphoto2-2-dev rawtherapee ufraw imagemagick
```

## Workflow

1. plug in camera 
1. plug in Arduino
1. run `./dias` and follow instructions
1. when you are done capturing your photos run these commands:

```
# if you have set your camera to RAW mode and captured raw images, first produce some JPEGs
# if your camera captured JPEGs directly, you can skip this
./autrt [path to your raw images] [relative path from there for result folder]
# example:
./autort ~/dias/uncropped/firstBatch/raw ..

# now lets crop the images (get rid of black borders)
# the path has to have "uncropped" in it, the resulting files will be put in the same folder except under "cropped"
./autocrop [path of uncropped images]
# example:
./autocrop ~/dias/uncropped/firstBatch
```

DONE! Now you have nice images in ~/dias/cropped/firstBatch to look at ;)

## More commands

The `dias` program also supports this:

```
# enter mode where you can thake the same picture over and over again (no projector control), useful to find good camera settings:
./dias setup

# enter mode where you only control the projector (camera isn't used), useful to test Arduino stuff only
./dias switch
```

For other useful commands see postprocess-helpers.txt

## Notes

The `autort` script currently uses ufraw to do it's work but it also has code in it to do the same via rawtherapee, depending on which one you like better, adapt it to use what you like. I currently go with ufraw mostly for performance reasons.

The `configs` folder contains some configs I am currently using for RawTherapee and Ufraw, they will probably not be the best options for you, so go experiment and create your own if you choose to shoot RAW.

## More info

See http://www.paukl.at/projects/#DiaCapture for more info and some pictures.

This was only possible thanks to these awesome projects: [gphoto2](http://gphoto.org), [RawTherapee](http://rawtherapee.com), [ufraw](http://ufraw.sourcefourge.net), [imagemagick](http://imagemagick.org).