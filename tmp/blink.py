import time

def blink(statusled, ledon=False):
    ledon = statusled.value()
    statusled.value(not ledon)
    time.sleep_ms(80)
    statusled.value(ledon)
    time.sleep_ms(150)
    statusled.value(not ledon)
    time.sleep_ms(80)
    statusled.value(ledon)

