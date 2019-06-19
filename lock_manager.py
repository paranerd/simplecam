import os
import datetime

class Lock_Manager:
	def __init__(self, name):
		self.locks = os.path.dirname(os.path.realpath(__file__)) + "/locks"
		self.name = name + ".lock"
		self.path = os.path.join(self.locks, self.name)

		if not os.path.exists(self.locks):
			os.makedirs(self.locks)

	def set(self):
		if not os.path.exists(self.path):
			print("Setting {} lock".format(self.name))
			timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

			with open(self.path, 'w+') as f:
				f.write(timestamp)

	def remove(self):
		if os.path.isfile(self.path):
			os.remove(self.path)

	def get_lock_time(self):
		for filename in os.listdir(self.locks):
			with open(self.locks + "/" + filename) as f:
				return f.read()

		return None
