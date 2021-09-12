# kitlight.py
import config
from machine import Pin
import time
import led0

def version():
	return "0"
	# 0: first real version 

sensor = config.importer('sensor')
stats = sensor.Stats()
bootflags = sensor.BootFlags()

hassmqtt = config.importer('hassmqtt')

strip = led.WS2812(0,20)

lights = sensor.Light("cabinet", strip)
mode = sensor.Sensor("mode", "auto")
motion = sensor.Input("motion",15)

hass = hassmqtt.HassMqtt(config.nodename,sensor)

def main():

	while True:
		hass.Spin()
		strip.spin()


main()