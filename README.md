# Why this?
This project was the result of an evolution through home automation and sensors. The ESP8266 has fascinated me from the beginning and started with Arduino/mqtt and is now focused on micropython/mqtt for communication with Homeassistant.

The driver for micropython was to learn python, not because it's better in some way. It has significant limitations on code size and speed, but for the majority of my sensors and controllers, it is more than adequate.

## Overview

The interaction between the sensor device and Homeassistant is shown below and described in more detail following that. This readme is only an overview. More detailed documentation is needed but unless anyone actually asks for it, I do not plan to do much more here.

!(./hass-mqtt-sensor-overview.jpg)

The latest iteration of code includes a means to automatically update .py files via a web server using http requests. No authentication or code verification is being done here and on the esp8266 platform, probably never will be. It's added overhead that I can't afford to keep code size small.

## Components (uController)

### bootloader

The bootloader is a stripped down version of the httpclient code and includes some basic setup to allow for the initial pull of files from the webserver. Using rshell and a script, you can take a new ESP8266 nodemcu, flash it and reinstall files with a single command (assuming the web server has the config file ready)

### main
Primary purpose is to decide whether to run the "updater" code or start the node. This is done based on RTC values (set before reboot) or the state of the configuration

### secrets
This file contains what you would expect and is imported by "config". MQTT server/creds and topics. Wifi name/password is never re-entered and only setup during bootloader run. TODO: item might be to add wifi name/pwd change support.

```
# secrets.py

def version():
    return "vv"

mqttuser = "username"
mqttpass = "pwd"
mqttserver = "192.168.x.x"
custom_topics = ("global/set","global/heartbeat")
hasstopic = "homeassistant"
code_url = "http://nn.nn.nn.nn:80/local/code/"
```

### config
Config contains some core functions to maintain the RTC flags and import other modules based on version #. Versioning is done by appending a version number to the name of each .py file (ie. name0.py or name20.py). As new versions are updated on the web server, they are copied by the updater script and then loaded according to the \<macaddr\> or \<macaddr\>.alt file that is saved on the uController. 

### \macaddr\> (aka node config file)
Two files stored (in json format) the names and versions for the node to use. The primary is named simply as the MacAddress of the node. The secondary is the same but with .alt appended. During an update, the primary is moved to .alt and the new primary created based on what was downloaded from the server.

If an update fails, the secondary is loaded (which should just restart the node with the old versions).

The node name itself is stored in this file, which is used to start the nodenameNN.py accordingly. See the format of this file below in the web components section.

### RTC values
The RTC memory was used to maintain some state across restarts, as it was necessary to kick off an update from the network, reboot and then start the update due to memory constraints (can't import updater/httpclient at the same time as all the node files)

These values are documented in more detail below.

### nodenameNN.py (node script)
Each node has a unique main script that loads everything else (mostly). The general format is shown below: 

```
import sensors,hassmqtt,mymodules

# define sensors
sensors.Switch(xxx)
sensors.Light(xxx)

#instantiate HassMqtt to connect to MQTT
hass = HassMqtt(xxx)

# main looping
def main():
    while True:
        hass.Spin()
        # your non-blocking code here

main()

```
    
Technically, the node script should never end. If it does, the config.importer() will reboot the controller.

### sensors
This module loads all other sensors as needed (based on what is in the node config file). It was originally one big file that became impossible to import. Each sensor class is now a separate file with some grouping if it makes sense (like gpiobase). This also helps save memory for sensors that need more user space memory.

Currently defined:

- **gpiobase** - includes Analog (ADC), Input (GPIO input) and Switch (GPIO output)
- **Value** - Any type of value: int, float, str, bool, tuple
- **Light** - Homeassistant light device (requires led.py or equiv.)
- **dht** - support for dht11 or dht22 temp/humidity
- **Ina219** - I2C based Current sensor
- **bootloader** - Access to RTC values
- **Stats** - systems stats (wifi signal, mem_free and uptime)

sensors is the basis for creating sensors in your nodenameNN.py. They must be created before instantiating the HassMqtt Class. This is because HassMqtt uses the list of sensors to connect to MQTT, subscribe and publish. It is theoretically possible to add to the list and force a "reconnect", but not tested and could result in churn on the Homeassistant side.

The only bundled sensors are the bootloader and system stats (which are optional if memory is a concern). To update remotely, you have to instantiate the "bootloader" sensor in your node script. The system stats are really optional.

### mqttdevice
This module handles the Class for mqtt related information for each sensor defined in "sensors". A list (dictionary) is created that is used for handling subscribing, publishing and updating.

### hassmqtt
This module maintains communication to the MQTT server, updating sensors when incoming messages arrive and publishing updates as things change on sensors (either timer based or interrupt).

**Connect()** - initial setup of sensors based on the "list" of sensors. This also does auto-configuration through Homeassistant's discovery for mqtt sensors and subscribes to topics as needed. This is done automatically when you instantiate HassMqtt and is not called directly.

**Publish()** - As sensors indicate they have changed, messages related to state are published so that Homeassistant can see them. This is called via the Spin() method below and not directly.

**Spin()** - This is a maintainer method that has to be in a looping regular call in your "main()" function. If this is not called regularly, MQTT will timeout and cause reconnects or lost data.

### updater
This is the module that maintains the files in flash according to the node config file it downloads from the web server. I use Homeassistant's web server since it's already there and FTP files to it as needed.

When an update RTC flag is set, it downloads two files from the web server: \<macaddr\>.config and latestversions. Between these two files, it builds a dictionary of files, compares it to the current config and downloads anything new, building a new node config file (\<macaddr\>) described above. If any errors occur during an update, the node config file is not touched and RTC flags are set so that once restarted, you can see the results in Homeassistant.

## Web Server Components
The only file needed to configure a node is the one named using the MacAddress. This can reference all the files needed. To make updating core files easier, use the "latestversions" to set global versions for files (see example below)

### \<macaddr\>.config
The node config file is json formatted with the node name and files it should use. It looks like this:

```
{
    "nodename":"mysensor"
    "mysensor":"5",
    "sensors":"latest"
}
```

In the example above, the node is named "mysensor" which is what you will see in Homeassistant and there are two files it will use, one is the main user node script named "mysensor". Updater will expect to find "mysensor5.py" on the web server by appending the version to the name and adding ".py". The "sensors" file shown above uses "latest" which will look in the "latestversions" file (see below) for the version to use. By using "latest" for most of the files, you can update the latestversions and push an update out to all your sensors (Yay!).

### latestversions
This file is also json formatted and is a list of more file names and versions that are used to replace "latest" in the node config file. One important note is the use of "!" as "config" does in the example below.

```
{
    "config":"!5",
    "updater":"11"
    ...
}
```

Here, config is at version "5" but config is a special script that is loaded using the stock "import" and not "config.importer()" (Why!?! because how could it load itself?). The "!" exclamation tells updater to copy config5.py from the web server and save it as "config.py" on the uController. 

### Use "!" CAREFULLY - There is no undo...

I use this only for files that need it or for some basic utilities that rarely need updating.
