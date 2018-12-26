# https://raw.githubusercontent.com/jeysonmc/python-google-speech-scripts/master/stt_google.py
# sudo apt install lame python3-pip
# pip3 install pyaudio

import pyaudio
import wave
import audioop
import subprocess
import os
import time
import math
import struct
import threading
import io

from collections import deque
from datetime import datetime

from lock_manager import LockManager

from util import Util

class NoiseDetector(threading.Thread):
	def __init__(self, threshold=None, useRMS=True):
		threading.Thread.__init__(self)

		self.name				= self.__class__.__name__

		self.FORMAT             = pyaudio.paInt16
		self.RATE               = 16000 # Hz, so samples (bytes) per second
		self.CHUNK_SIZE			= 1024  # How many bytes to read from mic each time (stream.read())
		self.CHUNKS_PER_SEC		= math.floor(self.RATE / self.CHUNK_SIZE) # How many chunks make a second? (16.000 bytes/s, each chunk is 1.024 bytes, so 1s is 15 chunks)
		self.CHANNELS           = 1
		self.HISTORY_LENGTH		= 2     # Seconds of audio cache for prepending to records to prevent chopped phrases (history length + observer length = min record length)
		self.OBSERVER_LENGTH	= 3	    # Time in seconds to be observed for noise
		self.NOTIFICATION_LIMIT = 1     # Seconds before a notification is sent

		self.useRMS				= useRMS
		self.archive			= "archive"
		self.currentFile		= None
		self.chunk				= None
		self.chunks				= []
		self.record				= [] # Stores audio to be saved
		self.notified			= False # If we already notified the client(s)

		self.audio              = pyaudio.PyAudio()
		self.stream				= self.getStream()

		self.threshold			= self.determineThreshold(useRMS, threshold)

		self.lockManager		= LockManager("noise")
		self.detectedAt			= None

	def __del__(self):
		self.stream.close()
		self.audio.terminate()

	def determineThreshold(self, useRMS=False, default=None):
		"""
		Determine threshold noise intensity
		Anything below the threshold is considered silence
		"""

		if default is None:
			return self.determineThresholdRMS() if (useRMS == True) else self.determineThresholdAVG()

		return default


	def getStream(self):
		return self.audio.open(
			format=self.FORMAT,
			channels=self.CHANNELS,
			rate=self.RATE,
			input=True,
			frames_per_buffer=self.CHUNK_SIZE
		)

	def determineThresholdAVG(self, num_samples=50):
		"""
		Get the average of the 20% largest recorded noise intensities
		Add 200 for threshold
		"""

		Util.log(self.name, "Determining threshold using AVG")

		# Get average audio intensities
		values = [math.sqrt(abs(audioop.avg(self.stream.read(self.CHUNK_SIZE), 4)))
					for x in range(num_samples)]
		values = sorted(values, reverse=True)
		avg = sum(values[:int(num_samples * 0.2)]) / int(num_samples * 0.2)

		threshold = avg + 200
		Util.log(self.name, "Setting threshold to: " + str(threshold))
		return threshold

	def determineThresholdRMS(self, num_samples=50):
		"""
		Get the average noise level and adds 0.008 for threshold
		"""

		Util.log(self.name, "Determining threshold using RMS")

		res = []
		for x in range(num_samples):
			block = self.stream.read(self.CHUNK_SIZE)
			res.append(self.getRMS(block))

		threshold = (sum(res) / len(res)) + 0.008
		Util.log(self.name, "Setting threshold to: " + str(threshold))
		return threshold

	def getRMS(self, block):
		# RMS amplitude is defined as the square root of the
		# mean over time of the square of the amplitude.
		# so we need to convert this string of bytes into
		# a string of 16-bit samples...

		# We will get one short out for each two chars in the string
		count = len(block) / 2
		format = "%dh" % (count)
		shorts = struct.unpack(format, block)

		# Iterate over the block
		sum_squares = 0.0
		for sample in shorts:
			# Sample is a signed short in +/- 32768.
			# Normalize it to 1.0
			n = sample * (1.0/32768.0)
			sum_squares += n*n

		return math.sqrt(sum_squares / count)

	def startRecording(self):
		'''
		Setup the recorder
		'''

		self.currentFile = self.archive + "/" + self.detectedAt

		Util.log(self.name, "Noise detected! Recording...")

	def stopRecording(self):
		# Reset all
		self.currentFile = None
		self.detectedAt = None
		self.notified = False
		self.record = []

	def run(self):
		"""
		Detect noise from microphone and record
		Noise is defined as sound surrounded by silence (according to threshold)
		"""

		# Stores audio intensity of previous sound-chunks
		# If one of these chunks is above threshold, recording gets triggered
		# Keep the last {OBSERVER_LENGTH} seconds in observer
		observer = deque(maxlen=self.OBSERVER_LENGTH * self.CHUNKS_PER_SEC)

		# Prepend audio from before noise was detected
		# Keep the last {HISTORY_LENGTH} seconds in history
		history = deque(maxlen=self.HISTORY_LENGTH * self.CHUNKS_PER_SEC)

		Util.log(self.name, "Listening...")

		try:
			while True:
				# Current chunk of audio data
				self.chunk = self.stream.read(self.CHUNK_SIZE)
				history.append(self.chunk)

				# Add the average audio intensity of this chunk to the sliding-window
				if self.useRMS:
					observer.append(self.getRMS(self.chunk))
				else:
					observer.append(math.sqrt(abs(audioop.avg(self.chunk, 4))))

				if self.detected(sum([x > self.threshold for x in observer]) > 0):
					# There's at least one chunk in the sliding-window above threshold
					if not self.recording():
						self.startRecording()

					self.record.append(self.chunk)

					if not self.notified and len(self.record) > self.NOTIFICATION_LIMIT * self.CHUNKS_PER_SEC:
						self.notify()
				elif self.recording():
					# Silence limit was reached, finish recording and save
					self.save(list(history) + self.record)
					self.stopRecording()

					Util.log(self.name, "Listening...")
		except KeyboardInterrupt:
			Util.log(self.name, "Interrupted.")

	def genHeader(self, sampleRate, bitsPerSample, channels, samples):
		#datasize = 2000*10**6
		#datasize = 1 * channels * bitsPerSample // 8
		datasize = len(samples) * channels * bitsPerSample // 8
		o = bytes("RIFF","ascii")                                               # (4byte) Marks file as RIFF
		o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
		o += bytes("WAVE",'ascii')                                              # (4byte) File type
		o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
		o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
		o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
		o += (channels).to_bytes(2,'little')                                    # (2byte)
		o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
		o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
		o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
		o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
		o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
		o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
		return o

	def getSound2(self):
		data = [self.chunk]
		data = b''.join(data)

		# Generate the WAV file contents
		with io.BytesIO() as wav_file:
			wav_writer = wave.open(wav_file, "wb")
			try:
				wav_writer.setframerate(self.RATE)
				wav_writer.setsampwidth(self.audio.get_sample_size(self.FORMAT))
				wav_writer.setnchannels(self.CHANNELS)
				wav_writer.writeframes(data)
				wav_data = wav_file.getvalue()
			finally:
				wav_writer.close()
		return wav_data

	def getSound(self):
		# Current chunk of audio data
		data = self.chunk

		self.chunks.append(data)
		self.save([self.chunk])

		wav_header = self.genHeader(self.RATE, self.audio.get_sample_size(self.FORMAT), self.CHANNELS, list(self.chunks))

		return wav_header + data

	def getSound3(self, data):
		Util.log(self.name, "Saving live chunks")
		# Concat data array to string
		data = b''.join(data)

		# Write frames to file
		wf = wave.open('tmp.wav', 'wb')
		wf.setnchannels(self.CHANNELS)
		wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
		wf.setframerate(self.RATE)
		wf.writeframes(data)
		wf.close()

	def save(self, data):
		"""
		Save mic data to a WAV file.
		Return path of saved file
		"""

		Util.log(self.name, "Saving audio...")

		# Concat data array to string
		data = b''.join(data)

		# Write frames to file
		wf = wave.open(self.currentFile + ".wav", 'wb')
		wf.setnchannels(self.CHANNELS)
		wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
		wf.setframerate(self.RATE)
		wf.writeframes(data)
		wf.close()

		# Convert
		self.convertToMp3()

	def convertToMp3(self, source=None):
		try:
			Util.log(self.name, "Converting audio...")
			cmd = 'for i in ' + self.archive + '/*.wav; do lame --preset insane "$i" 2> /dev/null && rm "$i"; done'
			p = subprocess.Popen(cmd, shell=True)
			(output, err) = p.communicate()

		except subprocess.CalledProcessError:
			Util.log(self.name, "Error converting audio")

	def detected(self, noise):
		otherDetected = self.lockManager.readOther()

		# Set time of detection
		if otherDetected:
			self.detectedAt = otherDetected
		elif noise:
			self.detectedAt = datetime.now().strftime("%Y%m%d_%H%M%S")
		else:
			self.detectedAt = None

		# Manage noise-lock
		if noise:
			self.lockManager.set(self.detectedAt)
		else:
			self.lockManager.remove()

		return otherDetected or noise

	def recording(self):
		return len(self.record) > 0

	def notify(self):
		Util.log(self.name, "Notifying")
		self.notified = True

if __name__ == "__main__":
	nd = NoiseDetector()
	nd.start()
