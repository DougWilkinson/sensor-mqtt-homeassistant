# light homeassistant topic info

"""        
l = LedLight(0,16)
l.fg = (60,0,20)
l.flash()
while True:
    l.spin()
"""

#light config string
"""
'{"stat_t": "hass/lt/state", 
"name": "mylightname", 
"cmd_t": "hass/lt/set", 
"brightness_command_topic": "hass/ltb/set", 
"brightness_state_topic": "hass/ltb/state", 
"rgb_state_topic": "hass/ltrgb/state", 
"rgb_command_topic": "hass/ltrgb/set"}'

set values from HASS
hass/lt/set ON
hass/lt/set ON
hass/ltrgb/set 0,0,255
hass/lt/set ON
hass/ltrgb/set 255,0,0
hass/lt/set ON
hass/ltb/set 145
hass/lt/set ON

published values to HASS:
mosquitto_pub -u -t "hass/ltrgb/state" -m "0,0,0"
mosquitto_pub -u -t "hass/ltrgb/state" -m "255,0,0"
mosquitto_pub -u -t "hass/ltrgb/state" -m "255,0,255"
mosquitto_pub -u -t "hass/ltb/state" -m "200"

"""