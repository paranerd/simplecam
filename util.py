from datetime import datetime

class Util:
	def log(source, msg):
		print(datetime.now().strftime("%Y%m%d_%H%M%S") + " | " + source + " | " + str(msg))
