import os

class LockManager:
	def __init__(self, name):
		self.locks = os.path.dirname(os.path.realpath(__file__)) + "/locks"
		self.name = name + ".lock"

		if not os.path.exists(self.locks):
			os.makedirs(self.locks)

	def set(self, content):
		with open(self.locks + "/" + self.name, 'w+') as f:
			f.write(content)

	def read(self):
		with open(self.locks + "/" + os.listdir(self.locks)[0]) as f:
			return f.read()

	def readOther(self):
		for filename in os.listdir(self.locks):
			if filename != self.name:
				with open(self.locks + "/" + filename) as f:
					return f.read()

	def remove(self):
		if os.path.isfile(self.locks + "/" + self.name):
			os.remove(self.locks + "/" + self.name)

lm = LockManager('motion')
print(lm.readOther())
