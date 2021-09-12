# smartcharger.py
import config
from machine import I2C,Pin

def version():
    return "11"
    # 11: changes for sensor19/20

sensor = config.importer('sensor')
stats = sensor.Stats()
bootflags = sensor.BootFlags()

hassmqtt = config.importer('hassmqtt')

i2cbatt = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
ext_battery = sensor.Ina219("extbatt", i2cbatt, polling=60000, diff=0.05)

# oculus current sensor on D6/D7
i2cvr = I2C(scl=Pin(12), sda=Pin(13), freq=100000)
oculus_battery = sensor.Ina219("oculus",i2cvr, polling=60000, diff=0.05)

# oculus charger relay on D5 (gpio 14)
vrpower = sensor.Switch("vrpower",14, initval=False)

# supercap voltage
adc = sensor.Analog("supercap", polling=300000, diff=0.05)

brightness = sensor.Sensor("brightness", initval=10, minval=0, maxval=255, units="lux")

hass = hassmqtt.HassMqtt(config.nodename,sensor)

def main():

    while True:
        hass.Spin()
        # Do stuff, return True 

main()