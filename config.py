# config.py

import network
import ubinascii
import ujson
import machine
import time

def version():
    return "0"

def reboot():
    machine.reset()
    while True:
        pass

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("Connecting to Wifi ...")

while not wlan.isconnected():
    time.sleep(1)
    print(".",end='')
print(" Connected!\n")


rtc = machine.RTC()
names = ["magic","update","update_failed","server_failed","reboots"]
empty_flags = [42,0,0,0,0]
boot_flags = []

def write(flags=boot_flags):
    rtc.memory(bytes(flags))
    print("Flags saved: ",flags)

def set(flag, value=1):
    boot_flags[names.index(flag)] = value
    write()

def clear(flag):
    set(flag, value=0)

def get(flag):
    return boot_flags[names.index(flag)]

# If power on, write initial flags (reboots = 0)
if rtc.memory() == b'':
    write(empty_flags)

for flag in rtc.memory():
    #print(flag)
    boot_flags.append(flag)

# if not valid flags, write empty
if boot_flags[0] != 42:
    write(empty_flags)

espMAC = str(ubinascii.hexlify(network.WLAN().config('mac')).decode())
primary = False
alternate = False
current = {}

try:
    f = open(espMAC)
    current = ujson.load(f)
    f.close()
    name = current["name"]
    primary = True
except:
    print("Primary config corrupt or missing ...")

if not primary or (primary and get('reboots') > 4):
    primary = False
    try:
        f = open(espMAC+".alt")
        current = ujson.load(f)
        f.close()
        name = current["name"]
        alternate = True
    except:
        print("alternate config corrupt or missing ...")

def importer(module, use_version=True):
    try:
        if module in current and use_version:
            return __import__(module + current[module])
        else:
            return __import__(module)
    except:
        print("Error importing {} ...".format(module))
        print(current)
        reboot()

def from_importer(module, submodule, use_version=True):
    try:
        if module in current and use_version:
            return __import__(module + current[module], submodule)
        else:
            return __import__(module,submodule)
    except:
        print("Error importing {} from {} ...".format(submodule,module))
        print(current)
        reboot()

