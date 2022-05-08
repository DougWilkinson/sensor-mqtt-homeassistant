# sensors.py
from machine import reset_cause
from gc import mem_free
import sys
import time
import config

def version():
    return "4"
    # 4: added BLE to list 

mqttdevice = config.importer('mqttdevice')

list = mqttdevice.list
config.Device = mqttdevice.Device

if 'light' in config.current:
	light = config.importer('light')
	Light = light.Light

if 'gpiobase' in config.current:
	gpiobase = config.importer('gpiobase')
	Switch = gpiobase.Switch
	Input = gpiobase.Input
	Analog = gpiobase.Analog

if 'value' in config.current:
	value = config.importer('value')
	Value = value.Value

if 'ina219' in config.current:
	ina219 = config.importer('ina219')
	Ina219 = ina219.Ina219

if 'ble' in config.current:
	ble = config.importer('ble')
	BLE = ble.BLE

if 'dht' in config.current:
	dht = config.importer('dht')
	Dht = dht.Dht

if 'hx' in config.current:
	hx = config.importer('hx')
	Hx = hx.HX711

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
		return Value(name, initval=config.boot_flags[config.flagnames.index(name)], 
						callback=self.callback, attrs=attrs)

	def __init__(self, include=defaults.keys()):
		self.callback = config.set
		self.list = {}
		for name in include:  
			if name in BootFlags.defaults:
				self.list[name] = self.add(name, attrs=BootFlags.defaults[name])

class Stats:

	start_time = time.time()
	
	def update(self):
		self.uptime.set(time.time() - Stats.start_time)
		self.rssi.set(config.wlan.status('rssi'))
		self.memfree.set(mem_free())
		# TODO If uptime > ?? reset reboots count to 0

	def __init__(self):

		self.uptime = config.Device("uptime",'sensor', 0, units='seconds', poll=300, poller=self.update)
		self.rssi = config.Device("rssi",'sensor', 0, units='dbm')
		self.memfree = config.Device("memfree",'sensor', 0, units='bytes')
		self.update()
