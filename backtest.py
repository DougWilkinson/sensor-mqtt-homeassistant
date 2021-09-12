# backtest.py (aka backdoor)
from machine import Pin
import time
import config
import random
import gc

def version():
    return "6"
    # 6: using new sensors module

gc.collect()

sensors = config.importer('sensors')
hassmqtt = config.importer('hassmqtt')
led  = config.importer('led')
stepclass = config.importer('stepclass')

stats = sensors.Stats()
bootflags = sensors.BootFlags()

backdoor = sensors.Input("backdoor", 4, pullup=False)
#backdoor = sensors.Input("backdoor", 4, pullup=True)

curtains = sensors.Value("curtains", initval="init" )
desired = sensors.Value("desired", initval=0)
position = sensors.Value("position", initval=0)
backoff = sensors.Value("backoff", initval=350)

strip = led.WS2812(0,20)

lights = sensors.Light("cabinet", strip)
mode = sensors.Value("mode", "auto")
motion = sensors.Input("motion",5)
ontime = sensors.Value("ontime", 60, attrs={"Value":"LED on time in seconds"} )

# limitmode = switch or encoder
limitmode = sensors.Value("limitmode",initval = "switch")
limitmode.triggered = True

gc.collect()

hass = hassmqtt.HassMqtt(config.nodename,sensors)

# backtest - inverted and no pullups

def main():
    lastmotion = time.time()

    while True:
        hass.Spin()
        strip.spin()

        if mode.value == "auto" and motion.triggered:
            motion.triggered = False
            strip.set_color((0,30,30))
            mode.set("timer")
            lastmotion = time.time()

        if not hass.connected or (mode.value == "timer" and time.time() - lastmotion > ontime.value):
            mode.set("auto")
            strip.set_color()

        if limitmode.triggered:
            limitmode.triggered = False
            if limitmode.value == "switch":
                slider = stepclass.Stepper(maxsteps=1000, backoff=backoff.value, inverted=True, open_limit_pin=14)
            else:
                slider = stepclass.Stepper(encoder_pin=14, maxsteps=10000, timeout=5000, backoff=backoff.value, inverted=True)
            desired.triggered

        if backoff.triggered:
            print("backoff: ",backoff.value)
            backoff.triggered = False
            slider.backoff = backoff.value
            limitmode.triggered = True

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