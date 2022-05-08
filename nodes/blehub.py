# blehub.py
import config
import time

def version():
    return "1"
    # 1: changed to auto-discover bluetooth
    # Uses: ble8 

sensors = config.importer('sensors')
stats = sensors.Stats()
bootflags = sensors.BootFlags()

hassmqtt = config.importer('hassmqtt')

blehub = sensors.BLE()

hass = hassmqtt.HassMqtt(config.nodename,sensors)

def main():

    while True:
        hass.Spin()

main()