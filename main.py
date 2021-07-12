# main.py

import config

def version():
    return "2"

# Increment reboot counter
config.set('reboots', config.get('reboots') + 1 ) 

# Update flag set - run updater
if config.get('update'):
    print("Starting updater")
    config.importer('updater')

# Start Sensor if good config is found (could be primary or alternate)
if (config.primary or config.alternate):
    print("Starting Sensor: ", config.name,"\n")
    for f in config.current.keys():
        print("{}:{}".format(f,config.current[f]))
    config.importer(config.name)

# Last ditch effort, no configs, run original updater
import updater