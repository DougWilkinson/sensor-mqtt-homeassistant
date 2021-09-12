# stepclass.py

from machine import Pin,PWM,Timer
import time

def version():
    return "2"
    # 2: changed how limit switches work and added home trigger -1

class Stepper:

    def __init__(self, dir_pin=15, step_pin=13, enable_pin=12, 
                open_limit_pin=5, close_limit_pin=14, 
                encoder_pin=None, inverted=False, 
                pullups=False, period=1250, timeout=900, 
                maxsteps=4000, backoff=400):
        
        # period 1250 for 8BY stepper,??? for NEMA?
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.step_pin = Pin(step_pin, Pin.OUT)
        self.enable_pin = Pin(enable_pin, Pin.OUT)
        self.enable_pin.value(1)

        self.encoder = True if encoder_pin is not None else False

        if self.encoder:
            if pullups:
                self.encoder_pin = Pin(encoder_pin, Pin.IN, Pin.PULL_UP)
            else:
                self.encoder_pin = Pin(encoder_pin, Pin.IN)
            self.encoder_state = self.encoder_pin.value()
            self.timeout = timeout

        if not self.encoder:
            if pullups:
                self.open_limit_pin = Pin(open_limit_pin, Pin.IN, Pin.PULL_UP)
                self.close_limit_pin = Pin(close_limit_pin, Pin.IN, Pin.PULL_UP)
            else:
                self.open_limit_pin = Pin(open_limit_pin, Pin.IN)
                self.close_limit_pin = Pin(close_limit_pin, Pin.IN)

        self.inverted = inverted

        # Timing for stepper for smooth operation (tested)
        self.delay = period
    
        #position_known = True if we are confident ucpos is true
        self.position_known = False
        
        # Current percent open and stepper step tracking, max steps to 100% open
        self.steps = -1
        self.maxsteps = maxsteps
        self.backoff = backoff

    def check_pin(self, pin):
            if self.inverted:
                return not pin.value()
            else:
                return pin.value()

    def limit(self):
        if self.encoder:
            if self.encoder_state != self.encoder_pin.value():
                self.last_encoder_change = time.ticks_ms()
                self.encoder_state = self.encoder_pin.value()
                print("R",end='')
                return False
            if time.ticks_ms() - self.last_encoder_change > self.timeout:
                return True
            else:
                return False
        else:
            return self.check_pin(self.open_limit_pin) or self.check_pin(self.close_limit_pin)

    def onestep(self):
        self.step_pin.value(1)
        pass
        self.step_pin.value(0)
    
    def open(self, newpercent=100):

        if newpercent < 0:
            if not self.home():
                return "Home-Failed"
            else:
                return "closed"

        newsteps = int(self.maxsteps * newpercent / 100)

        # Reset steps to first open setting (from mqtt?)
        if self.steps < 0:
            self.steps = newsteps
            self.position_known = True
        
        if newsteps != self.steps:
        
            if not self.position_known:
                if not self.home():
                    return "home-failed"
            
            if newsteps > self.steps:
                step = 1
                self.dir_pin.value(1)
            else:
                step = -1
                self.dir_pin.value(0)

            self.enable_pin.value(0)

            self.last_encoder_change = time.ticks_ms()
            while (self.steps != newsteps) and not self.limit():
                self.onestep()
                self.steps += step
                time.sleep_us(self.delay)
            
            self.enable_pin.value(1)
            
            if newsteps > self.steps:
                self.position_known = False
                return "limit-open"

            if newsteps < self.steps:
                self.position_known = False
                return "limit-closed"
            
        if self.steps == 0:
            return "closed"
        else:
            return "open"

    def home(self):
        self.position_known = False
        self.dir_pin.value(0)

        # Set over-limit to +10% of max + backoff
        self.steps=int((self.maxsteps + self.backoff) * 1.1)

        self.enable_pin.value(0)

        self.last_encoder_change = time.ticks_ms()
        while self.steps > 0 and not self.limit():
            self.onestep()
            self.steps -= 1
            time.sleep_us(self.delay)

        self.enable_pin.value(1)

        # Never hit home
        if self.steps <= 0:
            self.position_known = False
            return False
        
        # Hit home, reset steps and back off limit switch
        self.steps = 0
        self.dir_pin.value(1)

        self.enable_pin.value(0)

        for i in range(self.backoff):
            self.onestep()
            self.steps += 1
            time.sleep_us(self.delay)

        self.enable_pin.value(1)
        self.steps = 0

        self.position_known = True
        return True
