from machine import Pin
import time
import config

def version():
    return "3"
    # 3: switched to sensors/Value

sensor = config.importer('sensors')
stats = sensor.Stats()
bootflags = sensor.BootFlags()

hass_mod = config.importer('hassmqtt')
HassMqtt = hass_mod.HassMqtt

brightness = sensor.Value("brightness", initval=40)
motion = sensor.Input("motion",5)

clock_mod = config.importer('clock','Clock')
Clock = clock_mod.Clock

hass = HassMqtt(config.nodename,sensor)

def main():
    thistime = Clock()
    lasttime = Clock()
    thistime.second = 1
    lasttime.second = 0
    
    secfade = time.ticks_ms()
    fadetime = 200
    tail = [0,0,0,0,0,0]
    sec = 0
    print("Waiting for time update ...")
    while hass.hour.value < 0:
        size = -2
        thistime.draw_hand(thistime.pose[sec], size , thistime.color_second, brightness.value)
        k = 1
        for i in tail:
            thistime.draw_hand(thistime.pose[i], size, thistime.color_second, int(brightness.value/len(tail) * (len(tail) - k ) ))
            k +=1
        tail.pop()
        tail.insert(0,sec)
        sec += 1
        if (sec > 11):
            sec = 0
        thistime.led.write()
        hass.Spin()
        time.sleep_ms(100)

    while True:
        if hass.hour.value >= 0:
            lasttime.hour = thistime.hour
            lasttime.minute = thistime.minute
            thistime.hour = hass.hour.value
            if thistime.hour > 11:
                thistime.hour = thistime.hour - 12
            thistime.minute = int(hass.minute.value / 5)

        hass.Spin()
        secbright = time.ticks_ms() - secfade 

        if secbright < fadetime:
            #thistime.draw_hand(start, len, color
            # Fade out last second hand
            thistime.draw_hand(thistime.pose[lasttime.second], thistime.len_second, thistime.color_second, int(brightness.value / 2 * (fadetime - secbright) / fadetime))
            # int(brightness * (fadetime - secbright) / fadetime))
            thistime.led.write()

        if secbright >= fadetime:
            # Turn off last second hand completely 
            thistime.draw_hand(thistime.pose[lasttime.second], thistime.len_second, thistime.color_second, 0)
            thistime.led.write()

        if secbright < (5 * fadetime): 
            # int(brightness * secbright / 1000)
            #color = [0,0,int(brightness * secbright / 1000)]
            # Brighten current second over 1 second time 
            thistime.draw_hand(thistime.pose[thistime.second], thistime.len_second, thistime.color_second, int(brightness.value * secbright / 1000))
            thistime.led.write()

        if secbright >= (5 * fadetime): 
            thistime.draw_hand(thistime.pose[thistime.second], thistime.len_second, thistime.color_second, brightness.value )
            thistime.led.write()

        if secbright > 5000:
            #print("Current brightness: ", brightness)
            lasttime.second = thistime.second
            thistime.second = thistime.second + 1
            if thistime.second == 12:
                thistime.second = 0
            thistime.display(thistime.minute, thistime.hour, -1,brightness.value,brightness.value)
            secfade = time.ticks_ms()

main()