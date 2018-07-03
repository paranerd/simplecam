import cv2
import numpy as np
from datetime import datetime
import time
from collections import deque
import math

from itertools import izip
from PIL import Image

class MotionDetector():
	def __init__(self, showWindows=False, doRecord=False, doTrack=True):
		self.writer         = None
		self.capture        = cv2.VideoCapture(0)
		self.initialized    = time.time()
		self.warmupTime     = 5 # Seconds to adjust luminosity, etc.
		self.codec          = cv2.cv.FOURCC('M', 'J', 'P', 'G')
		self.fps            = 7 #self.findFPS(self.capture) # 15

		self.doRecord       = doRecord
		self.isRecording    = False
		self.recordDuration = 5
		self.triggerTime    = 0
		self.show           = showWindows
		self.track          = doTrack

		self.movement       = 0
		self.threshold      = 0.6
		self.stillLimit     = 2

		# Read three images first
		self.frame1         = cv2.cvtColor(self.capture.read()[1],cv2.COLOR_RGB2GRAY)
		self.frame2         = cv2.cvtColor(self.capture.read()[1],cv2.COLOR_RGB2GRAY)
		self.frame3	        = cv2.cvtColor(self.capture.read()[1],cv2.COLOR_RGB2GRAY)

		self.height, self.width = self.frame3.shape[0: 2]

		if self.show:
			cv2.namedWindow("Image", cv2.WINDOW_AUTOSIZE)
			cv2.namedWindow("Diff", cv2.WINDOW_AUTOSIZE)

	def __del__(self):
		self.capture.release()
		self.writer.release()

	def findFPS(self, source, num_frames=120):
		print("* Determining FPS...")

		# Start time
		start = time.time()

		# Grab a few frames
		for i in xrange(0, num_frames):
			ret, frame = source.read()

		# End time
		end = time.time()

		# Time elapsed
		seconds = end - start

		# Calculate frames per second
		fps = int(math.floor(num_frames / seconds))
		print("* Setting FPS to " + str(fps))
		return fps

	def initRecorder(self):
		'''
		Create the recorder
		'''
		# Set path and FPS
		self.writer = cv2.VideoWriter(datetime.now().strftime("%b-%d_%H:%M:%S")+".avi", self.codec, self.fps, (self.width, self.height))

	def warmup(self):
		# Wait for luminosity adjustments, etc.
		print("* Warming up...")
		remaining = (time.time() - self.initialized - self.warmupTime)
		if (remaining < 0):
			time.sleep(abs(remaining))

	def run(self):
		self.warmup()
		slid_win = deque(maxlen=self.fps * self.stillLimit)
		framesWritten = 0
		print("* Started")

		while True:
			# Capture frame
			success, frame = self.capture.read()

			# Put frames in the right order
			self.frame1 = self.frame2
			self.frame2 = self.frame3
			self.frame3 = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

			# Get difference-frame
			diff = self.diffImg(self.frame1, self.frame2, self.frame3)

			# Get movement-ratio
			movement = self.getMovement(self.frame2, self.frame3)

			# Add frame to sliding window
			slid_win.append(movement)

			if not self.isRecording:
				if movement > self.threshold:
					print("* Movement detected - " + str(time.time()))

					if self.track:
						self.trackMotion(frame, diff)

					if self.doRecord:
						print("* Start recording - " + str(time.time()))
						self.initRecorder()
						self.isRecording = True
			else:
				# Record at least {self.recordDuration} seconds
				# and as long as there's been movement in the last
				# {self.stillLimit} seconds
				if (sum([x > self.threshold for x in slid_win]) == 0 and
					framesWritten >= self.recordDuration * self.fps):
					print("* Stop recording - " + str(time.time()))

					# Reset all
					self.isRecording = False
					framesWritten = 0
					slid_win = deque(maxlen=self.fps * self.stillLimit)
				else:
					print("* Write: " str(datetime.now().strftime("%b-%d_%H:%M:%S")))
					self.writer.write(frame)
					framesWritten += 1

			if self.show:
				cv2.imshow("Diff", diff)
				cv2.imshow("Image", frame)

				key = cv2.waitKey(10)
				if key == 27:
					cv2.destroyAllWindows()
					break

	def diffImg(self, frame1, frame2, frame3):
		# Generate the 'difference' from the 3 captured images...
		i1 = cv2.absdiff(frame3, frame2)
		i2 = cv2.absdiff(frame2, frame1)
		return cv2.bitwise_and(i1, i2) # cv2.bitwise_xor(i1, i2)

	def trackMotion(self, frame, diff):
		thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
		thresh = cv2.dilate(thresh, None, iterations=2)
		(cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		# Loop over the contours
		for c in cnts:
			# If the contour is too small, ignore it
			if cv2.contourArea(c) < 100.0:
				continue

			# Compute the bounding box for the contour, draw it on the frame,
			# and update the text
			(x, y, w, h) = cv2.boundingRect(c)
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

	def getMovement(self, tprev, tc):
		i1 = Image.fromarray(tprev)
		i2 = Image.fromarray(tc)

		pairs = izip(i1.getdata(), i2.getdata())
		if len(i1.getbands()) == 1:
			# For gray-scale jpegs
			dif = sum(abs(p1-p2) for p1,p2 in pairs)
		else:
			dif = sum(abs(c1-c2) for p1,p2 in pairs for c1,c2 in zip(p1,p2))

		ncomponents = i1.size[0] * i1.size[1] * 3

		return ((dif / 255.0 * 100) / ncomponents)

	def getFrame(self):
		success, frame = self.capture.read()

		# We are using Motion JPEG, but OpenCV defaults to capture raw images,
		# so we must encode it into JPEG in order to correctly display the
		# video stream.
		ret, jpeg = cv2.imencode('.jpg', frame)
		return jpeg.tobytes()

	'''def somethingHasMoved(self, frame):
		height, width, depth = frame.shape

		whitePixels = 0
		# Iterate over the entire image
		for y in range(height):
			for x in range(width):
				#print frame[0][0][0]#[y, x]
				#if frame[y,x] == 0.0:
				if np.any(frame[y, x] != 0):
					whitePixels += 1

		return True'''

if __name__ == "__main__":
	detect = MotionDetector(showWindows=False, doRecord=True, doTrack=False)
	detect.run()
