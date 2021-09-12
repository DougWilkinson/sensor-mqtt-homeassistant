# ledmatrix
from machine import Pin
from neopixel import NeoPixel
import time
import random

ledpin = Pin(14, Pin.OUT)
numled = 8 * 32


class LedMatrix:
    
    fg = (0,1,1)
    bg = (0,0,0)
    sb = [(0,0,0)]*48
    lcs = [32,32,32,32,32]
    trans = "random"
    tptr = -1
    tmsg = "hello world!"
    tlast = time.ticks_ms()
    tmax = 0

    def __init__(self, fontbitmap, ledmap, width):
        self.width = width
        self.maxdigits = int(32/width)
        self.font = fontbitmap
        self.map = ledmap
        self.led = NeoPixel(ledpin, numled)
        self.clear()

    def clear(self):
        for i in range(numled):
            self.led[i] = self.bg 
        self.led.write()
        self.lcs = [32,32,32,32,32]

    def text(self,msg):
        self.tmsg = msg + '     '
        self.tptr = 0
        self.tlast = time.ticks_ms()
        self.tmax = 0

    def uptext(self):
        t = time.ticks_ms() - self.tlast
        if t > self.tmax:
            self.tmax = t
        self.tlast = time.ticks_ms()
        if self.tptr < len(self.tmsg):
            self.display(self.sb, ord(self.tmsg[self.tptr]), refresh=False)
            for s in range(2,-1,-1):
                for t in range(numled - 16):
                    self.led[255-t] = self.led[239-t]
                for t in range(16):
                    self.led[t] = self.sb[t+(16*s)]
                self.led.write()
            self.tptr += 1
            return False
        else:
            return True
    
    def show(self,newnum=32, digit=0, speed=50, notrans=False):
        if notrans:
            self.display(self.led, ordnum=newnum, digit=digit, displayrow=1)
            return

        if self.trans == "scroll":
            r=1
            for i in range(8):
                self.display(self.led, ordnum=newnum,digit=digit, digitrow=7-r, displayrow=0, refresh=False)
                if i < 7:
                    self.display(self.led, ordnum=self.lcs[digit],digit=digit, displayrow=r+1)
                time.sleep_ms(speed)
                r += 1
                if r > 7:
                    r=0
            self.display(self.led, ordnum=newnum, digit=digit, displayrow=1)

        if self.trans == "random":
            if newnum != 32:
                for d in range(5):
                    self.display(self.led, ordnum=48+random.getrandbits(8) % 9,digit=digit)
                    time.sleep_ms(speed)
            self.display(self.led, ordnum=newnum,digit=digit)
  
    def display(self, dled, ordnum=32, digit=0, displayrow=1, digitrow=0, refresh=True ):
        #displayrow can be negative
        columns = self.width
        achar = self.font[ordnum]
        for x in range(columns):
            for y in range(digitrow, 8-displayrow):
                if ( achar[x] & 1 << y):
                    dled[(digit*8*columns) + self.map[y + displayrow - digitrow + (x*8)]] = self.fg
                if not ( achar[x] & 1 << y):
                    dled[(digit*8*columns) + self.map[y + displayrow - digitrow + (x*8)]] = self.bg
        if refresh:
            dled.write()
            self.lcs[digit] = ordnum

