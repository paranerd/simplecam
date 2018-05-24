# https://github.com/log0/video_streaming_with_flask_example

import os
import time
from multiprocessing import Process
from flask import Flask, render_template, Response, send_file, stream_with_context
from camera_cv2 import VideoCamera
from microphone import Microphone
#from motion_detector_cv2 import MotionDetector

app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/sounds')
def sounds():
	files = os.listdir('static/sounds')
	return render_template('sounds.html', files = files)

@app.route("/sound/<string:sound_id>")
def get_sound(sound_id):
	return render_template('sound.html', sound_id = sound_id)

@app.route('/videostream')
def videostream():
	return render_template('videostream.html')

@app.route('/videofeed')
def videofeed():
	def genVideo(camera):
		while True:
			frame = camera.getFrame()
			yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

	return Response(
		genVideo(VideoCamera()),
		mimetype='multipart/x-mixed-replace; boundary=frame'
	)

@app.route('/audiostream')
def audiostream():
	return render_template('audiostream.html')

@app.route('/audiofeed')
def audiofeed():
	def gen(microphone):
		while True:
			sound = microphone.getSound()
			with open('tmp.wav', 'rb') as myfile:
				yield myfile.read()
				#test = myfile.read()

			#yield sound
			#yield (b'--frame\r\n'
			#	b'Content-Type: audio/x-wav;codec=pcm\r\n\r\n' + sound + b'\r\n\r\n')

	return Response(stream_with_context(gen(Microphone())))
	#return Response(gen(Microphone()))

@app.route('/textoutput')
def textoutput():
	def generator():
		for i in range(0, 10):
			yield str(i)

	return Response(generator(), mimetype="text/plain")

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)