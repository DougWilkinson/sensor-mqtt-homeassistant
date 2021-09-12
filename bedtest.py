# bedtest.py
import config
from machine import Pin
import time

def version():
    return "1"
    # 1: first real version 

hx = config.importer('hx')

sensor = config.importer('sensor')
stats = sensor.Stats()
bootflags = sensor.BootFlags()

hassmqtt = config.importer('hassmqtt')

# how lbed is setup
hxsensor = hx.HX711(14,12)

minthresh = sensor.Sensor("minhx", initval=3500)
maxthresh = sensor.Sensor("maxhx", initval=4500)
diffhx = sensor.Sensor("diffhx", initval=hxsensor.diff)
scale = sensor.Sensor("scale", initval=hxsensor.value())
threshold = sensor.Sensor("threshold", initval="init")

# head board    top view looking down at bed
# rbed   lbed   right/left from perspective of being in bed
# foot board    laying face up
# rbed has issues (range drops to < 1000, normal 2700 - 8000)
# lbed seems fine (range 1700 - 4000)

# status = sensor.Sensor("status", "sensor", False)

# outbed = "lower threshold to cross to be "out" of bed
# inbed = "upper threshold to be "in" bed


hass = hassmqtt.HassMqtt(config.nodename,sensor)

def main():

    lasthx = scale.value
    while True:
        hass.Spin()
        if hxsensor.triggered or minthresh.triggered or maxthresh.triggered:
            scale.set(hxsensor.value())
            hxsensor.triggered = False
            if scale.value < minthresh.value:
                threshold.set("min")
            if scale.value > maxthresh.value:
                threshold.set("max")
        if diffhx.triggered:
            hxsensor.diff = diffhx.value
            diffhx.triggered = False

main()