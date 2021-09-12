# config.py

import network
import ubinascii
import ujson
import machine
import time
import os,sys

def version():
    return "20"
    # 20: logging for failed importer  - READ IN DEBUG FILE w/ limited size?
    # Want to limit problems loading config, how to only read a few lines?

ap = network.WLAN(network.AP_IF)
ap.active(False)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
ssid = wlan.config('essid')
espMAC = str(ubinascii.hexlify(network.WLAN().config('mac')).decode())

rtc = machine.RTC()
flagnames = ["checksum","magic","update","update_result","config","network","reboots"]
boot_flags = []

current = {}

try:
    import secrets
except KeyboardInterrupt:
    print("c_secrets: Ctrl-C detected")
    raise
except:
    print("Secrets not found!")
    raise

def reboot(msg=None, graceful=False):
    if graceful:
        clear('reboots')
    for i in range(10):
        print(i)
        time.sleep(1)
                 
    machine.reset()
    while True:
        pass

def bootflag_check():
    bf = []
    for flag in rtc.memory():
        bf.append(flag)
    if len(bf) > 1 and sum(bf[1:]) % 255 == bf[0]:
        return bf
    else:
        return [42,42,0,0,0,0,0]

def set(flag, value=1):
    if flag in flagnames:
        boot_flags[flagnames.index(flag)] = value
        boot_flags[0] = sum(boot_flags[1:]) & 255
        rtc.memory(bytes(boot_flags))
        print("Flags saved: ",boot_flags)

def clear(flag):
    if flag in flagnames:
        set(flag, value=0)

def get(flag):
    if flag in flagnames:
        return boot_flags[flagnames.index(flag)]

def read_config(name):
    try:
        f = open(name)
        current = ujson.load(f)
        f.close()
        return current
    except:
        return {}

def importer(module, use_version=True):
    try:
        if module in current and use_version:
            return __import__(module + current[module])
        else:
            return __import__(module)
    except KeyboardInterrupt:
        print("importer: Ctrl-C detected")
        raise
    except Exception as ImportError:
        f=open('debug','w')
        os.dupterm(f)
        sys.print_exception(ImportError)
        os.dupterm(None)
        f.close()
        reboot()

##############
# Confirm bootflag status from RTC

boot_flags = bootflag_check()

# Determine which config to load:

if get('update') and get('update_result') and get('reboots') > 1:
    print("\nExcessive reboots with update flags set ...")
    set('config',2)

if get('config') <= 1:
    print('\nUsing primary')
    current = read_config(espMAC)

if get('config') == 2:
    print('\nUsing alternate')
    current = read_config(espMAC + '.alt')

print("\n",flagnames)
print(boot_flags)

# Find nodename in one of the configs

print("\nCurrent:",current)

if 'nodename' in current:
    nodename = current['nodename']
else:
    nodename = ''

print("\nNodename: ",nodename, "\n")

timeout = time.time()
while not wlan.isconnected() and time.time() - timeout < 20:
    time.sleep(1)
    print(".",end='')

if wlan.isconnected():
    print(" connected to: {} \n".format(ssid))
    set('network')
else:
    clear('network')
    print(" failed to connect to: ",ssid)

