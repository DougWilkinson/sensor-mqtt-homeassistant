# sensor.py
from machine import Pin,Timer,ADC,reset_cause
import time
import config
import network
from gc import mem_free
import dht
import sys

def version():
	return "22"
	# 22: added light class and triggered to "Input"

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

class Sensor:

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

class BootFlags:

	defaults = { 'reboots':{}, 'update':{}, 'update_result':{"200":"General"}, 
				'config': { "versions":config.current, 
							"mpy": sys.implementation[2],
							"image": sys.implementation[1],
							"reset_cause": reset_cause(),
							"MACaddr": config.espMAC,
							"ifconfig": config.wlan.ifconfig() 
							}
				}

	def add(self, name, attrs):
		return Sensor(name, initval=config.boot_flags[config.flagnames.index(name)], 
						callback=self.callback, attrs=attrs)

	def __init__(self, include=defaults.keys()):
		self.callback = config.set
		self.list = {}
		for name in include:  
			if name in BootFlags.defaults:
				self.list[name] = self.add(name, attrs=BootFlags.defaults[name])

class Stats:

	start_time = time.time()
	
	def update(self, timer):
		self.uptime.set(time.time() - Stats.start_time)
		self.rssi.set(config.wlan.status('rssi'))
		self.memfree.set(mem_free())
		# TODO If uptime > ?? reset reboots count to 0

	def __init__(self, polling=300000):

		self.uptime = Device("uptime",'sensor', 0, units='seconds')
		self.rssi = Device("rssi",'sensor', 0, units='dbm')
		self.memfree = Device("memfree",'sensor', 0, units='bytes')

		self.update(None)
		self.timer = Timer(-1)
		self.timer.init(period=polling, mode=Timer.PERIODIC, callback=self.update)
