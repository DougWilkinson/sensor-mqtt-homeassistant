# sensor.py
from machine import Pin,Timer
import time
import config

def version():
	return "0"
	# 0: break out from sensor.py

Device = config.Device

class Light:
	def __init__(self, name, light, attrs={}):

		self.light = light
		self.triggered = False
		self.state = Device(name, 'light', False, attrs)
		self.bright = Device(name + "_bri", 'light', 0, config=False)
		self.rgb = Device(name + "_rgb", 'light', "0,0,0", config=False)
		self.timer = Timer(-1)
		self.timer.init(period=200, mode=Timer.PERIODIC, callback=self.update) 

	def update(self, timer):
		if self.state.updatevalue or self.bright.updatevalue or self.rgb.updatevalue:

			if self.bright.updatevalue:
				self.bright.updatevalue = False
				self.rgb.set("{},{},{}".format(self.bright.value,self.bright.value,self.bright.value))
				self.bright.changed = True
			if self.rgb.updatevalue:
				self.rgb.updatevalue = False
				self.rgb.changed = True
			if self.state.updatevalue:
				self.state.updatevalue = False
				self.state.changed = True
			if self.state.value:
				r = self.rgb.value.split(",")
				self.light.set_color( ( int(r[0]),int(r[1]),int(r[2]) ) )
			else:
				self.light.set_color((0,0,0))
