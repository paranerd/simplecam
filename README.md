# simpleCam

Surveillance camera with Motion- and Noise-Detector

## Prerequisites
```
sudo apt install python3 python3-pip lame ffmpeg libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
```

```
pip3 install -r requirements.txt
```

## To-Do
- Merging video and audio
- Maybe add eventlet (pip install eventlet; gunicorn --worker-class eventlet -w 1 server:app)

## Sources
https://github.com/log0/video_streaming_with_flask_example
