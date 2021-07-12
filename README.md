Sensorclass

Added support for Over the air updates to sensorclass related .py files. This was inspired by this OTA updater here:
https://github.com/rdehuyss/micropython-ota-updater

I wanted a local only option for updating my sensors, so using the httpclient to pull files from a local web server seemed simple enough.

Requirements:
- http server that can host files to be updated (I use Homeassistant)
- wifi capable microcontrollers like ESP8266/ESP32
- httpclient module from ota-updater repository (above mention)
- a bootloader.py module that does an initial "push"

You could adapt these scripts to update any set of micropython modules. main.py, config.py and updater.py stand on their own.

Approach:

Using the MAC address of the microcontroller, pull a unique file from the web server (also named as the MAC address) that defines the files to update for that device. This file contains versions for each file which can be specific versions or "latest".

You must include the "name" key.
The values (versions) are treated as strings and only compared to see if they are different before updating.

Files stored on the web server:
<deadbeef1234> - desired list of modules with version info
latestversions - list of all "latest" with versions
config.py
main.py
updater.py


deadbeef1234 (the MAC address of a device):

json file containing a list of files and versions this node should have.

contents:
        {
            "name": "smartcharger",
            "smartcharger": "1",
            "sensorclass": "2",
            "testmain": "latest",
            "mqttclass": "latest"
            "updater": "latest"
            "config": "6"
        }

config.py (no version control):

- Loads bootflags from RTC memory
- Loads primary config if exists (config.primary = True)
- Loads alternate config if no primary (config.alternate = True)
- used to set bootflags (see below)
- Only looks at local information (does not talk to web server)
- contains "importer" to import correct versions of your files

You should import this in your own programs to access information about the configuration files or bootflags.

main.py (runs from boot.py - no version control)

imports config
Decides whether to run updater.py
Runs the module referenced as "name" in the config file

updater.py (runs from main.py, can update self):

Contacts the web server, downloads desired config for the node based on MAC address (eg. deadbeef1234). Attempts to update files listed for this node, only downloading the ones with different versions from what it sees in "current" configuration.

Any errors will keep the primary configuration intact.
If all is updated without error, it will copy primary to alternate and save the new config to primary for the next restart.

Things you would use in your own programs to decide when to update and how:

bootflags (RTC memory):

These are stored in RTC memory and only exist if power is on the ESP8266/ESP32. Used as a simple communication channel across reboots.

"update" - set if update requested
"update_failed" - if update failed
"reboots" - counts how many times "main.py" is loaded
"server_failed" - set if updater can't reach web server

Trigger update on some event:

In the case of the sensorclass, an update could be triggered by an MQTT event. The program would then use the config.set() function to signal an update:

import config
...
your code...
...
if "update triggered":
    config.set('update')
    machine.reset()

It doesn't hurt to call the update periodically to check for new versions, if nothing is new, the node will just restart.

Then once your code restarts, check for the failed flag.

import config
...
your code...
...
if config.get('update_failed'):
    call_fast_blink()


Suggestions:

Reboots counter > 4 will force alternate config on startup
To avoid this, you should reset this counter somewhere in your code that makes sense, like if you force a normal restart to do an update or other reason. This is done to catch errors importing corrupt/bad files. If it repeatedly fails to load, it will revert back to the original files.

You might also check if you are running on the alternate config and take some action to notify that a problem exists. In the case of Sensorclass, an MQTT message will trigger a notification, but it could be a webhook call or some other method.




<Add files and workflow around how this works>
 
