# main.py

import config

def version():
    return "7"

# Increment reboot counter
config.set('reboots', config.get('reboots') + 1 ) 

# run updater if flag set
if config.get('update'):
    print("Starting updater")
    config.importer('updater')

# Start Sensor if good config is found (could be primary or alternate)
if (config.primary or config.alternate):
    print("Starting Sensor: ", config.nodename,"\n")
    for f in config.current.keys():
        print("{}:{}".format(f,config.current[f]))
    config.importer(config.nodename)

# Last ditch effort, no configs, run original updater
import updater