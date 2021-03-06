# kitlight.py
import config
from machine import Pin
import time

def version():
	return "5"
	# 5: fixed tabs and spaces(3) and reset trigger if lights on 

sensors = config.importer('sensors')
stats = sensors.Stats()
bootflags = sensors.BootFlags()

hassmqtt = config.importer('hassmqtt')
led  = config.importer('led')
strip = led.WS2812(5,40)

lights = sensors.Light("cabinet", strip)
mode = sensors.Value("mode", "auto")
motion = sensors.Input("motion",4)
night = sensors.Light("night", strip)
ontime = sensors.Value("ontime", 120, attrs={"Value":"LED on time in seconds"} )

hass = hassmqtt.HassMqtt(config.nodename,sensors)

def main():
	lastmotion = time.time()

	while True:
		hass.Spin()
		strip.spin()

		if mode.value == "auto" and not lights.state.value and (motion.triggered or night.state.value):
			print("nightlight on")
			motion.triggered = False
			night.on()
			mode.set("timer")
			lastmotion = time.time()

		if motion.triggered and not lights.state.value and mode.value == "timer":
			print("reset nightlight timer")
			motion.triggered = False
			lastmotion = time.time()

		if lights.state.value and (mode.value == "timer" or motion.triggered):
			print("lights on, nightlight timer off or trigger reset")
			motion.triggered = False
			mode.set("auto")

		if mode.value == "timer" and time.time() - lastmotion > ontime.value:
			print("timer or not connected, mode-auto, nightlight off")
			mode.set("auto")
			night.off()
			strip.set_color()

main()