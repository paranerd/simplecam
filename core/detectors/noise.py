import pyaudio
import wave
import audioop
import subprocess
import os
import time
import datetime
import math
import struct
import threading
import io
import numpy as np
from collections import deque
from pathlib import Path
import logging
import wave
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load config
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(DOTENV_PATH)


class NoiseDetector(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        name = self.__class__.__name__
        self.logger = logging.getLogger(name)
        self.is_detector = True
        self.is_recorder = True

        self.FORMAT = pyaudio.paInt16
        # Hz, so samples (bytes) per second, e.g. 44100 or 48000
        self.RATE = int(os.getenv('AUDIO_SAMPLE_RATE'))
        # How many bytes to read from mic each time (stream.read()), e.g. 512 or 2048
        self.CHUNK_SIZE = int(os.getenv('AUDIO_CHUNK_SIZE'))
        # How many chunks make a second? (example: 16.000 bytes/s, each chunk is 1.024 bytes, so 1s is 15 chunks)
        self.CHUNKS_PER_SEC = math.floor(self.RATE / self.CHUNK_SIZE)
        self.CHANNELS = int(os.getenv('AUDIO_CHANNELS'))
        # Time in seconds to be observed after noise
        self.OBSERVER_LENGTH = 5
        # Seconds of audio cache for prepending to records to prevent chopped phrases (history length + observer length = min record length)
        self.HISTORY_LENGTH = 0

        self.chunk = None

        self.audio = pyaudio.PyAudio()
        self.stream = self.get_stream()

        self.threshold = self.determine_threshold()

        # Prepend audio from before noise was detected
        # Keep the last {HISTORY_LENGTH} seconds in history
        self.history = deque(maxlen=self.HISTORY_LENGTH * self.CHUNKS_PER_SEC)
        self.detected = False
        self.record = []
        self.recording = False

    def __del__(self):
        # Stop recording
        if self.stream:
            self.stream.close()

        if self.audio:
            self.audio.terminate()

    def get_stream(self):
        """
        Open audio stream.

        @return PyAudio
        """
        return self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=int(os.getenv('AUDIO_DEVICE_ID')),
            frames_per_buffer=self.CHUNK_SIZE
        )

    def determine_threshold(self):
        """
        Determine threshold noise intensity using RMS.
        Anything below the threshold is considered silence

        @return float
        """
        self.logger.info("Determining noise threshold...")
        start = time.time()

        res = []
        for x in range(50):
            block = self.stream.read(
                self.CHUNK_SIZE, exception_on_overflow=False)
            rms = self.get_rms(block)
            res.append(rms)

        # Set threshold to 50% above average
        threshold = (sum(res) / len(res)) * 1.5
        self.logger.info("Setting threshold to: {}".format(threshold))

        return threshold

    def get_rms(self, block):
        """
        Calculate Root Mean Square (noise level) for audio chunk.

        @param bytes block
        @return float
        """
        d = np.frombuffer(block, np.int16).astype(float)
        return np.sqrt((d * d).sum() / len(d))

    def start_recording(self, path):
        """
        Setup the recorder.

        @param string filename
        """
        self.save_path = '{}.wav'.format(path)
        self.recording = True

    def stop_recording(self):
        """
        Reset variables to default
        """
        self.save()

        self.save_path = None
        self.detected_at = None
        self.notified = False
        self.recording = False
        self.record = []

    def save(self):
        """Create wave file from recorded chunks."""
        wf = wave.open(self.save_path, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.record))
        wf.close()

    def run(self):
        """
        Detect noise from microphone and record.
        Noise is defined as sound surrounded by silence (according to threshold)
        """

        # Stores audio intensity of previous sound-chunks
        # If one of these chunks is above threshold, recording gets triggered
        # Keep the last {OBSERVER_LENGTH} seconds in observer
        observer = deque(maxlen=self.OBSERVER_LENGTH * self.CHUNKS_PER_SEC)

        self.logger.info("Listening...")

        try:
            while True:
                # Current chunk of audio data
                self.chunk = self.stream.read(
                    self.CHUNK_SIZE, exception_on_overflow=False)
                self.history.append(self.chunk)

                # Add noise level of this chunk to the sliding-window
                rms = self.get_rms(self.chunk)
                observer.append(rms)

                if self.recording:
                    self.record.append(self.chunk)

                self.detected = sum([x > self.threshold for x in observer]) > 0
        except KeyboardInterrupt:
            self.logger.info("Interrupted.")


if __name__ == "__main__":
    nd = NoiseDetector()
    nd.start()
    time.sleep(2)

    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S-nd")
    nd.start_recording(filename)
    print('started nd')
    time.sleep(10)
    nd.stop_recording()
    print('stopped nd')
