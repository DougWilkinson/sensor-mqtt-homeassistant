# hassmqtt.py
import sys
import time
import json
from machine import reset
from umqtt.simple import MQTTClient

try:
    from secrets import mqttuser, mqttpass, mqttserver, customtopic, hasstopic
except:
    # What to do?
    pass

positives = {'YES','ON','TRUE','OPEN'}
negatives = {'NO','OFF','FALSE','CLOSED'}

def version():
    return "3" 
    # 3: remove "class" for Hass and flatten. 
    # finish un-selfify and add template support for autodiscovery to work for each class

devicelist = {}

def connect(self, nodename="test", sensorlist=None):

    # define a new list of name: hass objects
    hass objects contain the following:
    hassmqtt.config[nodename] = nodename
    # "testhass/"
    try:
        self.customtopic = secrets.customtopic
    except:
        self.customtopic = "command"
    config['topic'] = secrets.hasstopic
    self.sensorlist = sensorlist
    self.lastretry = time.time()
    #self.statusled = Pin(2,Pin.OUT)
    self.initfound = False
    self.mqttreconnects = 0

    self.client = MQTTClient(self.nodename, secrets.mqttserver, user=secrets.mqttuser, password=secrets.mqttpass)
    self.client.set_callback(self.Callback)

    self.Connect()

def Callback(self, topic, msg):
    #print(topic, msg)
    try:
        if "reset" in msg:
            print("MQTT Reset")
            time.sleep(5)
            reset()
            while True:
                pass
        for key in self.sensorlist:
            if key in topic:
                sensor = self.sensorlist[key]
                dvalue = msg
                if sensor.type is int:
                    dvalue = int(msg)
                if sensor.type is float:
                    dvalue = float(msg)
                if sensor.type is str:
                    dvalue = msg.decode()
                if sensor.type is bool:
                    if msg.upper() in positives:
                        dvalue = True
                    if msg.upper() in negatives:
                        dvalue = False
                # Update publish and value
                sensor.set(dvalue)
                sensor.triggered = True
                if "/init" in topic:
                    sensor.initvalseen = True
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
        self.sensorlist['mqttreconnects'].set(self.sensorlist['mqttreconnects'].value + 1)
        for sensor, object in self.sensorlist.items():
            #print(sensor.subtopic)
            base = "{}/{}/{}/{}".format(self.hasstopic,object.mqttclass,self.nodename, sensor)
            if object.mqttclass == "switch":
                self.client.publish(base + "/config", 
                                    '{{ "name": "{}", "cmd_t": "{}", "stat_t": "{}" }}'.format(
                                    self.nodename + "_" + sensor, base + "/set", base + "/state" ))
            else:
                self.client.publish(base + "/config", 
                                    '{{ "name": "{}", "stat_t": "{}" }}'.format(
                                    self.nodename + "_" + sensor, base + "/state" ))

            self.client.subscribe(base + "/set" )
            self.client.subscribe(base + "/init" )
        self.client.subscribe(self.customtopic + "/set" )
    
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
    
    for sensor, object in self.sensorlist.items():
        if object.pubneeded:
            base = "{}/{}/{}/{}".format(self.hasstopic, object.mqttclass, 
                                        self.nodename, sensor)
            self.client.publish(base + "/state", str(object.value))
            if object.persist:
                self.client.publish(base + "/init", str(object.value))
            object.pubneeded = False


