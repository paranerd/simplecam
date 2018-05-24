import cv2
import cv2.cv as cv
from datetime import datetime
import time

class MotionDetector():
	def __init__(self,triggerPercent=8, doRecord=True, doTrack=False, showWindows=False):
		self.curframe = None
		# Video write destination
		self.writer         = None
		# Set codec (alt: DIVX, H264, DIB_)
		self.codec          = cv.CV_FOURCC('M', 'J', 'P', 'G')
		# Either or not record the moving object
		self.doRecord       = doRecord
		# Whether or not we are recording
		self.isRecording    = False
		# Whether or not to track motion
		self.doTrack        = doTrack
		# Coordinates of motion area
		self.motionArea     = None
		# Either or not show the 2 windows
		self.show           = showWindows
		# Video input
		self.capture        = cv.CaptureFromCAM(0)
		# Take a frame to init recorder
		self.frame          = cv.QueryFrame(self.capture)
		# Total pixels
		self.totalPixels    = self.frame.width * self.frame.height
		# To distinguish between movement and still
		self.triggerPercent = triggerPercent
		# Hold timestamp of the last detection
		self.triggerTime    = 0
		# Gray frame at t-1
		self.frame1gray     = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U)
		# Gray frame at t
		self.frame2gray     = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U)
		# Will hold the thresholded result
		self.res            = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U)
		# Create a font
		self.font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, 1, 1, 0, 2, 8)

		cv.CvtColor(self.frame, self.frame1gray, cv.CV_RGB2GRAY)

		if showWindows:
			cv.NamedWindow("Image")
			cv.CreateTrackbar("Mytrack", "Image", self.triggerPercent, 100, self.onChange)

	'''def getFrame(self):
		success, image = self.video.read()
		# We are using Motion JPEG, but OpenCV defaults to capture raw images,
		# so we must encode it into JPEG in order to correctly display the
		# video stream.
		ret, jpeg = cv2.imencode('.jpg', image)
		return jpeg.tobytes()'''

	def getFrame(self):
		jpeg = cv2.imencode('.jpg', self.curframe)
		return jpeg.tobytes()

	def __del__(self):
		self.video.release()

	def onChange(self, val):
		'''
		Callback when the user changes the triggerPercentage
		'''
		self.triggerPercent = val

	def initRecorder(self):
		'''
		Create the recorder
		'''
		# Set path and FPS (15)
		self.writer = cv.CreateVideoWriter(datetime.now().strftime("%b-%d_%H:%M:%S")+".avi", self.codec, 15, cv.GetSize(self.frame), 1)

	def run(self):
		print "Started"
		started = time.time()
		while True:
			curframe = cv.QueryFrame(self.capture)
			self.curframe = curframe
			# Get timestamp of this frame
			instant = time.time()

			# Process the image
			self.processImage(curframe)

			if not self.isRecording:
				if self.somethingHasMoved(curframe):
					# Update the triggerTime
					self.triggerTime = instant

					if self.doTrack and self.motionArea != None:
						cv.Rectangle(curframe, self.motionArea[0], self.motionArea[1], (0,255,0), 3)

					# Wait 5 second for luminosity adjusting etc.
					if instant > started +5:
						print "* Something is moving (" + self.getTimestamp() + ")"
						# Set isRecording = True only if we record a video
						if self.doRecord:
							self.initRecorder()
							self.isRecording = True
			else:
				# Record during 10 seconds
				if instant >= self.triggerTime +10:
					print "* Stop recording"
					self.isRecording = False
				else:
					# Put date on the frame
					cv.PutText(curframe,datetime.now().strftime("%b %d, %H:%M:%S"), (25,30), self.font, 0)
					# Write the frame
					cv.WriteFrame(self.writer, curframe)

			if self.show:
				cv.Flip(curframe, curframe, 1)
				cv.ShowImage("Image", curframe)
				#cv.ShowImage("Res", self.res)

				cv.Copy(self.frame2gray, self.frame1gray)
			c = cv.WaitKey(1)
			# Exit if user enters 'Esc'
			if c == 27 or c == 1048603:
				break

	def processImage(self, frame):
		cv.CvtColor(frame, self.frame2gray, cv.CV_RGB2GRAY)

		# Get the difference between the frames
		cv.AbsDiff(self.frame1gray, self.frame2gray, self.res)

		# Remove the noise and do the threshold
		cv.Smooth(self.res, self.res, cv.CV_BLUR, 5,5)
		element = cv.CreateStructuringElementEx(5*2+1, 5*2+1, 5, 5,  cv.CV_SHAPE_RECT)
		cv.MorphologyEx(self.res, self.res, None, None, cv.CV_MOP_OPEN)
		cv.MorphologyEx(self.res, self.res, None, None, cv.CV_MOP_CLOSE)
		cv.Threshold(self.res, self.res, 10, 255, cv.CV_THRESH_BINARY_INV)

	def somethingHasMoved(self, curframe):
		'''
		Get black-pixel-ratio
		If greater than triggerPercent, something has moved
		'''

		blackPixels = 0
		motion = [[None, None], [None, None]]

		# Iterate over the entire image
		for y in range(self.frame.height):
			for x in range(self.frame.width):
				if self.res[y,x] == 0.0:
					if motion[0][0] == None or x < motion[0][0]:
						motion[0][0] = x
					elif motion[0][1] == None or x > motion[0][0]:
						motion[0][1] = x
					if motion[1][0] == None or y < motion[1][0]:
						motion[1][0] = y
					elif motion[1][1] == None or y > motion[1][1]:
						motion[1][1] = y

					# Pixel is black, that means it has been changed
					blackPixels += 1

		# Calculate the percentage of black pixels in the image
		percent = (blackPixels * 100.0) / self.totalPixels

		self.motionArea = ((motion[0][0], motion[1][0]), (motion[0][1], motion[1][1]))

		return percent > self.triggerPercent

	def getTimestamp(self):
		return datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":
	detect = MotionDetector(triggerPercent=4,doRecord=False,doTrack=True,showWindows=False)
	detect.run()