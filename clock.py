from machine import Pin
from neopixel import NeoPixel
import time

def version():
    return "0"
    # 0: Revised to new format

class Clock:

    pose = (10, -27, 48, -65, 86, -103, -8, 29, -46, 67, -84, 105) 

    def __init__(self, numleds=114, pin=14):
        ledpin = Pin(pin, Pin.OUT)
        self.numleds = numleds
        self.led = NeoPixel(ledpin, numleds)
        self.clear()

        self.brightness = 20
        self.color_second = [0,0,255]
        self.color_minute = [0,255,0]
        self.color_hour = [255,0,0]
        
        self.len_second = -2
        self.len_minute = 8
        self.len_hour = 6

        self.update()

        self.quarters = True

    def draw_hand(self, start, length, color, brightness):
        #print(start, length, color, brightness)
        direction = abs(start)/start
        if (brightness < 0):
            return
        newstart = start    
        if (start < 0):
            newstart = abs(start) - abs(length) + 2
            if (length < 0):
                newstart = newstart - (10 + length)
            else:
                length += 3
            #steps = int(brightness/abs(length-1) * direction)
        if (start > 0):
            if (length < 0):
                newstart = newstart + (10 + length)
            else:
                newstart -= 3
                length += 3
            #steps = int(brightness/abs(length-1) * direction)
            #brightness = brightness - (abs(steps) * abs(length -1))
        for i in range( newstart , newstart + abs(length) - 1):
            #print(i)
            self.led[i] = [color[0] & brightness , color[1] & brightness , color[2] & brightness ]
            #brightness += steps

    def draw_second(self):
        self.draw_hand(self.pose[self.second], self.len_second, self.color_second) 
    def draw_minute(self):
        self.draw_hand(self.pose[self.minute], self.len_minute, self.color_minute) 
    def draw_hour(self):
        self.draw_hand(self.pose[self.hour], self.len_hour, self.color_hour) 

    def clear(self):
        for i in range(0,self.numleds):
            self.led[i] = (0,0,0)
        self.led.write()

    def update(self, second=0, minute=0, hour=0):
        self.second = second
        self.minute = minute
        self.hour = hour

#    def display(self, sb=self.brightness, mb=self.brightness, hb=self.brightness):
    def spin(self, delay=0, b=10):
        for h in range(0,12):
            for m in range(0,12):
                self.display(m,h,b,b,b)
                time.sleep_ms(delay)
                
    def display(self, dm, dh, sb=5, mb=5, hb=5):
        for i in range(0,self.numleds):
            self.led[i] = [0,0,0]
        self.draw_hand(self.pose[self.second], self.len_second, self.color_second, sb)
        self.draw_hand(self.pose[dm], self.len_minute, self.color_minute, mb) 
        
        t = dh + 1
        if t > 11:
            t = 0

        if int(hb * (1 - (dm / 11))) > 0:
            self.draw_hand(self.pose[dh], self.len_hour, self.color_hour, int(hb * (1 - (dm / 11)))) 
        
        if int(hb *  (dm /11)) > 0:
            self.draw_hand(self.pose[t], self.len_hour, self.color_hour, int(hb *  (dm /11))) 

        self.led[104] = [0,3 * int(mb / (abs(self.len_minute) - 1)) ,0]
        self.led.write()

