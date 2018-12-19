# pip3 install flask
# https://github.com/log0/video_streaming_with_flask_example

import os
import time
from multiprocessing import Process
from flask import Flask, render_template, Response, send_file, stream_with_context, redirect, url_for
from motion_detector import MotionDetector
from noise_detector import NoiseDetector

app = Flask(__name__)
archive_path = 'archive'

# Setup detectors
nd = NoiseDetector(useRMS=True)
nd.start()

#md = MotionDetector(doDisplay=False)
#md.start()

#md.sync(nd)
#nd.sync(md)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/live')
def live():
	return render_template('live.html')

@app.route('/audiostream')
def audiostream():
	def gen():
		sound = nd.getSound3()
		while sound:
			yield sound
			sound = nd.getSound3()

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

	#return Response(stream_with_context(gen3()))
	#return Response(gen2(), mimetype="audio/x-wav;codec=pcm")
	return send_file('tmp.wav', cache_timeout=-1)

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
	app.run(host='0.0.0.0', debug=True, use_reloader=False)
