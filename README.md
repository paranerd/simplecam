# simpleCam

Surveillance camera with Motion- and Noise-Detector

## Hardware requirements
I tested the code with the following setup:
- Raspberry Pi 4 Model B (4GB)
- Electreeks Raspberry Pi Camera with IR cut-off filter
- USB microphone
- HC-SR-501 PIR Sensor

## Prerequisites
### Install dependencies
```
sudo apt install python3 python3-pip python3-pyaudio lame ffmpeg libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
```

```
sudo apt-get install libcblas-dev libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev libqtgui4 libqt4-test
```

```
pip3 install -r requirements.txt
```

### Create virtual audio devices
```
sudo modprobe snd-aloop
```

```
sudo echo 'snd-aloop' >> /etc/modules
```

### Create virtual video device
```
sudo modprobe v4l2loopback devices=1
```

This will create /dev/video1

### Gather additional information
To determine the ID of your physical and loopback audio devices, run:
```
arecord -l
```

You may replace `hw:2,0` (physical input) and `hw:3,1` (virtual loopback output) in the `ffmpeg` command below with your respective IDs in the format `hw:device,subdevice`.

To get the audio ID used by PyAudio, run:
```
python3 /path/to/util/get_device_index.py
```

To get info on your microphone's default sample rate, run:
```
python3 /path/to/util/get_device_info.py --device [device_id]
```

### Edit config
Edit `simplecam/.env` to your particular setup.

## Prepare environment
### Set project path
```
SIMPLECAM_PATH=/path/to/simplecam
```

### Launch node server
```
npm start --prefix ${SIMPLECAM_PATH}/server &
```

### Start streaming
```
ffmpeg -hide_banner -re -f alsa -ar 44100 -ac 1 -i hw:2,0 -f v4l2 -i /dev/video0 -c:a aac -b:a 128k -y -s 480x320 -b:v 2014k -preset ultrafast -tune zerolatency -crf 23 -f v4l2 /dev/video1 -f alsa hw:3,1 -force_key_frames "expr:gte(t,n_forced*2)" -hls_time 1 -hls_list_size 10 -hls_flags delete_segments -start_number 1 ${SIMPLECAM_PATH}/server/stream/index.m3u8 &
```

This will create the HLS stream as well as create a copy of the video and audio streams to be used by motion and noise detection.

## Access in the browser
Go to `http://your-host:8081`
