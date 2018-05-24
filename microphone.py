import pyaudio
import wave
import struct
from collections import deque
import time

class Microphone():
	def __init__(self):
		self.FORMAT   = pyaudio.paInt16
		self.CHUNK    = 1024  # How many bytes to read each time from mic (stream.read())
		self.CHANNELS = 1
		self.RATE     = 16000 # Hz, so samples (bytes) per second
		self.audio    = pyaudio.PyAudio()
		self.frames   = deque(maxlen=150)

		self.stream = self.audio.open(
			format=self.FORMAT,
			channels=self.CHANNELS,
			rate=self.RATE,
			input=True,
			frames_per_buffer=self.CHUNK
		)

	def __del__(self):
		print "\n*** DEL ***\n"
		self.stream.close()
		self.audio.terminate()

	def run(self):
		try:
			while True:
				data = self.stream.read(self.CHUNK)
				self.frames.append(data)
		except KeyboardInterrupt:
			self.save(list(self.frames))
			self.stream.close()
			self.audio.terminate()
			print "* Done recording."

	def setupStream(self):
		# Open stream
		self.stream = self.audio.open(
			format = self.FORMAT,
			channels = self.CHANNELS,
			rate = self.RATE,
			input = True,
			frames_per_buffer = self.CHUNK
		)

	def getSound(self):
		# Current chunk of audio data
		data = self.stream.read(self.CHUNK)
		self.frames.append(data)
		wave = self.save(list(self.frames))
		return data

	def save(self, data):
		data = '' . join(data)

		wavefile = wave.open("tmp.wav", 'wb')
		wavefile.setnchannels(self.CHANNELS)
		wavefile.setsampwidth(self.audio.get_sample_size(self.FORMAT))
		wavefile.setframerate(self.RATE)
		wavefile.writeframes(data)
		wavefile.close()
		#return wavefile

		with open("tmp.wav", mode='rb') as file: # b is important -> binary
			fileContent = file.read()
			return fileContent

if __name__ == "__main__":
	mic = Microphone()
	mic.run()