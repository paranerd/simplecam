import os
import yaml
import logging
import logging.config
import subprocess
from dotenv import load_dotenv
from pathlib import Path
import time
import datetime
from workers.noise import NoiseDetector
from workers.motion import MotionDetector
from workers.pir import PIRDetector
from util.detector import Detector
from util.recorder import Recorder

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')
TMP_PATH = os.path.join(PROJECT_ROOT, 'tmp')
ARCHIVE_PATH = os.path.join(PROJECT_ROOT, 'archive')
LOG_PATH = os.path.join(PROJECT_ROOT, 'log')
LOGGER_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config', 'logger.yaml')

load_dotenv(DOTENV_PATH)
threads = []


def init_logger():
    """Initialize the logger."""
    # Load logger config
    with open(LOGGER_CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

    logger = logging.getLogger('supervisor')

    return logger


def init_environment():
    """Create all necessary folders."""
    for d in [TMP_PATH, ARCHIVE_PATH, LOG_PATH]:
        Path(d).mkdir(exist_ok=True)


def merge(filename, source, destination):
    """
    Merge .wav and .avi using ffmpeg.
    For some reason we need to first convert AVI to MP4 and then merge that MP4 with the WAV to be able to play in the browser.

    @param string filename
    @param string source
    @param string destination
    """
    logger.info('Merging...')

    # Convert AVI -> MP4
    cmd = 'ffmpeg -i {1}/{0}.avi {1}/{0}.mp4 2> /dev/null'.format(filename, source)
    subprocess.call(cmd, shell=True)

    # Merge MP4 + WAV -> MP4
    cmd = "ffmpeg -hide_banner -loglevel error -i {1}/{0}.wav -i {1}/{0}.mp4 -c:v copy -c:a aac -strict experimental {2}/{0}.mp4 && rm {1}/{0}.*".format(
        filename, source, destination)
    subprocess.call(cmd, shell=True)

    logger.info('Merged.')


def watch():
    """
    Watch loop to check for detections and trigger recordings.
    """
    detected = False
    notified = False
    detected_by = ""
    recording_started = None
    max_recording_length = int(os.getenv('MAX_RECORDING_LENGTH'))

    try:
        logger.info('Ready')

        while True:
            # Check for detections
            for t in threads:
                if isinstance(t, Detector) and t.detected():
                    detected = True
                    detected_by = t.name
                    break

            if detected and not (recording_started and time.time() - recording_started > max_recording_length):
                if not notified:
                    recording_started = time.time()

                    # Determine recording destination
                    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    path = os.path.join(TMP_PATH, str(filename))

                    for t in threads:
                        if isinstance(t, Recorder):
                            t.start_recording(path)

                    logger.info('Detection by {}'.format(detected_by))
                    logger.info('Recording started...')

                    notified = True
            else:
                if notified:
                    logger.info('Recording stopped.')

                    for t in threads:
                        if isinstance(t, Recorder):
                            t.stop_recording()

                    # Merge audio/video
                    merge(filename, TMP_PATH, ARCHIVE_PATH)

                    # Reset for next run
                    notified = False
                    recording_started = None

                    logger.info('Waiting...')
    except KeyboardInterrupt:
        logger.info('Cancelled')


if __name__ == '__main__':
    # Set up environment
    init_environment()

    # Set up logger
    logger = init_logger()

    # Set up threads
    threads = [
        NoiseDetector(),
        MotionDetector(),
        PIRDetector(),
    ]

    # Start all threads
    for t in threads:
        t.start()

    # Start watch loop
    watch()
