import dht
from machine import PWM,ADC,Pin,Timer,reset,reset_cause
import time
from blink import blink
import json
from umqtt.simple import MQTTClient
import network
from gc import mem_free
from publish import publish

class Sensor:

    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    clock = time.time
    lastblink = time.time()
    CallBlink = blink
    Callmemfree = mem_free
    Callpublish = publish
    mqttclient = MQTTClient
    name = ""
    basetopic = ""
    usingmqtt = False
    mqttconnected = False
    publishing = False
    lastmqttretry = time.time() - 15 
    
    list = []
    statechange = False
    lastheartbeat = time.time()
    lastminute = 0
    lasthour = 0
    ledonval = True
    statusled = Pin(2,Pin.OUT)
    initfound = False

    def mqtt_callback(topic, msg):
        #print(topic, msg)
        if Sensor.initfound and "/init" in topic:
            return
        if not Sensor.initfound:
            Sensor.initfound = True
        try:
            jdata = json.loads(msg)
            #print("jdata: ", jdata)
            if "heartbeat" in jdata:
                Sensor.lastheartbeat = time.time()
                Sensor.lastminute = int(jdata["Minute"])
                Sensor.lasthour = int(jdata["Hour"])
                #print("hearbeat set: ", time.time())
                return
            if "reset" in jdata:
                print("MQTT Reset")
                time.sleep(1)
                reset()
            for s in Sensor.list:
                if s.name in jdata:
                    val = jdata[s.name]
                    if type(0) == type(s.value):
                        s.setvalue(int(val))
                        continue
                    if type(0.0) == type(s.value):
                        s.setvalue(float(val))
                        continue
                    if val == "ON" or val == "on":
                        s.setstate(True)
                        continue
                    if val == "OFF" or val == "off":
                        s.setstate(False)
                        continue
                    s.setvalue(jdata[s.name])
        except:
            pass

    def MQTTConnect():
        if time.time() - Sensor.lastmqttretry > 10:
            Sensor.lastmqttretry = time.time()
            try:
                Sensor.mqttclient.connect(clean_session=True)
                Sensor.mqttclient.subscribe(Sensor.basetopic+"heartbeat")
                Sensor.mqttclient.subscribe(Sensor.basetopic+Sensor.name+"/init")
                Sensor.mqttclient.subscribe(Sensor.basetopic+Sensor.name+"/set")
                #print("Connected to MQTT topics /heartbeat /init /set")
                Sensor.lastheartbeat = time.time()
                return True
            except:
                #print("MQTTConnect failed ...")
                return False

    def MQTTSetup(name="test", basetopic="basetopicname/", server="192.168.x.x", mqttuser="xxxxxx", mqttpass="xxxxxx"):
        Sensor.basetopic = basetopic
        Sensor.name = name
        Sensor.usingmqtt = True
        Sensor.mqttclient = MQTTClient(name, server, user=mqttuser, password=mqttpass)
        Sensor.mqttclient.set_callback(Sensor.mqtt_callback)

    def Spin():
        if time.time() - Sensor.lastblink > 8:
            Sensor.CallBlink(Sensor.statusled, Sensor.ledonval)
            Sensor.lastblink = time.time()

        if not Sensor.mqttconnected:
            Sensor.mqttconnected = Sensor.MQTTConnect()

        try:
            if Sensor.mqttconnected:
                Sensor.mqttclient.check_msg()
                Sensor.Callpublish(Sensor.mqttclient, Sensor.basetopic, Sensor.name, Sensor.list)
        except:
            #print("Error in checkmsg or publish, will reconnect ...")
            Sensor.mqttconnected = False
        
        if time.time() - Sensor.lastheartbeat > 200:
            #print("Hearbeat lost after 200 seconds, will reconnect ...")
            Sensor.mqttconnected = False


    def UPTIME(self):
        global uptime
        uptime.setvalue(Sensor.clock() - uptime.diff)

    def MEMFREE(self):
        global memfree
        newmemfree = Sensor.Callmemfree()
        if (memfree.value - newmemfree) > memfree.diff:
            memfree.setvalue(newmemfree)

    def RSSI(self):
        global wifi
        t = Sensor.wlan.status('rssi')
        if t < 0:
            wifi.values.pop()
            wifi.values.insert(0,t)
            sum = 0
            for i in wifi.values:
                sum = sum + i
            avg = int(sum / 3)
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
        newvalue = self.pin.read()
        #self.publish = [[self.name , self.value]]
        if abs(self.value - newvalue) > self.diff:
            self.setvalue(newvalue)
    
    def PWM(self, newvalue=0):
       self.setvalue(newvalue) 

    def __init__(self, name, mode="VS", pin=-1, poll=None, diff=0, onname="ON", offname="OFF", callback=None, initval=None, save=False): 
        
        #print("Setup for: " + name + " as " + mode)
        
        modesetup = {"IN":self.IN, "INP":self.IN, "ADC":self.ADC, "VS":self.VS, "DHT":self.DHT, "OUT":self.OUT, "PWM":self.PWM } 
        
        self.name = name               # mqtt name of value to publish
        self.state = False
        self.onname = onname
        self.offname = offname
        self.diff = diff
        self.value = initval
        self.values = [initval, initval, initval]
        self.save = save
        self.mode = mode
        self.poll = poll
        self.callback = callback if (callback is not None) else modesetup.get(mode)
        self.pin = pin
        
        self.pubneeded = True
        self.triggered = False 
        
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
            print(self.mode, " GPIO ", pin, " setup complete ...")

        if self.mode == "DHT":
            self.pin = dht.DHT22(Pin(pin))
            self.temp = 0.0
            self.humidity = 0.0
            self.DHT("Setup")
            print("DHT GPIO ", pin, " setup completed")

        if self.mode == "PWM":     
            self.pin = PWM(Pin(pin))
            self.setvalue(0)
            #self.PWM(None)
            print("PWM GPIO ", pin, " setup complete ...")
        
        if self.mode == "OUT":     
            self.pin = Pin(pin, Pin.OUT)
            self.OUT(False)
            print("OUT GPIO ", pin, " setup complete ...")
        
        if self.mode == "VS":     
            self.VS(self.value)
            print("VS ",self.name, " setup complete ... ")
        
        if self.mode == "ADC":     
            self.pin = ADC(0)
            self.setvalue(0)
            self.ADC("Setup")
            print("ADC setup complete ...")

        if self.poll is not None:
            self.timer = Timer(-1)
            if callback is None:
                self.timer.init(period=self.poll, mode=Timer.PERIODIC, callback=modesetup.get(self.mode))
                #print("Using callback: ",self.mode)
            else:
                self.timer.init(period=self.poll, mode=Timer.PERIODIC, callback=self.callback)
                #print("Using callback: ",self.callback)
        
        Sensor.list.append(self)

ap = network.WLAN(network.AP_IF)
ap.active(False)
uptime = Sensor("uptime", poll=60000, callback=Sensor.UPTIME, diff=time.time(), initval=0)
wifi = Sensor("rssi", poll=60000, callback=Sensor.RSSI, diff=2, initval=-65)
memfree = Sensor("memfree", poll=60000, callback=Sensor.MEMFREE, diff=500, initval=mem_free())
wifi.pubneeded = True
