# value.py
from machine import Timer
import time
import config

def version():
	return "1"
	# 1: Added poller support for sensors

Device = config.Device

class Value:
	def __init__(self, name, initval=0, diff=0, minval=None, maxval=None, units=None, 
				callback=None, attrs={}, poll=-1):

		self.value = initval
		self.callback = callback
		self.triggered = False
		self.mqtt = Device(name, 'sensor', initval, diff, 
						minval, maxval, units, attrs,
						poll=poll, poller=self.update) 

	def update(self):
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
