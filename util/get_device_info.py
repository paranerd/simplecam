import argparse
import pyaudio

parser = argparse.ArgumentParser()
parser.add_argument('--device', type=int,
                    help='Device ID')

if __name__ == '__main__':
  args = parser.parse_args()
  p = pyaudio.PyAudio()

  device_info = p.get_device_info_by_index(args.device)

  print(device_info)
