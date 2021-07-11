Added support for Over the air updates to sensorclass related .py files
This does not update firmware for micropython.

Requirements:
- http server that can host files to be updated (I use Homeassistant)
- wifi capable microcontrollers like ESP8266/ESP32

You could adapt these scripts to run any code, you do not need the sensorclass or mqttclass files to use these.

Approach:

Using the MAC address of the microcontroller, query a web server (preset in a bootloader) to find the files for that node.
The web server has a file for each device that lists the files and versions that it needs.
Need to swap out a bad microcontroller? Just update the file with the new MAC address and run the bootloader to re-synch the needed files.

<Add files and workflow around how this works>
 
