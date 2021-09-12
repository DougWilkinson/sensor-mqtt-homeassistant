# qatest.py

# Run through testing scenarios

#   1. update main nodefile
#       - update with good file
#       - update with bad file
#   2. multiple reboot when not updating
#   3. multiple reboot on alt config
#   4. recovery mode?
#   5. test local mode (no network)

import config

sensor = config.importer('sensor')
hass_mod = config.importer('hassmqtt','HassMqtt')
HassMqtt = hass_mod.HassMqtt

def version():
    return "0"
    # 0: New

hass = HassMqtt(config.nodename,sensor)

def main():
    
    # Put bad syntax here
    print("Before loop and m/h set to -1")
    m = -1
    h = -1
    while True:
        hass.Spin()
        if hass.minute.value >= 0:
            if hass.minute.value != m:
                h = hass.hour.value
                m = hass.minute.value
                print("{} : {}".format(h,m))

main()
