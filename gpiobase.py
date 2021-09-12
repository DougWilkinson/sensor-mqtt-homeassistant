# gpiobase.py Analog, Switch, Input
from machine import ADC, Pin, Timer
import time
import config

def version():
	return "0"
	# 0: break out from sensor.py

Device = config.Device

class Input:

	def __init__(self, name, pin, pullup=False, invert=False):
		# pullup: True=YES
		# pin: gpio#, period: None or ms
		if pullup:
			self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
		else:
			self.pin = Pin(pin, Pin.IN)
		self.invert = invert
		self.triggered = False
		self.mqtt = Device(name, 'binary_sensor', False) 
		self.update(None)
		self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.update) 

	def update(self, irq):
		self.lasttime = time.ticks_ms()
		self.value = not (self.pin.value() > 0) if self.invert else self.pin.value() > 0
		self.mqtt.set(self.value)
		if self.value:
			self.triggered = True

class Switch:

	def __init__(self, name, pin, initval=False):
		# pin: gpio#, period: None or ms
		self.value = initval
		self.triggered = False
		self.pin = Pin(pin, Pin.OUT)
		self.pin.value(initval)
		self.mqtt = Device(name, 'switch', initval) 
		self.timer = Timer(-1)
		self.timer.init(period=100, mode=Timer.PERIODIC, callback=self.update) 

	# sync protocol (like mqtt) updated values here
	def update(self, timer):
		if self.mqtt.updatevalue:
			self.mqtt.updatevalue = False
			self.value = self.mqtt.value
			self.pin.value(self.value)
			self.mqtt.changed = True
			self.triggered = True

	def set(self, newvalue=True):
		self.mqtt.set(newvalue)
		self.pin.value(newvalue)

class Analog:

	def __init__(self, name, pin=0, k=0.003028, diff=0.05, units='v', polling=5000):
		self.pin = ADC(pin)
		self.k = k
		self.mqtt = Device(name, 'sensor', 0.0, diff, units=units)
		self.update(None)
		self.timer = Timer(-1)
		self.timer.init(period=polling, mode=Timer.PERIODIC, callback=self.update) 

	def update(self, timer):
		self.mqtt.set(self.pin.read() * self.k)
		self.value = self.mqtt.value
