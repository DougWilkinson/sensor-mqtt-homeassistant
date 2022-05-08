# main.py

import config

version = { 'version': "20", 
            'changes' : "streamlined" }

# Increment reboot counter
config.set('reboots', config.get('reboots') + 1 ) 

# run updater if flag set and not on alternate config(2)
if config.get('update') == 1 and config.get('update_result') == 0:
    print("Starting updater ...")
    updater = config.importer('updater')
    updater.update()
    config.reboot()

# Start loading sensors if good config
if config.nodename != '' and config.get('update') != 3:
    print("Loading sensors: ", config.nodename,"\n")
    for f in config.current.keys():
        print("{}:{}".format(f,config.current[f]))
    config.importer(config.nodename)
    config.reboot()

# Failed to load primary and alternate
print("Unrecoverable error ...")
