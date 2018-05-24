import cv2.cv as cv

class VideoCamera(object):
	def __init__(self):
		self.capture = cv.CaptureFromCAM(0)

	def __del__(self):
		self.capture.release()

	def getFrame(self):
		curframe = cv.QueryFrame(self.capture)
		img = cv.EncodeImage('.jpg', curframe)
		return img.tostring()