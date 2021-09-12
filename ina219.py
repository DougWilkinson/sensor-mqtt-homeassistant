# ina219.py
from machine import Pin, Timer
import time
import config

def version():
	return "0"
	# 0: break out from sensor.py

Device = config.Device

class Ina219:

	def write_register(self, register, register_value):
		register_bytes = bytearray([(register_value >> 8) & 0xFF, register_value & 0xFF])
		self.pin.writeto_mem(self.address, register, register_bytes)

	def read_register(self, register):
		register_bytes = self.pin.readfrom_mem(self.address, register, 2)
		register_value = int.from_bytes(register_bytes, 'big')
		if register_value > 32767:
			register_value -= 65536
		return register_value
	
	def __init__(self, name, pin, k=0.0000214292, diff=0.05, polling=5000):
		self.pin = pin
		self.address = 0x40
		self.write_register(0x05, 16793)
		self.write_register(0, 2463)
		self.k = k
		self.mqtt = Device(name, 'sensor', 0.0, diff=diff, minval=0, units="A")
		self.update(None)
		self.timer = Timer(-1)
		self.timer.init(period=polling, mode=Timer.PERIODIC, callback=self.update) 

	def update(self, timer):
		self.mqtt.set(round(self.read_register(0x04) * self.k,3))
		self.value = self.mqtt.value
