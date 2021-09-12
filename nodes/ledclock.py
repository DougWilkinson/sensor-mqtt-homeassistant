# ledclock.py
from neopixel import NeoPixel
from machine import Pin
import time
import config

def version():
    return "2"
    # 2: changed to ticks_diff() to solve rollover? similar to pillbox

sensor = config.importer('sensor')
stats = sensor.Stats()
bootflags = sensor.BootFlags()

hass_mod = config.importer('hassmqtt')
HassMqtt = hass_mod.HassMqtt

ledpin = Pin(5, Pin.OUT)
led = NeoPixel(ledpin, 13)

brightness = sensor.Sensor("brightness", initval=30)
facelight = sensor.Sensor("facelight", initval=1)

hass = HassMqtt(config.nodename,sensor)

def main():

    # Translate leds to location
    m = [6,5,4,3,2,1,0,11,10,9,8,7,12]

    hour = 0
    minute = 0
    second = 1
    lasthour = 0
    lastminute = 0
    lastsecond = 0
    timechange = True

    secfade = time.ticks_ms()

    while True:

        # secbright gets larger over time
        secbright = time.ticks_diff(time.ticks_ms(),secfade) 
        fadetime = 500

        # Spin when not fading (looks choppy if you do)
        if secbright > 1100:
            hass.Spin()


        # fade out last second
        if secbright < fadetime:
            led[m[11-lastsecond]] = (led[m[11-lastsecond]][0], 
                                    led[m[11-lastsecond]][1],
                                    int(brightness.value * (fadetime - 
                                    secbright) / fadetime) + 1 )
            led.write()

        # fade in new second
        if secbright < 1001:
            led[m[11-second]] = (led[m[11-second]][0], 
                                led[m[11-second]][1], 
                                int(brightness.value * secbright / 1000))
            led.write()

        if (secbright > 100 ) and hass.hour.value < 0:
            hass.Spin()
            secbright = 5001
            timechange = True
            led[m[11-lastsecond]] = (facelight.value,facelight.value,facelight.value)

            if second == 11 and hass.hour.value < 0:
                lastminute = minute
                minute += 1
                if minute > 11:
                    minute = 0
                    lasthour = hour
                    hour += 1
                if hour > 11:
                    hour =   0

        if secbright > 5000:
            lastsecond = second
            second = second + 1
            if second == 12:
                second = 0
            secfade = time.ticks_ms()

        if (hass.minute.value != minute) and (hass.hour.value >= 0):
            lasthour = hour
            lastminute = minute
            hour = hass.hour.value
            if hour > 12:
                hour = hour - 12
            if hour == 0:
                hour = 12
            minute = int(hass.minute.value / 5)
            if minute == 0:
                minute = 12
            hass.minute.value = minute
            timechange = True

        if timechange or brightness.triggered or facelight.triggered:
            led.fill((facelight.value,facelight.value,facelight.value))
            led[m[12-hour]] = (brightness.value,0,0)
            led[m[12-minute]] = (led[m[12-minute]][0],brightness.value,0)
            led.write()
            brightness.triggered = False
            facelight.triggered = False
            timechange = False

main()