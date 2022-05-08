# gpiobase.py Analog, Switch, Input
from machine import ADC, Pin, Timer
import time
import config

def version():
	return "4"
	# 4: changed to use polling 

Device = config.Device

class Input:

	def __init__(self, name, pin, pullup=False, inverted=False):
		# pullup: True=YES
		# pin: gpio#, period: None or ms
		if pullup:
			self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
		else:
			self.pin = Pin(pin, Pin.IN)
		self.inverted = inverted
		self.triggered = False
		self.mqtt = Device(name, 'binary_sensor', False) 
		self.update(None)
		self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.update) 

	def update(self, irq):
		self.lasttime = time.ticks_ms()
		self.value = not (self.pin.value() > 0) if self.inverted else self.pin.value() > 0
		self.mqtt.set(self.value)
		if self.value:
			self.triggered = True

class Switch:

	def __init__(self, name, pin, initval=False, poll=-1):
		# pin: gpio#
		self.value = initval
		self.triggered = False
		self.pin = Pin(pin, Pin.OUT)
		self.pin.value(initval)
		self.mqtt = Device(name, 'switch', initval, poll=poll, poller=self.update) 

	# sync protocol (like mqtt) updated values here
	def update(self):
		if self.mqtt.updatevalue:
			self.mqtt.updatevalue = False
			self.value = self.mqtt.value
			self.pin.value(self.value)
			self.mqtt.changed = True
			self.triggered = True

	def set(self, newvalue=True):
		self.mqtt.set(newvalue)
		self.value = newvalue
		self.pin.value(newvalue)

class Analog:

	def __init__(self, name, pin=0, k=0.003028, diff=0.05, units='v', poll=5):
		self.pin = ADC(pin)
		self.k = k
		self.mqtt = Device(name, 'sensor', 0.0, diff, units=units, poll=poll, poller=self.update)
		self.update()

	def update(self):
		self.mqtt.set(self.pin.read() * self.k)
		self.value = self.mqtt.value
