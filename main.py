import time
from machine import Pin,reset

try:
    #buzz = Pin(16, Pin.OUT)
    #buzz.value(0)
    pin = Pin(2, Pin.OUT)
    for i in range(5):
        pin.value(0)
        time.sleep_ms(500)
        pin.value(1)
        time.sleep_ms(500)
    import node
    node.main()
except KeyboardInterrupt:
    pin.value(1)
    print("Control-C detected")
except Exception as e:
    pin.value(1)
    print("node.py import error, trying node1.py ...")
    print(e)
    for i in range(10):
        pin.value(0)
        time.sleep_ms(150)
        pin.value(1)
        time.sleep_ms(150)
    try:
        import node1
        node1.main()
    except Exception as e:
        print(e)
        print("Unrecoverable error ... Resetting in 30 seconds ")
        print("machine.reset in 30 secs")
        time.sleep(30)
        reset()

