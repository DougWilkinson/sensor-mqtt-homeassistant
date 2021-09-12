# value.py
from machine import Timer
import time
import config

def version():
	return "0"
	# 0: break out from sensor.py

Device = config.Device

class Value:
	def __init__(self, name, initval=0, diff=0, minval=None, maxval=None, units=None, 
				polling=None, callback=None, attrs={}):

		self.value = initval
		self.callback = callback
		self.triggered = False
		self.mqtt = Device(name, 'sensor', initval, diff, 
								minval, maxval, units, attrs) 
		self.timer = Timer(-1)
		self.timer.init(period=100, mode=Timer.PERIODIC, callback=self.update) 

	def update(self, timer):
		if self.mqtt.updatevalue:
			self.value = self.mqtt.value
			self.mqtt.updatevalue = False
			self.triggered = True
			if self.callback is not None:
				self.callback(self.mqtt.name,self.mqtt.value)

	# Convenience for setting new value, mqtt class handles actual value/publishing
	def set(self, newvalue):
		self.mqtt.set(newvalue)
		self.value = newvalue
