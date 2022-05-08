# gmclock.py
import time
import config

def version():
    return "1"
    # 1: inverted qsense

sensors = config.importer('sensors')
stats = sensors.Stats()
bootflags = sensors.BootFlags()

hass_mod = config.importer('hassmqtt')
HassMqtt = hass_mod.HassMqtt

# chime sensor
# test rig
#qsense = sensors.Input("qsense", 14, inverted=True, pullup=False)
# actual clock
qsense = sensors.Input("qsense", 4, inverted=True, pullup=False)

#chime used to turn on or off, pin 0 not really used
chime = sensors.Switch("chime", pin=0, initval=False)
#chime_status reflects actual state of switch/motor
chime_status = sensors.Value("status", initval=False)

# range for on/off to move motor
swing = sensors.Value("swing", initval=600)

# Back off motor (percent)

backoff = sensors.Value("backoff", initval=2, attrs={"Percent of swing to back off"})

hass = HassMqtt(config.nodename,sensors)

stepclass = config.importer('stepclass')

# dir and step pins reversed on this
#backtest rig
#slider = stepclass.Stepper(open_limit_pin=2, close_limit_pin=2, inverted=True, pullups=True, backoff=0, maxsteps=swing.value )
#gmclock actual
slider = stepclass.Stepper(dir_pin=13, step_pin=15, open_limit_pin=2, close_limit_pin=2, inverted=True, pullups=True, backoff=0, maxsteps=swing.value )

def main():
    last_chimed = time.time() - 500

    while True:
        hass.Spin()

        if qsense.triggered:
            qsense.triggered = False
            print("Chime sensed")
            last_chimed = time.time()

        if chime_status.triggered:
            chime_status.triggered = False
            if not chime_status.value:
                print("Forcing chime off!")
                print(slider.open(0))
                slider.open(backoff.value)
                chime.set(False)

        # turn on chime any time
        if chime.triggered and chime.value and not chime_status.value:
            chime.triggered = False
            print(slider.open(100))
            slider.open(100-backoff.value)
            chime_status.set(True)

        # only turn chime off 1-5 minutes after chime sensed
        if time.time() - last_chimed > 60 and time.time() - last_chimed < 400:
            if chime.triggered and not chime.value and chime_status.value:
                chime.triggered = False
                print(slider.open(0))
                slider.open(backoff.value)
                chime_status.set(False)
        
        if swing.triggered:
            swing.triggered = False
            print("Swing set to: ", swing.value)
            slider.maxsteps = swing.value

main()
