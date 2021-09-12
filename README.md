# hass.py


# TODO: copy hassmqtt to esp (ftp done)
# add http base to secrets
# need a simple copy from http in config (if http imported?) 

# TODO working on updater.py

# Some info on newly flashed settings for wifi
# Newly flashed settings:
# wlan.config('essid') = '' 
# wlan.status() == 255
# wlan.connect()
# wlan.status() == 0
# wlan.connect('jugglers',pwd)
# wlan.isconnected() = True
# wlan.status() = 5
# wlan.config('essid') = 'jugglers'








list = {}

class Device:
    def __init__(self, name, etc):
        # variables:
        name
        value
        type of value (bool, int, float, etc)
        class (hass class)
        getter (callback to use with timer or interrupt to update this devices value(s))
        setter (callback to use with timer to update other things)
        add to list
        return self
    
    def set(self, value)
    
    def get(self)

def gpio_read()

def gpio(name,pin):
    #hardware
    device = hass.Device(name,)

def getvalue(name):
    return mqttlist[name]





    @property
    def name():
        return self.name

    def dict_numbers(self, args):
        # dictionary list of numbers

    def gpio_output(args):
        # HASS - switch

    def number(args):
        # generic number

    def gpio_input(arge):
        # HASS motion sensor, etc

    def dht_input():
        # temp/humidity

    def ina219_input():
        # AMP current meter

    def pwm_output():

    def neopixel_light():

Usage:

import hass

kitchen = hass.Mqtt()  # creates a class of sensors
# creates a class? default sensors - returns a dict of names and objects

sensors.InSensor(name, pin, protocol=usensor.mqtt, class=sensor)

#usensor format/design


class MqttSensors:
    list = {} # master list for MQTT types

    def __init__(args)
    values for MQTT related communication

def somesensor(name, class):
    new = MQTT(kwargs)
    new.blah initialize


sensors.Switch(name, pin#, ... )
sensors.Number(name, initval=0 (int), proto ... class=number)
sensors.Dht()
sensors.Ina219()
usensor.

# sensorclass

Sensor("name","MQTT", initval=[])

Sensor - internal preset

Sensor - basic MQTT single value

Sensor - MQTT dict of values

    How to update values when mqtt receives a "set"

Sensor - polling vs. non polling

Sensor - custom callback? (to set values)
        hx711 does this today

# pubtopic - publish topics
# base/name/sys - system values (built in)
# base/name/boot - bootflags (built in)
# If not specified:
# base/name - default publish to basetopic + name
# If "None" specified:
# Sensor values are not published (internal variables?)

# subtopic - subscribe topics
# base/name/set - used for updating all Sensor values (default)
# base/name/init - used to save settings if save flag set (default)
# base/heartbeat - Contains hour and minute
# base/name/boot - set bootflags (built in)
# base/name/<subtopic>

# sample topic and message from callback
# b'dougha/heartbeat' b'{"heartbeat": "ON", "Hour": "19", "Minute": "16"}'
# b'dougha/smartcharger/set' b'{"test":"4"}'



