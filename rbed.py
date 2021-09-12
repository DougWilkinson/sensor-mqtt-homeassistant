# rbed.py
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
hxsensor = hx.HX711(14,12, diff=30)

minthresh = sensor.Sensor("minhx", initval=3500)
maxthresh = sensor.Sensor("maxhx", initval=4500)
diffhx = sensor.Sensor("diffhx", initval=hxsensor.diff)
scale = sensor.Sensor("scale", initval=hxsensor.value, units="hx")
threshold = sensor.Sensor("threshold", initval="init")

# head board    top view looking down at bed
# rbed   lbed   right/left from perspective of being in bed
# foot board    laying face up
# rbed has issues (range drops to < 1000, normal 2700 - 8000)
# lbed seems fine (range 1700 - 4000)
# new rbed (this code) range 2600 - 7200 (about same as before)

# status = sensor.Sensor("status", "sensor", False)

# outbed = "lower threshold to cross to be "out" of bed
# inbed = "upper threshold to be "in" bed


hass = hassmqtt.HassMqtt(config.nodename,sensor)

def main():

    lasthx = scale.value
    minthresh.triggered = True

    while True:
        hass.Spin()
        if hxsensor.triggered or minthresh.triggered or maxthresh.triggered:

            if hxsensor.triggered:
                scale.set(round(hxsensor.value,1))
                print(hxsensor.values)
                hxsensor.triggered = False

            minthresh.triggered = False
            maxthresh.triggered = False
            threshold.set("middle")
            if scale.value < minthresh.value:
                threshold.set("under")
            if scale.value > maxthresh.value:
                threshold.set("over")

        if diffhx.triggered:
            hxsensor.diff = diffhx.value
            diffhx.triggered = False

main()