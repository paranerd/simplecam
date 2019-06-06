# https://github.com/log0/video_streaming_with_flask_example

import os
import time
import subprocess
from multiprocessing import Process
from flask import Flask, render_template, Response, send_file, stream_with_context, redirect, url_for
from flask_socketio import SocketIO, emit
from motion_detector import MotionDetector
from noise_detector import NoiseDetector

import threading

app = Flask(__name__)
socketio = SocketIO(app)
archive_path = 'archive'

# Setup detectors
nd = NoiseDetector(useRMS=True)
nd.start()

md = MotionDetector(doDisplay=False)
md.start()

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/live')
def live():
	return render_template('live.html')

@app.route('/audiostream')
def audiostream():
	def gen2():
		while True:
			with open("tmp.wav", "rb") as fwav:
				print("** tmp.wav re-open")
				data = fwav.read(1024)
				while data:
					print("** still data in tmp.wav")
					yield data
					data = fwav.read(1024)

	def gen3():
		while True:
			sound = nd.getSound()
			#yield sound
			yield (b'--frame\r\n'
				b'Content-Type: audio/x-wav;codec=pcm\r\n\r\n' + sound + b'\r\n\r\n')

	def gen4():
		sound = nd.getSound4()
		while sound:
			sound = nd.getSound4()
			data = subprocess.check_output(['cat', '/home/ijon/Dokumente/simplecam/tmp.wav'])
			yield data

	#return Response(stream_with_context(gen3()))
	#return Response(gen2(), mimetype="audio/x-wav;codec=pcm")
	#return send_file('tmp.wav', cache_timeout=-1)
	return Response(gen4(), mimetype='audio/x-wav;codec=pcm')

@app.route('/videostream')
def videostream():
	def genVideo():
		while True:
			frame = md.getFrame()

			if frame is not None:
				yield (b'--frame\r\n'
					b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

			time.sleep(0.1)

	return Response(
		genVideo(),
		mimetype='multipart/x-mixed-replace; boundary=frame'
	)

@app.route('/archive')
def archive():
	return render_template('archive.html')

@app.route('/archive/<string:filename>')
def archive_item(filename):
	name, extension = os.path.splitext(filename)
	type = getType(filename)
	return render_template('record.html', filename = filename, type = type)

@app.route('/archive/delete/<string:filename>')
def archive_delete(filename):
	os.remove(archive_path + "/" + filename)
	return redirect(url_for('archive'))

@app.route('/archive/play/<string:filename>')
def archive_play(filename):
	return send_file('archive/' + filename)

@socketio.on('connect')
def connect():
	print('Client connected')

@socketio.on('disconnect')
def disconnect():
	print('Client disconnected')

class Random_Thread(threading.Thread):
	def __init__(self):
		self.delay = 1
		super(Random_Thread, self).__init__()

	def generate_number(self):
		while True:
			sound = nd.getChunk()
			socketio.emit('sound', {'chunk': sound})
			time.sleep(0.01)

	def run(self):
		self.generate_number()

t = Random_Thread()
t.start()

def getType(filename):
	name, extension = os.path.splitext(filename)
	return 'video' if extension == '.mp4' else 'audio'

def getRecords():
	records = []

	for filename in sorted(os.listdir(archive_path), reverse=True):
		type = getType(filename)
		size = convertByteToMB(os.path.getsize(archive_path + "/" + filename))
		record = {"filename": filename, 'size': size, 'type': type}
		records.append(record)

	return records

def convertByteToMB(byte):
	mb = "{:.2f}".format(byte / 1024 / 1024)
	return str(mb) + " MB"

app.jinja_env.globals.update(getRecords=getRecords)

if __name__ == '__main__':
	socketio.run(app, host='localhost', port=5000, debug=True, use_reloader=False)
