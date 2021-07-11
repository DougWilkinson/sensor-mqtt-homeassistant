import config
import dht
from machine import PWM,ADC,Pin,Timer,reset,reset_cause
from math import trunc
import time
import network
import json
from gc import mem_free

def version():
    return "3"

class Sensor:

    list = []
    clock = time.time
    Callmemfree = mem_free
    statechange = False
    lastminute = 0
    lasthour = 0
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

    def UPTIME(self, devnull=None):
        self.setvalue(Sensor.clock() - uptime.diff)

    def MEMFREE(self, devnull=None):
        global memfree
        newmemfree = Sensor.Callmemfree()
        if (memfree.value - newmemfree) > memfree.diff:
            memfree.setvalue(newmemfree)

    def RSSI(self, devnull=None):
        global wifi
        t = Sensor.wlan.status('rssi')
        if t < 0:
            wifi.values.pop()
            wifi.values.insert(0,t)
            avg = int(sum(wifi.values)/len(wifi.values))
            if abs(avg - wifi.value) > wifi.diff:
                wifi.setvalue(avg)

    def OUT(self, newstate=False):
        self.setstate(newstate)

    def IN(self, devnull=None):
        newdifftime = time.ticks_diff(time.ticks_ms(), self.lasttime)
        if newdifftime > self.diff:
            self.difftime = newdifftime
        self.lasttime = time.ticks_ms()
        if self.state and self.pin.value() == 0:
            self.setstate(False)
        if not self.state and self.pin.value() == 1:
            self.setstate(True)

    def VS(self, newvalue=0):
        if type(newvalue) is bool:
            self.setstate(newvalue)
        else:
            self.setvalue(newvalue)

    def setstate(self, newstate=False):
        self.state = newstate
        self.setvalue(self.onname if self.state else self.offname)
        if self.mode == "OUT":
            self.pin.value(newstate)

    def setvalue(self, newvalue=0):
        self.value = newvalue
        self.publish = [[self.name , self.value]]
        self.pubneeded = True
        self.triggered = True
        if self.mode == "PWM":
            self.pin.duty(newvalue)

    def DHT(self, devnull):
        self.publish = [[self.name + "temp", 0] , [self.name + "humidity", 0] ]
        try:
            self.pin.measure()
            newtemp = (self.pin.temperature() * 9 / 5) + 32
            dtemp = abs(self.temp - newtemp)
            dhum = abs(self.humidity - self.pin.humidity())
            self.humidity = self.pin.humidity()
            self.temp = newtemp
            self.publish = [[self.name + "temp", self.temp] , [self.name + "humidity", self.humidity] ]
            if (dtemp > .2) or (dhum > 2):
                self.triggered = True
        except OSError as e:
            print("DHT read error: " + str(e))

    def ADC(self, devnull):
        new = round(self.pin.read() * self.k,3)
        if new < 0:
            new = 0
        if abs(self.value - new) > self.diff:
            self.setvalue(new)
    
    def PWM(self, newvalue=0):
        self.setvalue(newvalue) 

    def AMP(self, devnull=None, setinitval=False):
        new = round(self.read_register(0x04) * self.k,3)
        if new < 0:
            new = 0
        if setinitval or abs(self.value - new) > self.diff:
            self.setvalue(new)

    def write_register(self, register, register_value):
        register_bytes = bytearray([(register_value >> 8) & 0xFF, register_value & 0xFF])
        self.pin.writeto_mem(self.address, register, register_bytes)

    def read_register(self, register):
        register_bytes = self.pin.readfrom_mem(self.address, register, 2)
        register_value = int.from_bytes(register_bytes, 'big')
        if register_value > 32767:
            register_value -= 65536
        return register_value

    def __init__(self, name, mode="VS", pin=-1, poll=None, diff=0, onname="ON", offname="OFF", callback=None, initval=None, save=False, topic=None): 
        
        #print("Setup for: " + name + " as " + mode)
        
        modesetup = {"RSSI":self.RSSI, "UPTIME":self.UPTIME, "MEMFREE":self.MEMFREE, "IN":self.IN, "INP":self.IN, "ADC":self.ADC, "VS":self.VS, "DHT":self.DHT, "OUT":self.OUT, "PWM":self.PWM, "AMP":self.AMP, "MQTT":None } 
        
        self.name = name               # mqtt name of value to publish
        self.state = False
        self.onname = onname
        self.offname = offname
        self.k = 1.0
        self.diff = diff
        self.mode = mode
        self.setvalue(initval)
        self.values = [initval]*10
        self.save = save
        self.poll = poll
        self.callback = callback if (callback is not None) else modesetup.get(mode)
        self.pin = pin
        self.topic = topic
        
        self.pubneeded = True
        self.triggered = False 

        if self.mode == "AMP":
            self.address = 0x40
            self.write_register(0x05, 16793)
            self.write_register(0, 2463)
            self.k = 0.0000214292
            self.AMP(None, setinitval=True)
            print("Setup INA219, Value: ", self.value)
        
        if self.mode.find("IN") >= 0:
            self.pin = Pin(pin, Pin.IN)
            if self.mode == "INP":
                self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
            self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.IN) 
            self.lasttime = time.ticks_ms()
            self.difftime = 0
            #Fix to set publish values even if no change in state
            self.setstate(False)
            self.IN(None)

        if self.mode == "DHT":
            self.pin = dht.DHT22(Pin(pin))
            self.temp = 0.0
            self.humidity = 0.0
            self.DHT("Setup")
 
        if self.mode == "PWM":     
            self.pin = PWM(Pin(pin))
            self.setvalue(0)
            #self.PWM(None)
        
        if self.mode == "OUT":     
            self.pin = Pin(pin, Pin.OUT)
            self.OUT(False)
        
        if self.mode == "VS":     
            self.VS(self.value)

        if self.mode == "ADC":     
            self.pin = ADC(0)
            self.k = 0.003028
            self.setvalue(0)
            self.ADC("Setup")
 
        if self.poll is not None:
            self.timer = Timer(-1)
            if callback is None:
                self.timer.init(period=self.poll, mode=Timer.PERIODIC, callback=modesetup.get(self.mode))
                #print("Using callback: ",self.mode)
            else:
                self.timer.init(period=self.poll, mode=Timer.PERIODIC, callback=self.callback)
                #print("Using callback: ",self.callback)

        print("{} Sensor {} - setup complete ...".format(self.mode,self.name))
        Sensor.list.append(self)

uptime = Sensor("uptime", "UPTIME", poll=60000, diff=time.time(), initval=0)
wifi = Sensor("rssi", "RSSI", poll=60000, diff=2, initval=-65)
memfree = Sensor("memfree", "MEMFREE", poll=60000, diff=500, initval=mem_free())
heartbeat = Sensor("hb", "MQTT", initval={}, topic="/heartbeat")
init = Sensor("init", "MQTT", initval={}, topic="init")
set = Sensor("set", "MQTT", initval={}, topic="set")
wifi.pubneeded = True

