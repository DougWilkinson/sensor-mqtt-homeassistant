# quest2.py
import config
from machine import I2C,Pin,ADC
import time

def version():
    return "4"
    # 4: convert to sensors

sensors = config.importer('sensors')
stats = sensors.Stats()
bootflags = sensors.BootFlags()

hassmqtt = config.importer('hassmqtt')

i2c_charge = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
charge = sensors.Ina219("charge", i2c_charge, poll=1, diff=0.05)

# charger relay on D5 (gpio 14)
relay = sensors.Switch("relay",14, initval=False)

# cable sensor with probe GPIO = ON
# > 800 : nothing connected to charging cable (relay off)
# < 800 : Charging cable connected to device to charge (relay off)

probe = Pin(12,Pin.OUT)
adc = ADC(0)

threshold = sensors.Value("threshold", initval=780)

# return True if connected to something (< threshold)
def cable_connected():
    probe.value(1)
    time.sleep_ms(1)
    val = adc.read()
    probe.value(0)    
    return "connected" if val < threshold.value else "disconnected"

cable = sensors.Value("cable", initval=cable_connected())

hass = hassmqtt.HassMqtt(config.nodename,sensors)

def main():

    while True:
        hass.Spin()

        # check cable connected only when relay off
        if not relay.value:
            newval = cable_connected()
            if newval != cable.value:
                cable.set(newval)

main()