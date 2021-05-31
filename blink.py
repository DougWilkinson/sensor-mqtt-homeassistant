import time

def blink(statusled, ledon=False):
    ledbefore = statusled.value()
    statusled.value(ledon)
    time.sleep_ms(80)
    statusled.value(not ledon)
    time.sleep_ms(150)
    statusled.value(ledon)
    time.sleep_ms(80)
    statusled.value(not ledon)
    statusled.value(ledbefore)

