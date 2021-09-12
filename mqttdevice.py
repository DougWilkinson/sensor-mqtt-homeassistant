# sensor.py
from machine import Timer
import time
import sys

def version():
	return "0"
	# 0: created to break apart sensor.py

list = {}
	
class Device:
	def __init__(self, name, device_class, initval, diff=0, 
				minval=None, maxval=None, units=None, attrs={}, 
				config=True, local=False):
		if name in list:
			print("Using existing object for {}".format(name))
			return list[name]

		vtype = type(initval)

		self.name = name
		self.type = vtype
		self.device_class = device_class

		# Signals user changed value, should be published (mqtt)
		self.changed = True
		
		# received new value (from mqtt), update for user
		self.updatevalue = False

		self.attrs = attrs
		self.local = local
		self.config = config
		self.value = initval
		self.diff = diff
		self.minval = minval
		self.maxval = maxval
		self.units = units
		list[name] = self
		if units is None:
			units = ""
		print("{}: {} = {} {}".format(device_class, 
								name,initval,units))

	def set(self, newval):
		changed = False

		if self.type is int or self.type is float:
			if self.maxval is not None and newval > self.maxval:
				newval = self.maxval
			if self.minval is not None and newval < self.minval:
				newval = self.minval
			if abs(newval - self.value) >= self.diff:
				self.value = newval
				changed = True

		if self.type is bool and newval != self.value:
			self.value = not self.value
			changed = True

		if self.type is str:
			self.value = newval
			changed = True

		if changed:
			self.changed = True

