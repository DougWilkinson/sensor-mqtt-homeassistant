# bathlight.py
import config
from machine import Pin,ADC
import time

def version():
	return "1"
	# 1: first real version 

sensors = config.importer('sensors')
stats = sensors.Stats()
bootflags = sensors.BootFlags()

hassmqtt = config.importer('hassmqtt')
led  = config.importer('led')
strip = led.WS2812(5,20)

lights = sensors.Light("vanity", strip)
mode = sensors.Value("mode", "auto")
night = sensors.Light("night", strip)
ontime = sensors.Value("ontime", 120, attrs={"Value":"LED on time in seconds"} )

motion = sensors.Input("motion",4)
vac_adc = ADC(0)
vacuum = sensors.Value("vacuum", "unknown")

hass = hassmqtt.HassMqtt(config.nodename,sensors)

def main():
	lastmotion = time.time()
	last_analog_read = time.ticks_ms()
	last_blink_check = time.time()
	last_vacuum_value = vac_adc.read()
	blink_count = 0

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

		if time.ticks_ms() - last_analog_read > 200:
			new = vac_adc.read()
			if abs(last_vacuum_value - new) > 10:
				last_vacuum_value = new
				blink_count +=1
			last_analog_read = 0

		if time.time() - last_blink_check > 10:
			print("blinks:",blink_count)
			if blink_count > 10 and vacuum.value != "charging":
				vacuum.set("charging")
			if blink_count <= 3 and vacuum.value != "off":
				vacuum.set("off")
			last_blink_check = time.time()
			blink_count = 0

main()