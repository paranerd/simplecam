import os
import sys
import time
import datetime
import math
import getopt
import numpy as np
import cv2
import threading
import subprocess
from collections import deque
from pathlib import Path
from dotenv import load_dotenv
import logging
from util.recorder import Recorder
from util.detector import Detector

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config')

# Load config
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(DOTENV_PATH)

class MotionDetector(threading.Thread, Recorder, Detector):
    def __init__(self):
        threading.Thread.__init__(self)

        name = self.__class__.__name__
        self.logger = logging.getLogger(name)

        self.is_detector = True
        self.is_recorder = True

        self.writer = None

        # Time in seconds to be observed for motion
        self.OBSERVER_LENGTH = int(os.getenv('OBSERVER_LENGTH'))
        self.threshold = 3  # float(os.getenv('MOTION_THRESHOLD'))

        self.do_add_contours = int(os.getenv('ADD_CONTOURS'))
        self.enable_motion_detection = int(
            os.getenv('VISUAL_MOTION_DETECTION'))
        self.detect_faces = int(os.getenv('FACE_DETECTION'))
        self.show_image = int(os.getenv('SHOW_IMAGE'))

        self.source = self.init_camera()
        self.codec = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # (*'X264')
        self.height, self.width = self.get_dimensions(self.source)

        self.face_cascade = cv2.CascadeClassifier(os.path.join(
            CONFIG_PATH, 'haarcascade_frontalface_default.xml'))

        self.fps = self.find_fps(self.source)

        self.detected = False

        self.recording_start = None
        self.recording = []

    def __del__(self):
        # Release camera
        self.source.release()

        # Close all windows
        cv2.destroyAllWindows()

    def get_dimensions(self, source):
        """
        Determine height and width of the video source.

        @return tuple(int, int)
        """
        frame = cv2.cvtColor(source.read()[1], cv2.COLOR_RGB2GRAY)
        return frame.shape[0: 2]

    def find_fps(self, source):
        """
        Determine frames per second of the video source.

        @param video source
        @return int
        """
        self.logger.info("Determining FPS...")

        # How many frames to capture
        num_frames = 120

        # Start time
        start = time.time()

        # Grab a few frames
        for i in range(0, num_frames):
            ret, frame = source.read()

        # End time
        end = time.time()

        # Calculate frames per second
        fps = int(math.floor(num_frames / (end - start)))
        self.logger.info("Setting FPS to {}".format(fps))

        return fps

    def init_camera(self):
        """
        Start the camera.

        @return cv2.VideoCapture
        """
        # Init camera
        camera = cv2.VideoCapture(int(os.getenv('CAMERA')))
        camera.set(3, 320)
        camera.set(4, 240)

        # Wait half a second for light adjustment
        time.sleep(0.5)

        return camera

    def start_recording(self, path):
        """
        Setup the recorder.

        @param string path
        """
        self.path = path

        self.recording_start = time.time()

    def stop_recording(self):
        """Reset values to default."""
        duration = time.time() - self.recording_start
        fps = math.floor(len(self.recording) / duration)
        self.logger.info('Actual FPS: {}'.format(fps))

        self.writer = None
        self.recording_start = None

        self.save(fps)

    def save(self, fps):
        """
        Save stored frames to file.

        @param int fps
        """
        self.writer = cv2.VideoWriter('{}.avi'.format(
            self.path), self.codec, fps, (self.width, self.height))

        for frame in self.recording:
            self.writer.write(frame)

        self.writer = None

    def run(self):
        """
        Main worker.
        """
        observer = deque(maxlen=self.fps * self.OBSERVER_LENGTH)
        previous_frame = None

        while True:
            # Grab a frame
            (grabbed, current_frame) = self.source.read()

            # End of feed
            if not grabbed:
                self.logger.info('End of camera feed.')
                break

            if self.enable_motion_detection:
                # Gray frame
                frame_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

                # Blur frame
                frame_blur = cv2.GaussianBlur(frame_gray, (21, 21), 0)

                # If there's no previous frame, us the current one
                if previous_frame is None:
                    previous_frame = frame_blur
                    continue

                # Delta frame
                delta_frame = cv2.absdiff(previous_frame, frame_blur)

                # Threshold frame
                threshold_frame = cv2.threshold(
                    delta_frame, 15, 255, cv2.THRESH_BINARY)[1]

                # Dilate the thresholded image to fill in holes
                kernel = np.ones((5, 5), np.uint8)
                dilated_frame = cv2.dilate(
                    threshold_frame, kernel, iterations=4)

                # Find difference in percent
                res = dilated_frame.astype(np.uint8)
                movement = (np.count_nonzero(res) * 100) / res.size

                # Add movement percentage to observer
                observer.append(movement)

                if self.do_add_contours:
                    current_frame, targets = self.add_contours(
                        current_frame, dilated_frame)

                # Set blurred frame as new previous frame
                previous_frame = frame_blur

                if self.do_add_contours:
                    current_frame, _ = self.add_contours(
                        current_frame, dilated_frame)

            if self.detect_faces:
                _, current_frame = self.find_face(current_frame)

            self.detected = sum([x > self.threshold for x in observer]) > 0

            # Exit on 'q'
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

            # Store frame if recording
            if self.recording_start:
                self.recording.append(current_frame)

            # Display
            if self.show_image:
                cv2.imshow("Current frame:", current_frame)

    def find_face(self, frame):
        """
        Find face in frame.

        @param array frame
        @return tuple(int, array)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        return len(faces), frame

    def add_contours(self, raw_frame, dilated_frame):
        """
        Add contours to frame.

        @param array raw_frame
        @param array dilated_frame
        @return tuple(array, list)
        """
        # Find contours on thresholded image
        contours, nada = cv2.findContours(
            dilated_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Make coutour frame
        contour_frame = raw_frame.copy()

        # Target contours
        targets = []

        # Loop over the contour
        for c in contours:
            # If the contour is too small, ignore it
            if cv2.contourArea(c) < 500:
                # Make sure this has a less than sign, not an html escape
                continue

            # Contour data
            M = cv2.moments(c)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            x, y, w, h = cv2.boundingRect(c)
            rx = x + int(w / 2)
            ry = y + int(h / 2)
            ca = cv2.contourArea(c)

            # Plot contours
            cv2.drawContours(contour_frame, [c], 0, (0, 0, 255), 2)
            cv2.rectangle(contour_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.circle(contour_frame, (cx, cy), 2, (0, 0, 255), 2)
            cv2.circle(contour_frame, (rx, ry), 2, (0, 255, 0), 2)

            # Save target contours
            targets.append((rx, ry, ca))

        return contour_frame, targets


if __name__ == "__main__":
    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S-md")
    md = MotionDetector()
    md.start()

    time.sleep(2)

    print('Starting...')

    md.start_recording(filename)
    time.sleep(10)
    md.stop_recording()

    print('End.')
