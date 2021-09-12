import config
import dht
from machine import PWM,ADC,Pin,Timer,reset,reset_cause
import time
import network
from gc import mem_free

def version():
    return "8"  # Add versions to published info (not started)

class Sensor:

    list = []
    statechange = False
    lastblink = time.time()
    statusled = Pin(2,Pin.OUT)
    wlan = network.WLAN(network.STA_IF)

    def blink():
        led = Sensor.statusled.value()
        Sensor.statusled.value(not led)
        time.sleep_ms(80)
        Sensor.statusled.value(led)
        time.sleep_ms(150)
        Sensor.statusled.value(not led)
        time.sleep_ms(80)
        Sensor.statusled.value(led)

    def SYS(self, devnull=None):
        self.publish["resetcause"] = reset_cause()
        self.publish["uptime"] = time.time() - self.starttime
        self.publish["rssi"] = Sensor.wlan.status('rssi')
        self.publish["memfree"] = mem_free()
        self.pubneeded = True

    # flags "update","update_failed","server_failed","reboots"
    def BOOTFLAG(self, flag=None, value=None):
        if not self.triggered:
            return
        for flag in config.flagnames:
            if config.boot_flags[config.flagnames.index(flag)] != self.publish[flag]:
                config.set(flag,self.publish[flag])
        self.pubneeded = True
        self.triggered = False

    def OUT(self, newstate=False):
        self.setvalue(newstate)

    def INP(self, devnull=None):
        Sensor.IN(self,devnull)

    def IN(self, devnull=None):
        newdifftime = time.ticks_diff(time.ticks_ms(), self.lasttime)
        if newdifftime > self.diff:
            self.difftime = newdifftime
        self.lasttime = time.ticks_ms()
        if self.state and self.pin.value() == 0:
            self.setvalue(False)
        if not self.state and self.pin.value() == 1:
            self.setvalue(True)

    # deprecated
    def setstate(self, newstate=None):
        Sensor.setvalue(newstate)

    def setvalue(self, newvalue=None, low=None, high=None):
        if newvalue is None:
            print("SensorError: setvalue called with None")
            return

        changed = False        
        if type(newvalue) is bool:
            self.state = newvalue
            self.value = self.onname if self.state else self.offname
            if self.mode == "OUT":
                self.pin.value(self.state)
            changed = True

        if self.diff is not None:
            newvalue = newvalue * self.k
            if low is not None and newvalue < low:
                newvalue = low
            if high is not None and newvalue > high:
                newvalue = high
            try:
                if abs(self.value - newvalue) > self.diff:
                    self.value = newvalue
                    changed = True
            except:
                self.value = newvalue
                changed = True

        if changed:
            if self.mode == "PWM":
                self.pin.duty(newvalue)
            self.publish = {self.name : self.value}
            self.pubneeded = True
            self.triggered = True
        
    def DHT(self, devnull):
        # Does not use setvalue
        self.publish = {}
        self.pubneeded = False
        try:
            self.pin.measure()
            newtemp = (self.pin.temperature() * 9 / 5) + 32
            self.temp = newtemp
            self.humidity = self.pin.humidity()
            self.publish = {self.name + "temp": self.temp, self.name + "humidity": self.humidity}
            self.pubneeded = True
            self.triggered = True
        except OSError as e:
            print("DHT read error: " + str(e))

    def ADC(self, devnull):
        self.setvalue(self.pin.read())
    
    def AMP(self, devnull=None):
        self.setvalue(round(self.read_register(0x04),3))

    def write_register(self, register, register_value):
        register_bytes = bytearray([(register_value >> 8) & 0xFF, register_value & 0xFF])
        self.pin.writeto_mem(self.address, register, register_bytes)

    def read_register(self, register):
        register_bytes = self.pin.readfrom_mem(self.address, register, 2)
        register_value = int.from_bytes(register_bytes, 'big')
        if register_value > 32767:
            register_value -= 65536
        return register_value

    def __init__(self, name, mode="VS", pin=-1, initval=None, poll=None, 
                diff=None, onname="ON", offname="OFF", callback=None, 
                k=1, min=None, max=None, initstate=None, save=False, 
                pubtopic="", subtopic="/set"):
        
        if initstate is not None:
            initval = initstate
        self.name = name
        self.onname = onname
        self.offname = offname
        self.k = k
        self.mode = mode
        self.save = save
        self.pin = pin
        self.pubtopic = pubtopic
        self.subtopic = subtopic
        self.pubneeded = True
        self.triggered = False 
        self.state = initstate
        self.diff = diff

        if (type(initval) is int or type(initval) is float):
            self.values = [initval]*10
            self.min = min
            self.max = max
            if diff is None:
                self.diff = 0

        if initval is not None:
            self.setvalue(initval)

        if self.mode == "SYS":
            self.publish = {}
            self.starttime = time.time()
            self.SYS(None)
            self.callback = self.SYS

        if self.mode == "BOOTFLAG":
            self.publish = {}
            for flag in config.flagnames:
                self.publish[flag] = config.boot_flags[config.flagnames.index(flag)]
            self.value = initval
            self.callback = self.BOOTFLAG

        if self.mode == "AMP":
            self.address = 0x40
            self.write_register(0x05, 16793)
            self.write_register(0, 2463)
            self.k = 0.0000214292
            self.AMP(None)
            self.callback = self.AMP

        if self.mode.find("IN") >= 0:
            self.pin = Pin(pin, Pin.IN)
            if self.mode == "INP":
                self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
            self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.IN) 
            self.lasttime = time.ticks_ms()
            self.difftime = 0
            self.IN(None)

        if self.mode == "DHT":
            self.pin = dht.DHT22(Pin(pin))
            self.DHT("Setup")
            self.callback = self.DHT

        if self.mode == "PWM":     
            self.pin = PWM(Pin(pin))
            self.setvalue(0)
        
        if self.mode == "OUT":     
            self.pin = Pin(pin, Pin.OUT)
            if type(initval) is bool:
                self.OUT(initval)
            else:
                self.OUT(False)

        if self.mode == "ADC":     
            self.pin = ADC(0)
            self.k = 0.003028
            self.setvalue(0)
            self.ADC("Setup")
            self.callback = self.ADC

        if poll is not None:
            self.timer = Timer(-1)
            if self.callback is None:
                print("Error Callback not specified for polling Sensor ...")
            else:
                self.timer.init(period=poll, mode=Timer.PERIODIC, callback=self.callback)
                print("Polling {} Sensor with period {} ms ...".format(self.mode,poll))

        print("{} Sensor {} - setup complete ...".format(self.mode,self.name))
        Sensor.list.append(self)

Sensor("system", "SYS", initval=0, poll=10000, subtopic=None, pubtopic="system")
Sensor("bootflags", "BOOTFLAG", initval=0, poll=10000, pubtopic="bootflags")

# Subscribe to hearbeat
Sensor("heartbeat", initval=False, pubtopic=None, subtopic="/heartbeat")
Sensor.Hour = Sensor("Hour", initval=0, pubtopic=None)
Sensor.Minute = Sensor("Minute", initval=0, pubtopic=None)

Sensor("init", initval=0, pubtopic=None, subtopic="init")
Sensor("set", initval=0, pubtopic=None, subtopic="set")

 
