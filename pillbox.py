# pillbox.py
import config
import time
from machine import Pin
from neopixel import NeoPixel

def version():
    return "6"
    # 6: changed to ticks_diff() 

sensor = config.importer('sensor')
stats = sensor.Stats()
bootflags = sensor.BootFlags()

hass_mod = config.importer('hassmqtt')
HassMqtt = hass_mod.HassMqtt

def showmedstatus(led, medstatuslast):
    pulse = time.ticks_diff(time.ticks_ms(),medstatuslast)
    if pulse > 500:
        pulse = 500
        medstatuslast = time.ticks_ms()
    # sweeps range of brightness (default 30) 
    pulse = abs(int((brightness.value*2) * (pulse/500)) - brightness.value)
    pulse = 0 if pulse < 0 else pulse
    npulse = brightness.value - pulse
    npulse = 0 if npulse < 0 else npulse
    # Purple pulse - Invalid/Init state
    led[0] = [npulse >> 1,0,pulse >> 1 ]
    led[1] = [npulse >> 1,0,pulse >> 1 ]
    if medstatus.value == "good":
        led[0] = [0,int(brightness.value/3),0]
        led[1] = [0,int(brightness.value/3),0]
    if medstatus.value == "needed":
        led[0] = [pulse,0,0]
        led[1] = [pulse,0,0]
    if not pills.value:
        led[0] = [pulse >> 1,0,npulse >> 1]
        led[1] = [npulse >> 1,0,pulse >> 1]
    led.write()
    return medstatuslast

# Single pillbox pins
ledpin = Pin(5, Pin.OUT)
led = NeoPixel(ledpin, 2)

medstatus = sensor.Sensor("meds", "Init" )
brightness = sensor.Sensor("brightness", 15 )
pills = sensor.Input("pills", 4, invert=True)
buttonone = sensor.Input("buttonone", 14)
buttontwo = sensor.Input("buttontwo", 12)

# Must define hass after all sensors defined!
hass = HassMqtt(config.nodename,sensor) 

def main():
    medstatuslast = time.ticks_ms()
    while True:
        hass.Spin()
        #Add actions here
        medstatuslast = showmedstatus(led, medstatuslast)

main()