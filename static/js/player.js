class Player {
	constructor(config, socket) {
		let self = this;
		this.config = config;
		this.socket = socket;
		this.audioCtx = null;
		this.silence = new Float32Array(this.config.bufferSize);
		this.playing = false;

		this.audioQueue = {
			buffer: new Float32Array(0),

			write: function(chunk) {
				let currentLength = this.buffer.length;
				let newBuffer = new Float32Array(currentLength + chunk.length);
				newBuffer.set(this.buffer, 0);
				newBuffer.set(chunk, currentLength);
				this.buffer = newBuffer;
			},

			read: function(nSamples) {
				let samplesToPlay = this.buffer.subarray(0, nSamples);
				this.buffer = this.buffer.subarray(nSamples, this.buffer.length);
				return samplesToPlay;
			},

			length: function() {
				return this.buffer.length;
			},

			clear: function() {
				this.buffer = new Float32Array(0)
			}
		}

		socket.on('sound', function(data) {
			if (self.scriptNode) {
				let array = new Float32Array(data.chunk);
				console.log(array);
				self.audioQueue.write(array);
			}
		});
	}

	play() {
		this.playing = true;
		this.audioCtx = new AudioContext();
		this.scriptNode = this.audioCtx.createScriptProcessor(this.config.bufferSize, 1, 1);
		this.scriptNode.onaudioprocess = (e) => {
			if (this.audioQueue.length()) {
				e.outputBuffer.getChannelData(0).set(this.audioQueue.read(this.config.bufferSize));
			}
			else {
				e.outputBuffer.getChannelData(0).set(this.silence);
			}
		}

		this.scriptNode.connect(this.audioCtx.destination);
	}

	stop() {
		this.audioQueue.clear();
		this.scriptNode.disconnect();
		this.scriptNode = null;
	}

	isPlaying() {
		return !! this.scriptNode;
	}
}
