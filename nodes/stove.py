# stove.py 
from machine import Pin
import time
import dht
import config

def version():
    return "1"
    # 1: remove hass.connected check

sensors = config.importer('sensors')
hassmqtt = config.importer('hassmqtt')
led  = config.importer('led')

stats = sensors.Stats()
bootflags = sensors.BootFlags()

stovedht = dht.DHT22(Pin(13))
stove = sensors.Dht("stove",stovedht)

sinkdht = dht.DHT22(Pin(4))
undersink = sensors.Dht("sink",sinkdht)

coffee = sensors.Analog("coffee")

strip = led.WS2812(0,20)

lights = sensors.Light("cabinet", strip)
mode = sensors.Value("mode", "auto")
motion = sensors.Input("motion",14)
ontime = sensors.Value("ontime", 60, attrs={"Value":"LED on time in seconds"} )

hass = hassmqtt.HassMqtt(config.nodename,sensors)

def main():

    while True:
        hass.Spin()
        strip.spin()

        if mode.value == "auto" and motion.triggered:
            motion.triggered = False
            strip.set_color((0,30,30))
            mode.set("timer")
            lastmotion = time.time()

        if mode.value == "timer" and time.time() - lastmotion > ontime.value:
            mode.set("auto")
            strip.set_color()


main()