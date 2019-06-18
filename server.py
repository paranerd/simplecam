import os
import time
import subprocess
from multiprocessing import Process
from flask import Flask, render_template, Response, send_file, stream_with_context, redirect, url_for
from flask_socketio import SocketIO, emit

from motion_detector import MotionDetector
from noise_detector import NoiseDetector

import threading

import logging
import logging.handlers

app = Flask(__name__)
socketio = SocketIO(app)
archive_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'archive')

# Setup detectors
nd = NoiseDetector()
nd.start()

md = MotionDetector(doDisplay=False)
md.start()

@app.route('/home')
@app.route('/')
def index():
	return render_template('index.html')

@app.route('/live')
def live():
	return render_template('live.html')

@app.route('/videostream')
def videostream():
	def gen_video():
		while True:
			frame = md.get_frame()

			if frame is not None:
				yield (b'--frame\r\n'
					b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

	return Response(
		gen_video(),
		mimetype='multipart/x-mixed-replace; boundary=frame'
	)

@app.route('/archive')
def archive():
	return render_template('archive.html')

@app.route('/archive/<string:filename>')
def archive_item(filename):
	name, extension = os.path.splitext(filename)
	type = get_type(filename)
	return render_template('record.html', filename=filename, type=type)

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

class Stream_Thread(threading.Thread):
	def __init__(self):
		self.delay = 1
		super(Stream_Thread, self).__init__()

	def run(self):
		while True:
			sound = nd.get_chunk()
			socketio.emit('sound', {'chunk': sound})
			time.sleep(0.05)

t = Stream_Thread()
t.start()

def get_type(filename):
	name, extension = os.path.splitext(filename)
	return 'video' if extension == '.mp4' else 'audio'

def get_records():
	records = []

	for filename in sorted(os.listdir(archive_path), reverse=True):
		if not filename.startswith('.'):
			type = get_type(filename)
			size = byte_to_mb(os.path.getsize(archive_path + "/" + filename))
			record = {"filename": filename, 'size': size, 'type': type}
			records.append(record)

	return records

def byte_to_mb(byte):
	mb = "{:.2f}".format(byte / 1024 / 1024)
	return str(mb) + " MB"

app.jinja_env.globals.update(get_records=get_records)

if __name__ == '__main__':
	socketio.run(app, log_output=False, host='localhost', port=5000, use_reloader=False)
