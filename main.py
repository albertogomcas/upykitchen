from machine import Pin, ADC, PWM
import time
import tm1637
import uasyncio as asyncio


class Microwave:
    increment_mseconds = 5000
    max_time = 25000
    running_freq = 50
    running_duty = 50
    beep_freq = 1500
    beep_duty = 512
    
    def __init__(self):
        self.display = tm1637.TM1637(clk=Pin(5), dio=Pin(4))
        self.light = Pin(12, Pin.OUT)
        self.button = Pin(15, Pin.IN)
        self.speaker = PWM(Pin(0), 50)
        self.speaker.duty(0)
        self.remaining = 0
        self.start = None
        self.last_update = None
        self.last_press = None
        self.running = False
        
        self.display.write([0, 0, 0, 0])
        
    def check_button(self):
        if self.button.value():
            if self.last_press and time.ticks_diff(time.ticks_ms(), self.last_press) > 100:
                self.button_pressed()
            else:
                print("Ignored", time.time())
            self.last_press = time.ticks_ms()
          
    def beep(self,duration=100):
        before = self.speaker.duty()
        self.speaker.duty(0)
        self.speaker.freq(Microwave.beep_freq)
        self.speaker.duty(Microwave.beep_duty)
        time.sleep_ms(duration)
        self.speaker.duty(0)
        self.speaker.freq(Microwave.running_freq)
        self.speaker.duty(before)
                    
    def run_start(self):
        self.running = True
        self.light.value(1)
        self.speaker.freq(Microwave.running_freq)
        self.speaker.duty(Microwave.running_duty)
        
    def run_stop(self):
        self.running = False
        self.light.value(0)
        self.speaker.duty(0)
        self.beep(400)
        time.sleep_ms(100)
        self.beep(400)
        time.sleep_ms(100)
        self.beep(400)
                    
    def button_pressed(self):
        self.beep()
        self.run_start()
        self.remaining += Microwave.increment_mseconds
        self.remaining = min(Microwave.max_time, self.remaining)
        
        print("Pressed, remaining", self.remaining)
              
        if self.start is None:
            self.start = time.ticks_ms()
        if self.last_update is None:
            self.last_update = time.ticks_ms()
        
    def update_display(self):
        if self.remaining and self.last_update:
            now = time.ticks_ms()
            self.remaining -= time.ticks_diff(now, self.last_update)
            self.last_update = now
            
            if self.remaining <= 0:
                self.remaining = 0
                self.start = None
                self.last_update = None
                self.display.write([0, 0, 0, 0])
                if self.running:
                    self.run_stop()
                
        if self.remaining != 0:
            self.display.numbers(0, int(self.remaining/1000))
            

class Oven:
    def __init__(self):
        self.ignore = 50 # potentiometer offset
        self.pot = ADC(0)
        self.grill = PWM(Pin(14), 5000)
        self.top = 0    
        
    def update_temp(self):
        pot_value = self.pot.read()
        print(pot_value)
        if pot_value > self.ignore:
            self.top = pot_value
        else:
            self.top = 0
        
        self.grill.duty(self.top)
        
    

async def blink(): # basic test that things are alive
    led = Pin(2, Pin.OUT)
    while True:
        if led.value():
            led.off()
        else:
            led.on()
        await asyncio.sleep(1)  

async def microwave_display(mw):
    while True:
        mw.update_display()
        await asyncio.sleep_ms(100)

async def microwave_button(mw):
    while True:
        mw.check_button()
        await asyncio.sleep_ms(10)
        
async def oven_control(ov):
    while True:
        oven.update_temp()
        await asyncio.sleep_ms(100)

mw = Microwave()  
oven = Oven()

loop = asyncio.get_event_loop()
loop.create_task(blink())
loop.create_task(microwave_display(mw))
loop.create_task(microwave_button(mw))
loop.create_task(oven_control(oven))
loop.run_forever()
