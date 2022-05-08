from machine import Pin
import time
import config
import random

def version():
    return "4"
    # 4: updated to sensors

sensors = config.importer('sensors')
stats = sensors.Stats()
bootflags = sensors.BootFlags()

hass_mod = config.importer('hassmqtt')
HassMqtt = hass_mod.HassMqtt

door = sensors.Input("door", 4, pullup=False)
#backdoor = sensor.Input("backdoor", 4, pullup=True)

curtains = sensors.Value("curtains", initval="init" )
desired = sensors.Value("desired", initval=0)
position = sensors.Value("position", initval=0)
backoff = sensors.Value("backoff", initval=350)

hass = HassMqtt(config.nodename,sensors)

stepclass = config.importer('stepclass')
slider = stepclass.Stepper(inverted=False, pullups=True, backoff=backoff.value)

def main():

    while True:
        hass.Spin()

        if backoff.triggered:
            print("backoff: ",backoff.value)
            backoff.triggered = False
            slider.backoff = backoff.value

        if desired.triggered:
            desired.triggered = False
            print("setting position: ",desired.value)
            curtains.set(slider.open(desired.value))
            if curtains.value == 'open' or curtains.value == 'closed':
                if desired.value < 0:
                    desired.set(0)
                position.set(desired.value)
            print("Curtains: ",curtains.value)
            print("position: ",position.value)

main()