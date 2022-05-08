# rbed.py
import config
import time

def version():
    return "3"
    # 3: rewrite for polling and new Hx sensor 

sensors = config.importer('sensors')
stats = sensors.Stats()
bootflags = sensors.BootFlags()

hassmqtt = config.importer('hassmqtt')

scale = sensors.Hx("scale", statename="state", pd_sck=14, dout=12, lowhx=1500, diff=30)

# head board    top view looking down at bed
# rbed   lbed   right/left from perspective of being in bed
# foot board    laying face up
# rbed has issues (range drops to < 1000, normal 2700 - 8000)
# lbed seems fine (range 1700 - 4000)
# new rbed (this code) range 2600 - 7200 (about same as before)

# status = sensor.Value("status", "sensor", False)


hass = hassmqtt.HassMqtt(config.nodename,sensors)

def main():

    while True:
        hass.Spin()

main()