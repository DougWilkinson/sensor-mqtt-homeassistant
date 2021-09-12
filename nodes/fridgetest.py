# fridgetest.py
import config
from machine import Pin
import dht
import time

def version():
    return "1"
    # 1: added bootflag and stats for new "sensor19" methods 

sensor = config.importer('sensor')
stats = sensor.Stats()
bootflags = sensor.BootFlags()

hassmqtt = config.importer('hassmqtt')

# real fridge freezer=14, fridge=12
freezer_dht = dht.DHT22(Pin(12))
freezer = sensor.Dht("freezer",freezer_dht)

fridge_dht = dht.DHT11(Pin(5))
fridge = sensor.Dht("fridge",fridge_dht)

motion = sensor.Input("motion",2)

hass = hassmqtt.HassMqtt(config.nodename,sensor)

def main():

    while True:
        hass.Spin()


main()