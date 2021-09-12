# quest2.py
import config
from machine import I2C,Pin,ADC
import time

def version():
    return "1"
    # 1: update for sensor19

sensor = config.importer('sensor')
stats = sensor.Stats()
bootflags = sensor.BootFlags()

hassmqtt = config.importer('hassmqtt')

i2c_charge = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
charge = sensor.Ina219("charge", i2c_charge, polling=1000, diff=0.05)

# charger relay on D5 (gpio 14)
relay = sensor.Switch("relay",14, initval=False)

# cable sensor with probe GPIO = ON
# > 800 : nothing connected to charging cable (relay off)
# < 800 : Charging cable connected to device to charge (relay off)

probe = Pin(12,Pin.OUT)
adc = ADC(0)

threshold = sensor.Sensor("threshold", initval=780)

# return True if connected to something (< threshold)
def cable_connected():
    probe.value(1)
    time.sleep_ms(1)
    val = adc.read()
    probe.value(0)    
    return "connected" if val < threshold.value else "disconnected"

cable = sensor.Sensor("cable", initval=cable_connected())
brightness = sensor.Sensor("brightness", initval=10, minval=0, maxval=255, units="lux")

hass = hassmqtt.HassMqtt(config.nodename,sensor)

def main():

    while True:
        hass.Spin()

        # check cable connected only when relay off
        if not relay.value:
            newval = cable_connected()
            if newval != cable.value:
                cable.set(newval)

main()