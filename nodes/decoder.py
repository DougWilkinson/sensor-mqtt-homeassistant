# decoder.py
from machine import Pin
from machine import PWM
from machine import Timer
import time

class motor:

    def __init__(self, position=0, state="Closed", dirpin=15, steppin=13, enablepin=12, beltpin=14, pulsetime=900, speed=600, bounce=60):
        #current position of belt
        self.position = position
        #Setpoint for desired position of belt
        self.newposition = position
        #direction of motors - used to increment/decrement position
        self.direction = 0
        #Max time a white pulse should be seen - default 700ms
        #White = 0, Black = 1
        self.pulsetime = pulsetime
        
        #time to wait to check sensor after debounce
        self.bounce = bounce
        
        #time since last transition of sensor
        self.sensestart = time.ticks_ms()

        #Setup PWM and Sensor pins
        self.dirset = Pin(dirpin, Pin.OUT)
        self.step = PWM(Pin(steppin), freq=speed, duty=100)
        
        #Enable pin is active low, set to 1 to disable
        self.enable = Pin(enablepin, Pin.OUT)
        self.enable.value(1)
        
        self.beltsensepin = Pin(beltpin, Pin.IN)
        
        #Track the last state of sensor to check for false on or off
        self.laststate = self.beltsensepin.value()
        
        #setup IRQ for transition of sensor on either edge
        self.beltsense = self.beltsensepin.irq(handler=self.sensecheck, trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING)
        
        #Timer for pulse length timeout - endstops > pulsewidth
        self.mt = Timer(-1)
        
        #Timer for overall no signal timeout > 4 times the pulsewidth
        self.wd = Timer(-1)
        
        #Lockout flag while in IRQ handler
        self.insense = False
        
        #If True, stop at next possible time
        self.stop = False

        #import uio
        #try:
        #    settings = uio.open("curtain.ini")
        #    position = 
        #except:
        #    print("Could not open settings ...")
        
        self.state = state
        self.statechange = False

    def timeout(self, value):
        #mt periodic timer handler
        #Shutdown motors first - we're at the endstop
        self.enable.value(1)
        
        #Stop this timer and wd Timer from future firing
        self.mt.deinit()
        self.wd.deinit()
        
        #Check directions and set positions
        #If we end up here, our counting was not right
        if self.direction > 0:
            #print("Curtain open",self.position, self.newposition)
            self.state = "OpenStop"
            self.position += 1
            self.newposition +=1
        if self.direction < 0:
            #print("Curtain closed")
            self.state = "CloseStop"
            self.position = -1
            self.newposition = -1
        self.statechange = True

    #Something is seriously wrong, shutdown motors

    def wdcheck(self, value):
        if (self.pulsetime * 4) < time.ticks_diff(time.ticks_ms(), self.sensestart):
            self.enable.value(1)
            self.mt.deinit()
            self.wd.deinit()
            self.state = "Error"
            self.statechange = True
            print("No encoder activity detected, stopping ...")
    
    def sensecheck(self, value):
        if self.insense:
            return
        self.insense = True
        time.sleep_ms(10)
        first = self.beltsensepin.value()
        time.sleep_ms(self.bounce)
        #if time.ticks_diff(time.ticks_ms(), self.sensestart) < 20:
        #    self.insense = False
        #    return
        if first != self.beltsensepin.value():
            # two measurements need to be same or else false trigger
            self.insense = False
            return
        if first == self.laststate:
            # Can't be same state as it was before
            self.insense = False
            return
        self.laststate = first
        print(time.ticks_diff(time.ticks_ms(), self.sensestart))
        if first == 0:
            # dark to light?
            self.mt.init(period=self.pulsetime, mode=Timer.PERIODIC, callback=self.timeout)
        if first == 1:
            # light to dark?
            self.mt.deinit()
            self.position += self.direction
            if self.position == self.newposition or self.stop:
                self.stop = False
                self.newposition = self.position
                self.enable.value(1)
                self.wd.deinit()
                if self.position == 0:
                    self.state = "Closed"
                else:
                    self.state = "Open"
                self.statechange = True
                #print("At newpos")
        #print("ST:", first, "diff:", time.ticks_diff(time.ticks_ms(), self.sensestart))
        #print("Pos:", self.position)
        self.sensestart = time.ticks_ms()
        self.insense = False 
        
    def setposition(self, newpos):
        print("pos: ", self.position, "newpos: ", self.newposition, "requested: ", newpos)
        if newpos == self.newposition:
            return
        if self.state == "Moving" and not self.stop:
            self.stop = True
            return
        self.newposition = newpos
        if self.position < self.newposition:
            self.dirset.value(1)
            print("dirset should be 1: ", self.dirset.value())
            self.direction = 1
            self.enable.value(0)
        if self.position > self.newposition:
            self.dirset.value(0)
            print("dirset should be 0 or -1: ", self.dirset.value())
            self.direction = -1
            self.enable.value(0)
        self.sensestart = time.ticks_ms()
        self.wd.init(period=self.pulsetime, mode=Timer.PERIODIC, callback=self.wdcheck)
        self.state = "Moving"
        self.statechange = True
        #print(self.sensestart)

    def hardstop(self):
        self.enable.value(1)
        self.mt.deinit()
        self.wd.deinit()
        self.state = "HardStop"
        self.statechange = True
        print("Stopped")

