# led.py
from machine import Pin
from neopixel import NeoPixel
import time


def version():
    return "0"
    # 0: First version

class WS2812:
    
    def __init__(self, ledpin, numleds, fg = (0,0,0)):
        self.ledpin = Pin(ledpin, Pin.OUT)
        self.numleds = numleds
        self.fg = fg
        self.update = False
        self.mode = "light"
        #flashing
        self.flash_toggle = False
        self.speed = 500
        self.last = time.ticks_ms()
        #cylon
        self.direction = 1
        self.current = 0

        self.leds = NeoPixel(self.ledpin, self.numleds)
        self.clear()

    def spin(self):

        if self.update and self.mode == 'light':
            self.leds.fill(self.fg)
            self.leds.write()
            self.update = False                

        if time.ticks_diff(time.ticks_ms(), self.last) > self.speed:
            self.last = time.ticks_ms()

            if self.mode == 'flash':
                self.flash_toggle = not self.flash_toggle
                if self.flash_toggle:
                    self.leds.fill(self.fg)
                else:
                    self.leds.fill((0,0,0))
                self.leds.write()

            if self.mode == 'cylon':
                self.current += self.direction
                if self.current > self.numleds -1:
                    self.direction = -1
                    self.current = self.numleds - 2
                if self.current < 0:
                    self.direction = 1
                    self.current = 1
                self.leds[self.current] = self.fg
                decay = self.current - self.direction
                while decay >= 0 and decay < self.numleds:
                    x = self.leds[decay] 
                    self.leds[decay] = (x[0]>>1,x[1]>>1,x[2]>>1)
                    decay -= self.direction
                self.leds.write()

    def clear(self):
        self.leds.fill((0,0,0))
        self.leds.write()

    def set_color(self, color=(0,0,0)):
        self.fg = color
        self.update = True

    def flash(self, speed_ms=500):
        if speed_ms == 0:
            self.mode = 'light'
            self.update = True
            return
        self.flash_toggle = False
        self.mode = 'flash'
        self.speed = speed_ms

    def cylon(self, speed_ms=500):
        self.clear()
        if speed_ms == 0:
            self.mode = 'light'
            self.update = True
            return
        self.mode = 'cylon'
        self.direction = 1
        self.current = 0
        self.speed = speed_ms
