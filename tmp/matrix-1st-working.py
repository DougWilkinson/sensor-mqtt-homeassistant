# matrix.py
import config
import time
import random

sensor = config.importer('sensor')
hass_mod = config.importer('hassmqtt','HassMqtt')
HassMqtt = hass_mod.HassMqtt


def version():
    return "2"
    # 1: Added clock support
    # 2: fixed ending space for text and blinking colon

# matrix clock and text view
# Revised 8/7/2021

brightness = sensor.Sensor("brightness", initval=1)
mode = sensor.Sensor("mode", initval='clock')
trans = sensor.Sensor("trans", initval='scroll')
speed = sensor.Sensor("speed", initval=50)
delay = sensor.Sensor("delay", initval=1)
text = sensor.Sensor("text", initval="Hello World!!")

# {"heartbeat": "ON", "Hour": "17", "Minute": "57"}

def main():
    from ledmatrix import LedMatrix
    import font6a
    lastmode = mode.value
    delaytime = time.ticks_ms()
    smallfont = LedMatrix(font6a.bitmap,font6a.map,6)
    hass = HassMqtt(config.nodename,sensor)
    hass.minute.value = 99
    h = '??'
    while True:
        hass.Spin()
        if text.value != '':
            smallfont.clear()
            smallfont.text(text.value + " ")
            text.value = ''
            if mode.value != "text":
                lastmode = mode.value
            mode.set("text")
        if smallfont.uptext() and mode.value == 'text':
            mode.set(lastmode)
        if mode.value == 'clock' and (time.ticks_ms() - delaytime > delay.value):
            if hass.hour.value < 0:
                hass.minute.value += 1
            else:
                h = ' ' + str(hass.hour.value)
            m = '0' + str(hass.minute.value)

            smallfont.show(ord(m[-1]),0,speed.value)
            smallfont.show(ord(m[-2]),1,speed.value)
            smallfont.show(ord(h[-1]),3,speed.value)
            smallfont.show(ord(h[-2]),4,speed.value)
            delaytime = time.ticks_ms()

        if mode.value == 'clock':
            smallfont.show((time.time() % 2 * 32) + ((1 - time.time() % 2) * 58), digit=2, notrans=True)

        if trans.value != smallfont.trans:
            smallfont.trans = trans.value


main()
