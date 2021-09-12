# mqttclass.py
import sys
import time
import json
import secrets
from machine import reset
from umqtt.simple import MQTTClient
positives = {'YES','ON','TRUE','OPEN'}
negatives = {'NO','OFF','FALSE','CLOSED'}

def version():
    return "3" # Fix publish for general values only publishes changed sensor, not all

class MQTT:

    def __init__(self, nodename="testnode", sensorlist=None):
    
        self.nodename = nodename
        self.basetopic = secrets.mqttbasetopic

        self.sensorlist = sensorlist
        self.lastretry = time.time()
        #self.statusled = Pin(2,Pin.OUT)
        self.initfound = False

        self.client = MQTTClient(self.nodename, secrets.mqttserver, user=secrets.mqttuser, password=secrets.mqttpass)
        self.client.set_callback(self.Callback)

        self.Connect()

    def Callback(self, topic, msg):
        #print(topic, msg)
        if self.initfound and "/init" in topic:
            return
        if "/init" in topic:
            self.initfound = True
        try:
            jdata = json.loads(msg)
            #print("jdata: ", jdata)
            # loop through received keys and find sensors to update
            if "reset" in jdata:
                print("MQTT Reset")
                time.sleep(5)
                reset()
                while True:
                    pass
            for (key,value) in jdata.items():
                for sensor in self.sensorlist:
                    if sensor.subtopic is not None and key in sensor.publish:
                        dvalue = value
                        if type(sensor.value) is int:
                            dvalue = int(value)
                        if type(sensor.value) is float:
                            dvalue = float(value)
                        if value.upper() in positives:
                            dvalue = True
                        if value.upper() in negatives:
                            dvalue = False
                        # Update publish and value
                        sensor.publish[key] = dvalue
                        sensor.triggered = True
                        if len(sensor.publish) == 1:
                            sensor.setvalue(dvalue)
        except:
            print("Error handling received MQTT data:")
            print(topic, msg)

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
                if sensor.subtopic is not None:
                    #print(sensor.subtopic)
                    if sensor.subtopic[0] == '/':
                        self.client.subscribe(self.basetopic + sensor.subtopic.split('/')[1])
                    else:
                        self.client.subscribe(self.basetopic + self.nodename + "/" + sensor.subtopic) 
       
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
        publist = {}  # list of unique topics to publish list of lists
        basepub = {}  # default publish items
        tosave = {}
        resetlist = []
        pubneeded = False
        for s in self.sensorlist:
            sensorpub = {}  # build this dict to add to publist
            if s.pubtopic is not None:
                for (key,value) in s.publish.items():
                    if s.pubtopic == "":
                        basepub[key] = value
                        if s.pubneeded:
                            pubneeded = True
                            resetlist.append(s)
                    else:
                        if s.pubneeded:
                            pubneeded = True
                            resetlist.append(s)
                            sensorpub[key] = value
                if s.save:
                    for (key,value) in s.publish.items():
                        tosave[key] = value
            if len(sensorpub) > 0:
                #print(sensorpub)
                publist[self.basetopic + self.nodename + "/" + s.pubtopic] = sensorpub
        if len(basepub) > 0 and pubneeded:
            #print(basepub)
            self.client.publish(self.basetopic+self.nodename, json.dumps(basepub))
        if len(publist) > 0 and pubneeded:
            for (key,value) in publist.items():
                #print(key,value)
                self.client.publish(key, json.dumps(value))        
        if len(tosave) > 0:
            #print("Publishing saves to /init :", tosave)
            self.client.publish(self.basetopic+self.nodename+"/init", json.dumps(tosave), True)
        # Reset pubneeded last, done only if all publishes successful
        for s in resetlist:
            s.pubneeded = False

