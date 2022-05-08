# hx.py
import time
from machine import Pin,Timer
import config

def version():
    return "4"
    # 4: Major update to make a real sensor and combine attributes(Breaking changes) 

@micropython.native
def toggle(p):
    p.value(1)
    p.value(0)

Device = config.Device

class HX711:
    def __init__(self, name="scale", statename="state", pd_sck=4, dout=5, min=-10000, 
                max=10000, lowhx=0, diff=5, poll=1):
        self.gain = 128
        self.SCALING_FACTOR = 229
        self.dataPin = Pin(dout, Pin.IN)
        self.pdsckPin = Pin(pd_sck, Pin.OUT, value=0)
        self.powerUp()
        # "scale" that also does the polling
        self.hx = Device(name, "sensor", initval=self.raw_read(), diff=diff,
                    minval=min, maxval=max, units="hx", poll=poll, 
                    poller=self.update)
        # "low" or "good" threshold
        self.lowhx = Device("lowhx", 'sensor', lowhx)
        # min change to update
        self.diffhx = Device("diffhx", 'sensor', diff)
        self.values = [self.hx.value]*5
        self.state = Device(statename, 'sensor', self.getstate())

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

    def update(self):
        newhx = self.raw_read()
        if newhx == 0:
            return
        if newhx >= self.hx.minval and newhx <= self.hx.maxval:
            self.values.pop()
            self.values.insert(0,newhx)
        top = self.values.copy()
        top.sort()
        top.pop()
        top.reverse()
        top.pop()
        if abs(self.hx.value - sum(top)/len(top)) > self.diffhx.value:
            self.hx.set(sum(top)/len(top))
            self.state.set(self.getstate())
    
    def getstate(self):
        if self.hx.value < self.lowhx.value:
            return "low"
        else:
            return "good"
