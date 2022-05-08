# test.py (aka matrix clock)
import config
import time
import random
import gc

def version():
    return "14"
    # 14: fixed sensor to sensors and clear

sensors = config.importer('sensors')
stats = sensors.Stats()
bootflags = sensors.BootFlags()

hass_mod = config.importer('hassmqtt','HassMqtt')
HassMqtt = hass_mod.HassMqtt

from ledmatrix import LedMatrix
import font6a

def convert_time(hour,minute):
    h = ' ' + str(hour)
    m = '0' + str(minute)
    return [ord(h[-2]), ord(h[-1]), 58, ord(m[-2]), ord(m[-1])]
    
brightness = sensors.Value("brightness", initval=1)
mode = sensors.Value("mode", initval='init')
trans = sensors.Value("trans", initval='scroll')
speed = sensors.Value("speed", initval=50)
delay = sensors.Value("delay", initval=900)
text = sensors.Value("text", initval="")

# {"heartbeat": "ON", "Hour": "17", "Minute": "57"}

gc.collect()

hass = HassMqtt(config.nodename,sensors)

def main():
    uselocaltime = False
    localminute = 0
    localhour = 0
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
        
        if smallfont.uptext():
            
            # show cool display until time
            if hass.hour.value >= 0 and mode.value == 'init':
                smallfont.clear()
                mode.set('clock')

            if mode.value == 'burst' or mode.value == 'init':
                smallfont.burst(int(speed.value/10))

            # if hass.m.v is updated by mqtt, stop using localtime
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
                localminute = hass.minute.value
                localhour = hass.hour.value
                lastdigits = [0,0,0,0,0]
                smallfont.fg = (1,0,0)

            if mode.value == 'clock':
                if uselocaltime:
                    digits = convert_time(localhour, localminute)
                else:
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

        if time.time() - lastupdate > 64 and uselocaltime:
            lastupdate = time.time()
            localminute += 1

            if localminute > 59:
                localminute = 0
                localhour += 1

            if localhour > 23:
                localhour = 0

        if trans.value != smallfont.trans:
            smallfont.trans = trans.value


main()

