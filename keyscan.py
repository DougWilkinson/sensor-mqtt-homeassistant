# keyscan.py

import machine
import mcp23017
import time

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
mcp = mcp23017.MCP23017(i2c)

row = range(1,8)
col = range(9,16)


for x in range(0,16):
    mcp.pin(x,mode=1, pullup=1 )

def scan():
    for x in range(0,16):
        a = mcp.pin(x,mode=0, value=0 )
        time.sleep_us(100)
        for y in range(0,16):
            if x != y:
                if not mcp.pin(y):
                    print("{},{} shorted".format(x,y))
        a = mcp.pin(x,mode=1, pullup=1)
        #print("checking row {}".format(x))


    