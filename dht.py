# dht.py
from machine import Timer
import time
import config

def version():
	return "0"
	# 0: break out from sensor.py

Device = config.Device

class Dht:

	def __init__(self, name, dht, polling=5000):
		self.dht = dht
		self.temp = Device(name + "_" + "temp", 
							'sensor', 
							0.0, 
							diff=0.2, 
							minval=-50, 
							maxval=130,
							units = 'F') 
		self.humidity = Device(name + "_" + "humidity", 
							'sensor', 
							0, 
							diff=1, 
							minval=0, 
							maxval=100,
							units = "%")
		self.update(None)            
		self.timer = Timer(-1)
		self.timer.init(period=polling, mode=Timer.PERIODIC, callback=self.update) 

	def update(self, timer):
		try:
			self.dht.measure()
			self.temp.set(round((self.dht.temperature() * 9 / 5) + 32,1))
			self.humidity.set(int(round(self.dht.humidity(),0)))
		except OSError as e:
			print("DHT read error: " + str(e))
