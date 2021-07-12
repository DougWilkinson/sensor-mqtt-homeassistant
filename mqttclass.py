# mqttclass.py
import time
import json
import secrets
from machine import reset
from umqtt.simple import MQTTClient

def version():
    return "3"

class MQTT:

    def __init__(self, name="testnode", sensorlist=None):
    
        self.name = name
        self.basetopic = secrets.mqttbasetopic

        self.sensorlist = sensorlist
        self.lastretry = time.time() 
        self.lastheartbeat = time.time()
        self.lastminute = 0
        self.lasthour = 0
        
        self.ledonval = True
        #self.statusled = Pin(2,Pin.OUT)
        self.initfound = False

        self.client = MQTTClient(self.name, secrets.mqttserver, user=secrets.mqttuser, password=secrets.mqttpass)
        self.client.set_callback(self.Callback)

        self.Connect()

    def Callback(self, topic, msg):
        #print(topic, msg)
        if self.initfound and "/init" in topic:
            return
        if not self.initfound:
            self.initfound = True
        try:
            jdata = json.loads(msg)
            #print("jdata: ", jdata)
            if "heartbeat" in jdata:
                self.lastheartbeat = time.time()
                self.lastminute = int(jdata["Minute"])
                self.lasthour = int(jdata["Hour"])
                #print("hearbeat set: ", time.time())
                return
            if "reset" in jdata:
                print("MQTT Reset")
                time.sleep(1)
                reset()
            for s in self.sensorlist:
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

    def Connect(self):
        self.lastmqttretry = time.time()
        try:
            self.client.connect(clean_session=True)
            print("Connected to MQTT ")
            self.connected = True
        except:
            print("MQTTConnect failed ...")
            self.connected = False

        if self.connected:
            for sensor in self.sensorlist:
                if sensor.topic is not None:
                    #print(sensor.topic)
                    if sensor.topic[0] == '/':
                        self.client.subscribe(self.basetopic + sensor.topic.split('/')[1])
                    else:
                        self.client.subscribe(self.basetopic + self.name + "/" + sensor.topic) 
       
    def Spin(self):
        if self.connected:
            try:
                self.client.check_msg()
                self.Publish()
            except KeyboardInterrupt:
                print("Ctrl-C detected")
                sys.exit()
            except:
                print("Error in checkmsg or publish, will reconnect ...")
                self.connected = False
        
        if not self.connected and time.time() - self.lastmqttretry > 10:
            print("Attempting to reconnect ...")
            self.Connect()
        
    def Publish(self):
        topublish = {}
        tosave = {}
        resetlist = []
        savechanged = False
        pubneeded = False
        for s in self.sensorlist:
            if s.mode != "MQTT":
                #print(s.name)
                if s.pubneeded:
                    pubneeded = True
                    resetlist.append(s)
                    #s.pubneeded = False
                for p in s.publish:
                    topublish[p[0]] = p[1]
                if s.save:
                    for p in s.publish:
                        tosave[p[0]] = p[1]
                if s.save and s.pubneeded:
                    savechanged = True
        if topublish != {} and pubneeded:
            #print(json.dumps(topublish))
            self.client.publish(self.basetopic+self.name, json.dumps(topublish))
        if tosave != {} and savechanged:
            #print(json.dumps(tosave))
            self.client.publish(self.basetopic+self.name+"/init", json.dumps(tosave), True)
        for s in resetlist:
            s.pubneeded = False

