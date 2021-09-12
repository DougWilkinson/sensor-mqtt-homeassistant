from machine import Pin,Timer,ADC,reset_cause
import time
import config
import network
from gc import mem_free
import dht

def version():
    return "1" 
    # 1 Added persist() method and flags initvalseen/persist for MQTT

class Sensor:
    import network
    wlan = network.WLAN(network.STA_IF)
    # items that need to be provided outside of Sensor, like to mqtt
    classes = {'sensor', 'binary_sensor', 'light', 'switch', }
    mqttlist = {}
        
    class MQTT:
        def __init__(self, name, mqttclass, initval, diff=0, minval=None, maxval=None):
            if name in Sensor.mqttlist:
                print("Name {} exists, must be unique!".format(name))
                return
            vtype = type(initval)
            print("Init MQTT Sensor: {} , type: {}".format(name,vtype))

            self.name = name
            self.type = vtype
            self.mqttclass = mqttclass
            self.pubneeded = True
            self.persist = False
            self.initvalseen = False
            self.triggered = False
            self.value = initval
            self.diff = diff
            self.minval = minval
            self.maxval = maxval
            Sensor.mqttlist[name] = self

        def persist(value=True):
            self.persist = value

        def set(self, newval):
            changed = False

            if self.type is int or self.type is float:
                if self.maxval is not None and newval > self.maxval:
                    newval = self.maxval
                if self.minval is not None and newval < self.minval:
                    newval = self.minval
                if abs(newval - self.value) >= self.diff:
                    self.value = newval
                    changed = True

            if self.type is bool and newval != self.value:
                self.value = not self.value
                changed = True

            if self.type is str:
                self.value = newval
                changed = True

            if changed:
                self.pubneeded = True

    class vSensor:

        def __init__(self, name, initval, diff=0, minval=None, maxval=None, 
                    polling=None, callback=None):

            # vSensor only has one value, so call it 'mqtt'
            self.value = initval
            self.mqtt = Sensor.MQTT(name, 'sensor', initval, diff, minval, maxval) 
            self.timer = Timer(-1)
            self.timer.init(period=100, mode=Timer.PERIODIC, callback=self.update) 

        def update(self, null=None):
            self.value = self.mqtt.value

        # Convenience for setting new value, mqtt class handles actual value/publishing
        def set(self, newvalue):
            self.mqtt.set(newvalue)
            self.update()

    class InSensor:

        def __init__(self, name, pin, pullup=False):
            # pullup: True=YES
            # pin: gpio#, period: None or ms
            if pullup:
                self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
            else:
                self.pin = Pin(pin, Pin.IN)
            self.mqtt = Sensor.MQTT(name, 'binary_sensor', False) 
            self.set()
            self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.set) 

        def set(self, devnull=None):
            self.lasttime = time.ticks_ms()
            self.value = self.pin.value() > 0
            self.mqtt.set(self.value)

    class Switch:

        def __init__(self, name, pin, initval=False):
            # pin: gpio#, period: None or ms
            self.value = initval
            self.pin = Pin(pin, Pin.OUT)
            self.pin.value(initval)
            self.mqtt = Sensor.MQTT(name, 'switch', initval) 
            self.timer = Timer(-1)
            self.timer.init(period=100, mode=Timer.PERIODIC, callback=self.update) 

        def update(self, null=None):
            self.value = self.mqtt.value
            self.pin.value(self.value)

        def set(self, newvalue):
            self.mqtt.set(newvalue)
            self.update()
            self.pin.value(newvalue)

    class ADC:

        def __init__(self, name, pin=0, k=0.003028, diff=0.05, polling=5000):
            self.pin = ADC(pin)
            self.k = k
            self.mqtt = Sensor.MQTT(name, 'sensor', 0.0) 
            self.timer = Timer(-1)
            self.timer.init(period=polling, mode=Timer.PERIODIC, callback=self.set) 

        def set(self, devnull=None):
            self.mqtt.set(self.pin.read() * self.k)
            self.value = self.mqtt.value

    class DHT22:

        def __init__(self, name, pin=0, diff=0.05, polling=5000):
            self.pin = dht.DHT22(Pin(pin))
            self.temp = Sensor.MQTT(name + "_" + "temp", 'sensor', 0.0, diff=1, minval=-50, maxval=130) 
            self.humidity = Sensor.MQTT(name + "_" + "humidity", 'sensor', 0.0, diff=1, minval=0, maxval=100)
            self.set()            
            self.timer = Timer(-1)
            self.timer.init(period=polling, mode=Timer.PERIODIC, callback=self.set) 

        def set(self, devnull=None):
            try:
                self.pin.measure()
                self.temp.set((self.pin.temperature() * 9 / 5) + 32)
                self.humidity.set(self.pin.humidity())
            except OSError as e:
                print("DHT read error: " + str(e))

    class INA219:

        def write_register(self, register, register_value):
            register_bytes = bytearray([(register_value >> 8) & 0xFF, register_value & 0xFF])
            self.pin.writeto_mem(self.address, register, register_bytes)

        def read_register(self, register):
            register_bytes = self.pin.readfrom_mem(self.address, register, 2)
            register_value = int.from_bytes(register_bytes, 'big')
            if register_value > 32767:
                register_value -= 65536
            return register_value
        
        def __init__(self, name, pin, k=0.0000214292, diff=0.05, polling=5000):
            self.pin = pin
            self.address = 0x40
            self.write_register(0x05, 16793)
            self.write_register(0, 2463)
            self.k = k
            self.mqtt = Sensor.MQTT(name, 'sensor', 0.0, diff=diff, minval=0) 
            self.timer = Timer(-1)
            self.timer.init(period=polling, mode=Timer.PERIODIC, callback=self.set) 

        def set(self, devnull=None):
           self.mqtt.set(round(self.read_register(0x04) * self.k,3))
           self.value = self.mqtt.value
 
    class vDict:

        def __init__(self, items, polling=5000, callback=None):
            self.mqtt = {}
            self.callback = callback
            for key,value in items.items():
                self.mqtt[key] = Sensor.MQTT(key, 'sensor', value) 
            self.timer = Timer(-1)
            self.timer.init(period=polling, mode=Timer.PERIODIC, callback=self.set) 

        def set(self, devnull=None):
            for name, object in self.mqtt.items():
                if object.triggered and self.callback is not None:
                    self.callback(name, object.value)
                object.triggered = False

# Internal sensor definitions

# Bootflags from config
flagdict = {}
for name in config.flagnames:
    flagdict[name] = config.boot_flags[config.flagnames.index(name)]
bootflags = Sensor.vDict(flagdict, polling=1000, callback=config.set)

# Misc. system stats values
statslist = { "resetcause": 0, "uptime": 0, "rssi": 0, "memfree": 0 }
mqtt = {} 
start_time = time.time()

for key,value in statslist.items():
    mqtt[key] = Sensor.MQTT(key,'sensor', value)

def getstats(null=None):
    mqtt['uptime'].set(time.time() - start_time)
    mqtt['resetcause'].set(reset_cause())
    mqtt['rssi'].set(Sensor.wlan.status('rssi'))
    mqtt['memfree'].set(mem_free())

timer = Timer(-1)
timer.init(period=10000, mode=Timer.PERIODIC, callback=getstats)

print("All Sensors initialized ...")
