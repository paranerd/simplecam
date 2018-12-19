class Recorder:
	def __init__(self, fps=7):
		self.writer = None
		self.codec = cv2.VideoWriter_fourcc('M','J', 'P', 'G')
		self.currentFile = None
		self.framesWritten = 0

	def convertToMp4(self):
		# Build destination path
		filename, extension = os.path.splitext(self.currentFile)
		destination = filename + ".mp4"

		try:
			print("* Converting...")
			cmd = 'ffmpeg -i ' + self.currentFile + ' ' + destination + ' 2> /dev/null'
			p = subprocess.Popen(cmd, shell=True)
			(output, err) = p.communicate()
			print("* Done.")

			if removeself.currentFile and os.path.isfile(destination):
				os.remove(self.currentFile)
		except subprocess.CalledProcessError:
			print("Error converting")

	def start(self):
		'''
		Create the recorder
		'''
		if self.isRecording():
			print("Recorder already in use")
			return

		# Set destination
		self.currentFile = "archive/" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".avi"

		# Create writer
		self.writer = cv2.VideoWriter(self.currentFile, self.codec, self.fps, (self.width, self.height))
		#self.writer = cv2.VideoWriter("archive/" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4", self.codec, self.fps, (320,240))

	def record(self, frame):
		self.writer.write(frame)
		self.framesWritten += 1

	def stop(self):
		self.writer = None
		self.framesWritten = 0

	def isRecording(self):
		return self.writer is not None

	def length(self):
		return self.framesWritten
