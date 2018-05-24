# sudo apt-get install python-opencv
import time
import cv2
import datetime
from itertools import izip
from PIL import Image

def takePhoto():
	camera_port = 0
	camera = cv2.VideoCapture(camera_port)
	time.sleep(0.1)  # If you don't wait, the image will be dark
	return_value, image = camera.read()
	del(camera)
	return image

def getDiff(i1, i2):
	assert i1.mode == i2.mode, "Different kinds of images."
	assert i1.size == i2.size, "Different sizes."

	pairs = izip(i1.getdata(), i2.getdata())
	if len(i1.getbands()) == 1:
	    # for gray-scale jpegs
	    dif = sum(abs(p1-p2) for p1,p2 in pairs)
	else:
	    dif = sum(abs(c1-c2) for p1,p2 in pairs for c1,c2 in zip(p1,p2))

	ncomponents = i1.size[0] * i1.size[1] * 3
	return (dif / 255.0 * 100) / ncomponents

image1 = Image.fromarray(takePhoto())

while (True):
	time.sleep(0.1)
	image2 = Image.fromarray(takePhoto())
	diff = getDiff(image1, image2)
	image1 = image2

	if (diff > 5):
		print "Motion detected!"