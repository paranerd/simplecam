# sudo apt install python3-pip ffmpeg
# pip3 install opencv-python
# maybe: sudo apt install python3-opencv

import os, sys, time, math, getopt
import numpy as np
import cv2
import threading
import subprocess
from collections import deque
from datetime import datetime

from util import Util

class MotionDetector(threading.Thread):
	def __init__(self, source=None, doRecord=True, doDisplay=True, doAddContours=True, doAddTarget=False):
		threading.Thread.__init__(self)

		self.name = "MotionDetector"
		self.archive = "archive"

		self.writer = None
		self.master = None
		self.currentFrame = None

		self.codec = cv2.VideoWriter_fourcc('M','J', 'P', 'G')
		#self.codec = 0x7634706d #cv2.VideoWriter_fourcc('M','P', '4', 'V')
		#self.codec = cv2.VideoWriter_fourcc('X','2', '6', '4')
		#self.codec = 0x31637661
		self.stillLimit = 5
		self.threshold = 15

		self.doDisplay = doDisplay
		self.doRecord = doRecord
		self.doAddContours = doAddContours
		self.doAddTarget = doAddTarget
		self.currentFile = None

		self.source = cv2.VideoCapture(source) if source is not None else self.initCamera()

		self.fps = 22 #self.findFPS(self.source)
		self.height, self.width = self.setDimensions(self.source)

		self.noiseDetector = None
		self.detected = False

	def __del__(self):
		# Release camera
		self.source.release()

		# Close all windows
		cv2.destroyAllWindows()

	def getFrame(self):
		if self.currentFrame is not None:
			ret, jpeg = cv2.imencode('.jpg', self.currentFrame)
			return jpeg.tobytes()

		return None

	def setDimensions(self, source):
		frame = cv2.cvtColor(source.read()[1],cv2.COLOR_RGB2GRAY)
		return frame.shape[0: 2]

	def findFPS(self, source, num_frames=120):
		Util.log(self.name, "Determining FPS...")

		# Start time
		start = time.time()

		# Grab a few frames
		for i in range(0, num_frames):
			ret, frame = source.read()

		# End time
		end = time.time()

		# Time elapsed
		seconds = end - start

		# Calculate frames per second
		fps = int(math.floor(num_frames / seconds))
		Util.log(self.name, "Setting FPS to " + str(fps))
		return fps

	def initCamera(self):
		# init camera
		camera = cv2.VideoCapture(0)
		camera.set(3,320)
		camera.set(4,240)
		time.sleep(0.5)

		return camera

	def startRecorder(self):
		'''
		Create the recorder
		'''
		# Set filename
		self.currentFile = self.archive + "/" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".avi"
		# Set path and FPS
		self.writer = cv2.VideoWriter(self.currentFile, self.codec, self.fps, (self.width, self.height))
		#self.writer = cv2.VideoWriter("archive/" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4", self.codec, self.fps, (320,240))

	def stopRecorder(self):
		self.writer = None
		self.currentFile = None

	def convertToMp4(self, removeSource=True):
		# Build destination path
		filename, extension = os.path.splitext(self.currentFile)
		destination = filename + ".mp4"

		try:
			Util.log(self.name, "Converting video...")
			cmd = 'ffmpeg -i ' + self.currentFile + ' ' + destination + ' 2> /dev/null'
			p = subprocess.Popen(cmd, shell=True)
			(output, err) = p.communicate()
			Util.log(self.name, "Done.")

			if removeSource and os.path.isfile(destination):
				os.remove(self.currentFile)
		except subprocess.CalledProcessError:
			Util.log(self.name, "Error converting")

	def run(self):
		slidWin = deque(maxlen=self.fps * self.stillLimit)
		framesWritten = 0

		while True:
			# Grab a frame
			(grabbed, self.currentFrame) = self.source.read()

			# End of feed
			if not grabbed:
				break

			frameToSave = self.currentFrame

			# Gray frame
			frame1 = cv2.cvtColor(self.currentFrame, cv2.COLOR_BGR2GRAY)

			# Blur frame
			frame2 = cv2.GaussianBlur(frame1,(21,21),0)

			# Initialize master
			if self.master is None:
				self.master = frame2
				continue

			# Delta frame
			frame3 = cv2.absdiff(self.master, frame2)

			# Threshold frame
			frame4 = cv2.threshold(frame3,15,255,cv2.THRESH_BINARY)[1]

			# Dilate the thresholded image to fill in holes
			kernel = np.ones((5,5),np.uint8)
			frameDilated = cv2.dilate(frame4,kernel,iterations=4)

			# Find difference in percent
			res = frameDilated.astype(np.uint8)
			movement = (np.count_nonzero(res) * 100) / res.size

			# Add movement percentage to sliding window
			slidWin.append(movement)

			if self.doAddContours or self.doAddTarget:
				frameToSave, targets = self.addContours(self.currentFrame, frameDilated)

				if self.doAddTarget:
					frameToSave = self.addTarget(self.currentFrame, targets)

			self.detected = sum([x > self.threshold for x in slidWin]) > 0 # and movement > self.threshold

			if self.detected is True or (self.noiseDetector is not None and self.noiseDetector.hasDetected()): # os.path.isfile('noise.lock'):
				if self.writer is None:
					Util.log(self.name, "Motion detected! Recording...")
					self.startRecorder()

				self.writer.write(frameToSave)
			elif self.writer is not None:
				Util.log(self.name, "Saving video...")

				# Convert
				self.convertToMp4()

				# Reset all
				self.stopRecorder()

				Util.log(self.name, "Observing...")

			# Update master
			self.master = frame2

			# Display
			if self.doDisplay:
				cv2.imshow("Current frame:", self.currentFrame)

			# key delay and action
			key = cv2.waitKey(1) & 0xFF

			if key == ord('q'):
				break
			elif key != 255:
				Util.log('key:',[chr(key)])

	def addContours(self, frameRaw, frameDilated):
		# Find contours on thresholded image
		nada, contours, nada = cv2.findContours(frameDilated.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

		# make coutour frame
		frameContour = frameRaw.copy()

		# target contours
		targets = []

		# loop over the contour
		for c in contours:
			# if the contour is too small, ignore it
			if cv2.contourArea(c) < 500:
				# make sure this has a less than sign, not an html escape
				continue

			# contour data
			M = cv2.moments(c)#;Util.log( M )
			cx = int(M['m10']/M['m00'])
			cy = int(M['m01']/M['m00'])
			x, y, w, h = cv2.boundingRect(c)
			rx = x + int(w / 2)
			ry = y + int(h / 2)
			ca = cv2.contourArea(c)

			# plot contours
			cv2.drawContours(frameContour,[c],0,(0,0,255),2)
			cv2.rectangle(frameContour,(x,y),(x+w,y+h),(0,255,0),2)
			cv2.circle(frameContour,(cx,cy),2,(0,0,255),2)
			cv2.circle(frameContour,(rx,ry),2,(0,255,0),2)

			# save target contours
			targets.append((rx,ry,ca))

		return frameContour, targets

	def addTarget(self, frameRaw, targets):
		# make target
		area = sum([x[2] for x in targets])
		mx = 0
		my = 0

		if targets:
			for x, y, a in targets:
				mx += x
				my += y
			mx = int(round(mx / len(targets), 0))
			my = int(round(my / len(targets), 0))

		# plot target
		tr = 50
		frameTarget = frameRaw.copy()

		if targets:
			cv2.circle(frameTarget, (mx, my), tr, (0, 0, 255, 0), 2)
			cv2.line(frameTarget, (mx - tr, my), (mx + tr, my), (0, 0, 255, 0), 2)
			cv2.line(frameTarget, (mx, my - tr), (mx, my + tr), (0, 0, 255, 0), 2)

		return frameTarget

	def sync(self, nd):
		self.noiseDetector = nd

	def hasDetected(self):
		return self.detected

if __name__ == "__main__":
	args = sys.argv[1:]
	source = None

	try:
		opts, args = getopt.getopt(args, "hs:",["source="])
	except getopt.GetoptError:
		print('python3 motion_detector.py -s <source>')
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			print('python3 motion_detector.py -s <source>')
			sys.exit()
		elif opt in ("-s", "--source"):
			source = arg.strip()

	if source is not None:
		print('Input: ', source)
	else:
		print('Input: Camera')

	if source is not None and not os.path.isfile(source):
		print(str(source) + " does not exist")
	else:
		md = MotionDetector(source=source)
		md.start()
