# fridgetest.py
import config
from machine import Pin
import dht
import time

def version():
    return "2"
    # 2: convert to sensors 

sensors = config.importer('sensors')
stats = sensors.Stats()
bootflags = sensors.BootFlags()

hassmqtt = config.importer('hassmqtt')

# real fridge freezer=14, fridge=12
freezer_dht = dht.DHT22(Pin(14))
freezer = sensors.Dht("freezer",freezer_dht)

fridge_dht = dht.DHT22(Pin(12))
fridge = sensors.Dht("fridge",fridge_dht)

motion = sensors.Input("motion",13)

hass = hassmqtt.HassMqtt(config.nodename,sensors)

def main():

    while True:
        hass.Spin()

main()