from machine import Pin, SPI, RTC, Timer
import framebuf
import utime
import time
import math
import random
import os

WF_PARTIAL_2IN13_V3= [
    0x0,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x80,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x40,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x14,0x0,0x0,0x0,0x0,0x0,0x0,  
    0x1,0x0,0x0,0x0,0x0,0x0,0x0,
    0x1,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x22,0x22,0x22,0x22,0x22,0x22,0x0,0x0,0x0,
    0x22,0x17,0x41,0x00,0x32,0x36,
]

WS_20_30_2IN13_V3 = [ 
    0x80,0x4A,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x40,0x4A,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x80,0x4A,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x40,0x4A,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0xF,0x0,0x0,0x0,0x0,0x0,0x0,    
    0xF,0x0,0x0,0xF,0x0,0x0,0x2,    
    0xF,0x0,0x0,0x0,0x0,0x0,0x0,    
    0x1,0x0,0x0,0x0,0x0,0x0,0x0,    
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,    
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,    
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,    
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,    
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,    
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,    
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,    
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,    
    0x22,0x22,0x22,0x22,0x22,0x22,0x0,0x0,0x0,  
    0x22,0x17,0x41,0x0,0x32,0x36  
]

EPD_WIDTH       = 122
EPD_HEIGHT      = 250

RST_PIN         = 12
DC_PIN          = 8
CS_PIN          = 9
BUSY_PIN        = 13


class EPD_2in13_V3_Landscape(framebuf.FrameBuffer):
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        if EPD_WIDTH % 8 == 0:
            self.width = EPD_WIDTH
        else :
            self.width = (EPD_WIDTH // 8) * 8 + 8

        self.height = EPD_HEIGHT
        
        self.full_lut = WF_PARTIAL_2IN13_V3
        self.partial_lut = WS_20_30_2IN13_V3
        
        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.height, self.width, framebuf.MONO_VLSB)
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)   

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        print('busy')
        self.delay_ms(10)
        while(self.digital_read(self.busy_pin) == 1):      # 0: idle, 1: busy
            self.delay_ms(10)    
        print('busy release')

    def TurnOnDisplay(self):
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xC7)
        self.send_command(0x20)  #  Activate Display Update Sequence    
        self.ReadBusy()

    def TurnOnDisplayPart(self):
        self.send_command(0x22)  # Display Update Control
        self.send_data(0x0F)     # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20)  # Activate Display Update Sequence 
        self.ReadBusy()

    def LUT(self, lut):
        self.send_command(0x32)
        for i in range(0,153):
            self.send_data(lut[i])
        self.ReadBusy()

    def LUT_by_host(self, lut):
        self.LUT(lut)             # lut
        self.send_command(0x3F)
        self.send_data(lut[153])
        self.send_command(0x03)   # gate voltage
        self.send_data(lut[154])
        self.send_command(0x04)   # source voltage
        self.send_data(lut[155])  # VSH
        self.send_data(lut[156])  # VSH2
        self.send_data(lut[157])  # VSL
        self.send_command(0x2C)   # VCOM
        self.send_data(lut[158])

    def SetWindows(self, Xstart, Ystart, Xend, Yend):
        self.send_command(0x44)                #  SET_RAM_X_ADDRESS_START_END_POSITION
        self.send_data((Xstart >> 3) & 0xFF)
        self.send_data((Xend >> 3) & 0xFF)
        
        self.send_command(0x45)                #  SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)
        self.send_data(Yend & 0xFF)
        self.send_data((Yend >> 8) & 0xFF)

    def SetCursor(self, Xstart, Ystart):
        self.send_command(0x4E)             #  SET_RAM_X_ADDRESS_COUNTER
        self.send_data(Xstart & 0xFF)
        
        self.send_command(0x4F)             #  SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)

    def init(self):
        print('init')
        self.reset()
        self.delay_ms(100)
        
        self.ReadBusy()
        self.send_command(0x12)  # SWRESET
        self.ReadBusy()
        
        self.send_command(0x01)  # Driver output control 
        self.send_data(0xf9)
        self.send_data(0x00)
        self.send_data(0x00)
        
        self.send_command(0x11)  #data entry mode 
        self.send_data(0x07)
        
        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)
        
        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x05)
        
        self.send_command(0x21) # Display update control
        self.send_data(0x00)
        self.send_data(0x80)
        
        self.send_command(0x18) # Read built-in temperature sensor
        self.send_data(0x80)
        
        self.ReadBusy()
        self.LUT_by_host(self.partial_lut)

    def Clear(self):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(0xFF)
                
        self.TurnOnDisplay()    

    def display(self, image):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])

        self.TurnOnDisplay()

    def Display_Base(self, image):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
                
        self.send_command(0x26)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
                
        self.TurnOnDisplay()
        
    def display_Partial(self, image):
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(1)
        self.digital_write(self.reset_pin, 1)
        
        self.LUT_by_host(self.full_lut)
        
        self.send_command(0x37)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x40)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        
        self.send_command(0x3C)
        self.send_data(0x80)
        
        self.send_command(0x22)
        self.send_data(0xC0)
        self.send_command(0x20)
        self.ReadBusy()
        
        self.SetWindows(0,0,self.width-1,self.height-1)
        self.SetCursor(0,0)
        
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
                
        self.TurnOnDisplayPart()
    
    def sleep(self):
        self.send_command(0x10) #enter deep sleep
        self.send_data(0x01)
        self.delay_ms(100)
        
        
class Environment():
    
    conversion_factor = 3.3 / (65535)    
    
    def __init__(self, dt = None):
        
        self.rtc = RTC()
        if dt:
            self.rtc.datetime(dt)
            time.sleep(0.1) # this seems needed to reflect sprcified dt in self.rtc

        self.dtTuple = self.rtc.datetime()
        
        self.tempBuff = [0 for x in range(5)]
        self.idx = -1
        self.measure(0)
        
        self.timer = Timer()
        self.timer.init(period = 1000 * 60, callback = self.measure) #1?????????
        
    def measure(self, t):

        self.idx = (self.idx + 1) % 5
        
        # The temperature sensor measures the Vbe voltage of a biased bipolar diode, connected to the fifth ADC channel
        # Typically, Vbe = 0.706V at 27 degrees C, with a slope of -1.721mV (0.001721) per degree. 
        self.tempBuff[self.idx] = 27 - ((machine.ADC(4).read_u16() * Environment.conversion_factor) - 0.706) / 0.001721        
            
    def update(self):

        t = [x for x in self.tempBuff if 0 < x]
        self.tempValue = round(sum(t) / len(t), 1)

        t = str(self.tempValue)
        self.tempStr = t + ('' if '.' in t else '.0') + 'C'

        self.dtTuple = self.rtc.datetime()

        day = ''
        if self.dtTuple[3] == 0:
            day = 'Mon'
        elif self.dtTuple[3] == 1:
            day = 'Tue'
        elif self.dtTuple[3] == 2:
            day = 'Wed'
        elif self.dtTuple[3] == 3:
            day = 'Thu'
        elif self.dtTuple[3] == 4:
            day = 'Fri'
        elif self.dtTuple[3] == 5:
            day = 'Sat'
        elif self.dtTuple[3] == 6:
            day = 'Sun'

        dt = [('0' if len(str(x)) < 2 else '') + str(x) for x in self.dtTuple]        
        self.dtStr = dt[0] + '-' + dt[1] + '-' + dt[2] + ' ' + day + ' ' + dt[4] + ':' + dt[5] + ':' + dt[6]
    
    
class Logger():
    
    # 5???????????????????????????????????????
    # -> 18 * 60 / 5 = 216 Pixel????????????????????????-> 18????????????????????????????????????
    # -> 1,000,000???????????????????????? -> 1000000 * 5 / (60 * 24 * 365) = 9.5???????????????????????????
    
    weekLength = int(7 * 24 * 60 / 5) # ????????????????????????????????????
    dayLength = int(24 * 60 / 5)
    halfDayLength = int(12 * 60 / 5)
    displayLength = int(18 * 60 / 5)
    
    logFileName = 'history.log'
    falseRestore = True
    
    def __init__(self, wakeupDT, env, dummy = False):
        
        if dummy: #????????????
            self.temp = [random.uniform(19, 24) for x in range(Logger.weekLength)]
            self.distance = [random.uniform(0, 10) for x in range(Logger.weekLength)]
            self.currentIndex = -1

        else:
            self.temp = [0.0 for x in range(Logger.weekLength)]
            self.distance = [0.0 for x in range(Logger.weekLength)]

            if Logger.logFileName in os.listdir():
                with open(Logger.logFileName, 'r') as fp:
                    lastUpdateDT = [int(x) for x in fp.readline().split(',')]

                    # wakeupDT???lastUpdateDT??????????????????????????????????????????????????????????????????????????????????????????
                    # ??????????????????????????????????????????OFF?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                    if ''.join([str(x) for x in lastUpdateDT[:4]]) == ''.join([str(x) for x in wakeupDT[:4]]) or Logger.falseRestore:
                        
                        lastUpdateMin = (lastUpdateDT[4] * 60) + lastUpdateDT[5] + (lastUpdateDT[6] / 60)
                        wakeupMin = (wakeupDT[4] * 60) + wakeupDT[5] + (wakeupDT[6] / 60)
                        diffMin = wakeupMin - lastUpdateMin

                        idx = 0
                        for line in fp.readlines():
                            self.temp[idx], self.distance[idx] = [float(x) for x in line.split(',')]
                            idx += 1

                        #?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                        #??????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                        if 0 < diffMin and (not Logger.falseRestore): 
                            offsetIdx = round(diffMin / 5) % Logger.weekLength

#                            print(lastUpdateDT)
#                            print(wakeupDT)
#                            print(diffMin, diffMin / 60)
#                            print(offsetIdx)
                            
                            for i in range(offsetIdx):
                                self.temp[i] = 0.0
                                self.distance[i] = 0.0

                            self.currentIndex = offsetIdx - 1

                        else:
                            env.rtc.datetime(lastUpdateDT) # restore last updated time if time didn't proceed
                            time.sleep(0.1) # this seems needed to reflect dt in rtc
                            self.currentIndex = -1

                    else:
                        self.currentIndex = -1
            
            else:
                self.currentIndex = -1

    def update(self, tempValue, dt, distance):
        
        self.currentIndex = (self.currentIndex + 1) % Logger.weekLength
        self.temp[self.currentIndex] = tempValue
        self.distance[self.currentIndex] = distance
        
        self.distanceWeek = round(sum([self.distance[(self.currentIndex - i) % Logger.weekLength] for i in range(Logger.weekLength)]) / 1000, 1)
        self.distanceDay = round(sum([self.distance[(self.currentIndex - i) % Logger.weekLength] for i in range(Logger.dayLength)]))
        self.distanceHalfDay = round(sum([self.distance[(self.currentIndex - i) % Logger.weekLength] for i in range(Logger.halfDayLength)]))
        
        self.distLog = str(self.distanceWeek) + 'km/week ' + str(self.distanceDay) + 'm/day ' + str(self.distanceHalfDay) + 'm/12h'

        with open(Logger.logFileName, 'w') as fp:
            fp.write(','.join([str(x) for x in dt]) + '\n')

            idx = self.currentIndex + 1
            for x in range(Logger.weekLength):
                fp.write(','.join([str(self.temp[idx]), str(self.distance[idx])]) + '\n')
                idx = (idx + 1) % Logger.weekLength

class Counter():
    
    unit = math.pi * 0.16 #[m]    
    
    def __init__(self):
        
        self.lastTick = time.ticks_ms()        
        self.distance = 0.0
        self.led = Pin(25, Pin.OUT)
        
        # ???????????????????????????????????????GP4????????????pull up????????????
        Pin(2, Pin.IN, Pin.PULL_UP)
        Pin(3, Pin.IN, Pin.PULL_UP)
        Pin(5, Pin.IN, Pin.PULL_UP)

        # GND???????????????
        Pin(26, Pin.IN, Pin.PULL_DOWN)
        Pin(27, Pin.IN, Pin.PULL_DOWN)
        Pin(28, Pin.IN, Pin.PULL_DOWN)
        
        p4 = Pin(4, Pin.IN, Pin.PULL_UP)
        p4.irq(self.increment, Pin.IRQ_FALLING)
    
    def increment(self, pin):
        
        diff = time.ticks_diff(time.ticks_ms(), self.lastTick)
        self.lastTick = time.ticks_ms()
        if diff < 250:
            return
        
        self.distance += Counter.unit
#        print(self.distance)

        self.led.value(1)            
        time.sleep(0.2)
        self.led.value(0)
        
        
class Control():
    
    def __init__(self, env, logger, counter, epd):
        
        self.env = env
        self.logger = logger
        self.counter = counter
        
        self.epd = epd
        
        self.timer = Timer()
        self.timer.init(period = 1000 * 60 * 5, callback = self.update) #5?????????        
        self.update(0)
        
    def drawTimeAxis(self):
        
        h = self.env.dtTuple[4]
        m = self.env.dtTuple[5]
        
        c5Index = math.floor(0.2 * m) # 12 * m / 60
        self.epd.text('t', 0, 121, 0x00)
        
        h3 = 0
        for i in range(216):
            idx = (c5Index - i) % 12
            if idx == 0:
                if h3 == 0:
                    x = 216 - i - (8 if 9 < h else 4)
                    if 8 < x:
                        self.epd.text(str(h), x, 121, 0x00)
                    self.epd.vline(216 - i, 121 - 7, 6, 0x00)
                    
                else:
                    self.epd.vline(216 - i, 121 - 5, 4, 0x00)
                    
                h3 = (h3 + 1) % 3
                h = (h - 1) % 24
        
    def update(self, t):
        
        self.env.update()
        self.logger.update(self.env.tempValue, self.env.dtTuple, self.counter.distance)
        self.counter.distance = 0
        
        self.epd.init()
        
        self.epd.fill(0xff)
        self.epd.text(self.env.dtStr, 0, 8 - 1, 0x00)
        self.epd.text(self.env.tempStr, 200, 8 - 1, 0x00)
        self.epd.text(self.logger.distLog, 0, 16 + 2 - 1, 0x00)
        
        self.epd.hline(0, 119, 216, 0x00)
        self.epd.vline(0, 30, 122 - 32, 0x00)
        self.epd.vline(0 + 216, 30, 122 - 32, 0x00)
                
        self.drawTimeAxis()
        self.drawGraph()
        
        self.epd.display(self.epd.buffer)
        self.epd.sleep()
        
    def drawGraph(self):
        
        distList = [self.logger.distance[(self.logger.currentIndex + i) % Logger.weekLength] for i in range(-1 * Logger.displayLength + 1, 1)]
        distUpper = round(100 * math.ceil((1 + sum(distList)) / 100))            
        
        self.epd.text(str(distUpper), 250 - 8 * 4 - 1, 31, 0x00)
        self.epd.text('m', 250 - 8 * 4 - 1, 31 + 8, 0x00)
        self.epd.hline(250 - 8 * 4 - 6, 30, 5, 0x00)
        self.epd.text(str(round(distUpper / 2)), 250 - 8 * 4 - 1, 32 - 1 + 44, 0x00)
        self.epd.text('m', 250 - 8 * 4 - 1, 32 - 1 + 44 + 8, 0x00)
        self.epd.hline(250 - 8 * 4 - 6, 74, 5, 0x00)
        self.epd.text('0m', 250 - 8 * 4 - 1, 121 - 9, 0x00)

        total = distList[0]        

        if 0 < distUpper:
            for i in range(1, len(distList)):
                self.epd.line(i - 1, 119 - round(89 * total / distUpper), i, 119 - round(89 * (total + distList[i]) / distUpper), 0x00)
                total += distList[i]
        
        tempList = [self.logger.temp[(self.logger.currentIndex + i) % Logger.weekLength] for i in range(-1 * Logger.displayLength + 1, 1)]    
        tempLower = math.floor(min([x for x in tempList if 0 < x]))
        tempUpper = math.ceil(max([x for x in tempList if 0 < x]))
        tempWindow = tempUpper - tempLower
        
        self.epd.text(str(tempUpper) + 'C', 2, 32, 0x00)
        self.epd.hline(1, 30, 5, 0x00)
        self.epd.text(str(tempLower) + 'C', 2, 121 - 11, 0x00)
        
        self.epd.text(str(round((tempLower + tempUpper) / 2, 1)).replace('.0', 'C'), 2, 76, 0x00)
        self.epd.hline(1, 74, 5, 0x00)        

        if 0 < tempWindow:
            for i in range(len(tempList)):
                if tempList[i] <= 0:
                    continue
            
                self.epd.pixel(i, 119 - round(89 * (tempList[i] - tempLower) / tempWindow), 0x00)


if __name__=='__main__':

    epd = EPD_2in13_V3_Landscape()
    
    ''' # for clearing display
    counter.led.value(1)
    epd.Clear() # ???????????????????????????
    for i in range(30):
        counter.led.toggle()
        epd.delay_ms(100)

    counter.led.value(1)
    counter.led.value(0)        
    '''
    
    counter = Counter()
    env = Environment(dt = (2023, 2, 27, 0, 21, 30, 0, 0))
#    env = Environment()
    logger = Logger(env.dtTuple, env)

    ctrl = Control(env, logger, counter, epd)


'''
Thonny??????????????????????????????????????????Tonny?????????????????????????????????????????????????????????????????????????????????

?????????????????????????????????????????????????????????
?????????PartialUpdate?????????-> ????????????????????????????????????????????????????????????????????????????????????

wifi????????????????????????????????????????????????SSID???????????????web????????????SSID???????????????????????????????????????????????????
-> QR?????????(???URL)??????????????????????????????????????????????????????
-> ????????????????????????

??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
?????????????????????????????????????????????????????????????????????????????????
'''

