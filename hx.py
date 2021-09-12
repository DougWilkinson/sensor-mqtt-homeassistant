# hx.py
import time
from machine import Pin,Timer

def version():
    return "2"
    # 2: combined value into polling 

@micropython.native
def toggle(p):
    p.value(1)
    p.value(0)

class HX711:
    def __init__(self, pd_sck=4, dout=5, gain=128, sf=229, min=-10000, max=10000, diff=5):
        self.gain = gain
        self.SCALING_FACTOR = sf
        self.dataPin = Pin(dout, Pin.IN)
        self.pdsckPin = Pin(pd_sck, Pin.OUT, value=0)
        self.powerUp()
        self.diff = diff
        self.min = min
        self.max = max
        self.value = self.raw_read()
        if self.value <= self.min:
            self.value = self.min
        if self.value >= self.max:
            self.value = self.max
        self.values = [self.value]*5
        self.triggered = False
        self.start()

    def powerUp(self):
        self.pdsckPin.value(0)
        self.powered = True

    def isready(self):
        time.sleep(.001)
        return self.dataPin.value()

    def raw_read(self):
        while not self.isready():
            pass
        time.sleep_us(10)
        my = 0
        for idx in range(24):
            toggle(self.pdsckPin)
            data = self.dataPin.value()
            if not idx:
                neg = data
            else:
                my = ( my << 1) | data
        toggle(self.pdsckPin)
        if neg: my = my - (1<<23)
        return round(my/self.SCALING_FACTOR, 1)

    def poll(self, timer):
        newhx = self.raw_read()
        if newhx == 0:
            return
        if newhx >= self.min and newhx <= self.max:
            self.values.pop()
            self.values.insert(0,newhx)
        top = self.values.copy()
        top.sort()
        top.pop()
        top.reverse()
        top.pop()
        if abs(self.value - sum(top)/len(top)) > self.diff:
            self.value = sum(top)/len(top)
            self.triggered = True

    def start(self, polling=500):
        self.timer = Timer(-1)
        self.timer.init(period=polling, mode=Timer.PERIODIC, callback=self.poll)
    
    def stop(self):
        try:
            self.timer.deinit()
        except:
            print("polling not started or error ...")