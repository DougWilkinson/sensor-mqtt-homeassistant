# dht.py
from machine import Timer
import time
import config

def version():
	return "2"
	# 2: add poller support

Device = config.Device

class Dht:

	def __init__(self, name, dht, poll=5):
		self.dht = dht
		self.temp = Device(name + "_" + "temp", 
							'sensor', 
							0.0, 
							diff=0.3, 
							minval=-50, 
							maxval=130,
							units = 'F', poll=poll, poller=self.update) 
		self.humidity = Device(name + "_" + "humidity", 
							'sensor', 
							0, 
							diff=1, 
							minval=0, 
							maxval=100,
							units = "%")
		self.update()

	def update(self):
		try:
			self.dht.measure()
			self.temp.set(round((self.dht.temperature() * 9 / 5) + 32,1))
			self.humidity.set(int(round(self.dht.humidity(),0)))
		except OSError as e:
			print("DHT read error: " + str(e))
