import os
import RPi.GPIO as GPIO
import time
import threading
from pathlib import Path
from dotenv import load_dotenv
from util.detector import Detector

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load config
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(DOTENV_PATH)

SENSOR_PIN = int(os.getenv('PIR_SENSOR_PIN'))

GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_PIN, GPIO.IN)

class PIRDetector(threading.Thread, Detector):
    def __init__(self):
        threading.Thread.__init__(self)

        self.name = self.__class__.__name__

        self._detected = False

    def detected(self):
        """
        Returns whether movement was detected.

        @return bool
        """
        return self._detected

    def callback(self, channel):
        """
        Gets called on every change of the PIR sensor.

        @param int channel
        """
        if GPIO.input(SENSOR_PIN):
            self._detected = True
        else:
            time.sleep(3)  # You might also do this on the sensor directly
            self._detected = False

    def run(self):
        """Main entry point."""
        try:
            GPIO.add_event_detect(SENSOR_PIN, GPIO.BOTH,
                                  callback=self.callback)

            while True:
                time.sleep(100)
        except KeyboardInterrupt:
            pass

        GPIO.cleanup()
