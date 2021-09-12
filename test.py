# test.py (aka matrix clock)
import config
import time
import random
import gc

def version():
    return "10"
    # 10: Switched to sensors modular

sensor = config.importer('sensors')
stats = sensor.Stats()
bootflags = sensor.BootFlags()

hass_mod = config.importer('hassmqtt','HassMqtt')
HassMqtt = hass_mod.HassMqtt

from ledmatrix import LedMatrix
import font6a

def convert_time(hour,minute):
    h = ' ' + str(hour)
    m = '0' + str(minute)
    return [ord(h[-2]), ord(h[-1]), 58, ord(m[-2]), ord(m[-1])]
    
brightness = sensor.Value("brightness", initval=1)
mode = sensor.Value("mode", initval='init')
trans = sensor.Value("trans", initval='scroll')
speed = sensor.Value("speed", initval=50)
delay = sensor.Value("delay", initval=900)
text = sensor.Value("text", initval="")

# {"heartbeat": "ON", "Hour": "17", "Minute": "57"}

gc.collect()

hass = HassMqtt(config.nodename,sensor)

def main():
    uselocaltime = False
    lastminute = 0
    lastupdate = time.time() 
    lastblink = time.ticks_ms()
    colon = True
    smallfont = LedMatrix(font6a.bitmap,font6a.map,6)
    hass.minute.value = 0
    lastdigits = [0,0,0,0,0]
    digit_index = 4
    while True:
        hass.Spin()
        
        if time.time() - lastupdate > 60:
            lastupdate = time.time()
            hass.minute.value += 1

            if hass.minute.value > 59:
                hass.minute.value = 0
                hass.hour.value += 1

            if hass.hour.value > 23:
                hass.hour.value = 0

        if smallfont.uptext():
            
            # show cool display until time
            if hass.hour.value >= 0 and mode.value == 'init':
                mode.set('clock')

            if mode.value == 'burst' or mode.value == 'init':
                smallfont.burst(int(speed.value/10))

            # if hass.m.v is updated by mqtt, reset uselocaltime
            if hass.minute.value != lastminute and digit_index == 4:
                lastminute = hass.minute.value
                lastupdate = time.time()
                if uselocaltime:            
                    uselocaltime = False
                    lastdigits = [0,0,0,0,0]
                    smallfont.fg = (0,1,1)
            
            # set to red at 55 secs
            if time.time() - lastupdate > 54 and not uselocaltime and digit_index == 4:
                uselocaltime = True
                lastdigits = [0,0,0,0,0]
                smallfont.fg = (1,0,0)

            if mode.value == 'clock':
                digits = convert_time(hass.hour.value, hass.minute.value)
                if lastdigits[digit_index] != digits[digit_index]:
                    lastdigits[digit_index] = digits[digit_index]
                    smallfont.show(digits[digit_index], 4-digit_index, speed.value)
                digit_index -= 1
                if digit_index == 2:
                    digit_index = 1
                if digit_index < 0:
                    digit_index = 4
                    
                if time.ticks_ms() - lastblink > delay.value:
                    lastblink = time.ticks_ms()
                    smallfont.show(58 if colon else 32, digit=2, notrans=True)
                    colon = not colon

            # Display text if set but only during clock mode
            # Put last to clear display
            if text.value != '':
                smallfont.clear()
                smallfont.text(text.value + " ")
                text.value = ''
                lastdigits = [0,0,0,0,0]
                digit_index = 4

        if trans.value != smallfont.trans:
            smallfont.trans = trans.value


main()

