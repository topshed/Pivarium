#print("Starting")
import os
#import numpy as np
import glob
import time
import logzero
from logzero import logger
import RPi.GPIO as GPIO
from ISStreamer.Streamer import Streamer
from gpiozero import LED, Button
import inkyphat
from datetime import datetime as dt
from PIL import ImageFont, Image
import sys
sys.path.insert(0, '/home/pi/DHT11_Python')
import Adafruit_DHT
logzero.logfile("/home/pi/viv.log",maxBytes=1000000)
logger.debug("Finished imports")
humidity_gpio_pin = 3
humidity_sensor = Adafruit_DHT.DHT22
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
logger.debug("Setting door locks")
leftside = Button(20)
leftside_led = LED(21)
leftside_led.source = leftside.values
rightside = Button(19)
rightside_led = LED(26)
rightside_led.source = rightside.values

City = "SnakeTown"
BUCKET_NAME = ":snake:Vivarium"
BUCKET_KEY = ""
ACCESS_KEY = ""
SENSOR_LOCATION_NAME = "Viv1"

streamer = Streamer(bucket_name = BUCKET_NAME, bucket_key = BUCKET_KEY, access_key = ACCESS_KEY)
def iclear(col): # Clear inkyphat but don't refresh
    for x in range(212):
        for y in range(104):
            inkyphat.putpixel((x,y), col)

def iclearNow(col): # claer inkyphat and refresh
    for x in range(212):
        for y in range(104):
            inkyphat.putpixel((x,y), col)
    inkyphat.show()

def viv_display(th,tr,tc,hh): # display readinga and any alerts on inkyphat
    #logger.debug("Setting inkyphat")
    iclear(0)

    # load background image
    inkyphat.set_image(Image.open("/home/pi/snake-back.png"))
    # set font sizes
    font = ImageFont.truetype(inkyphat.fonts.FredokaOne, 28)
    smallfont = ImageFont.truetype(inkyphat.fonts.FredokaOne, 10)
    midfont = ImageFont.truetype(inkyphat.fonts.FredokaOne, 16)

    # Top left box for hot-end temp
    inkyphat.rectangle([2,2,70,25], fill=inkyphat.BLACK, outline=1)
    inkyphat.rectangle([2,2,70,70], fill=None, outline=1)#top left
    message = "HOT"
    inkyphat.text((20, 3), message, inkyphat.WHITE, midfont)
    if th > 28 and th < 31:
        inkyphat.text((8, 25), str(th), inkyphat.BLACK, font)
    else:
        inkyphat.text((8, 25), str(th), inkyphat.RED, font)

    #Middle box for roof temp
    inkyphat.rectangle([74,2,142,25], fill=inkyphat.BLACK, outline=1) # top middle
    inkyphat.rectangle([74,2,142,70], fill=None, outline=1)
    message = "ROOF"
    inkyphat.text((88, 3), message, inkyphat.WHITE, midfont)
    if tr > 34 and tr < 37:
        inkyphat.text((81, 25), str(tr), inkyphat.BLACK, font)
    else:
        inkyphat.text((81, 25), str(tr), inkyphat.RED, font)

    # Right box for cool end temp
    inkyphat.rectangle([146,2,210,25], fill=inkyphat.BLACK, outline=1) # top middle
    inkyphat.rectangle([146,2,210,70], fill=None, outline=1)
    message = "COOL"
    inkyphat.text((156, 3), message, inkyphat.WHITE, midfont)
    if tc > 21 and tc < 27:
        inkyphat.text((152, 25), str(tc), inkyphat.BLACK, font)
    else:
        inkyphat.text((152, 25), str(tc), inkyphat.RED, font)

    # Bottom left box for humidity
    inkyphat.rectangle([12,74,55,100], fill=inkyphat.BLACK, outline=1) # top middle
    inkyphat.rectangle([12,74,102,100], fill=None, outline=1)
    message = "Hum"
    inkyphat.text((16, 80), message, inkyphat.WHITE, midfont)
    if hh > 20 and hh < 75:
        inkyphat.text((62, 78), str(hh)+"%", inkyphat.BLACK, midfont)
    else:
        inkyphat.text((62,78), str(hh)+"%", inkyphat.RED, midfont)

    # Bottom middle for time
    rightnow = dt.now()
    inkyphat.text((110, 70), str("%02d" % (rightnow.hour,)) + ":" + str("%02d" % (rightnow.minute,)), inkyphat.RED, font)

    #print("Displaying on inkyphat")
    inkyphat.show()

def read_dht22(pin):
    humidity, temperature = Adafruit_DHT.read_retry(humidity_sensor, pin)
    while humidity is None or temperature is None: # on Linux, timings don't always work so get None
        humidity, temperature = Adafruit_DHT.read_retry(humidity_sensor, pin)
        logger.error("Retrying DHT22 read")
        time.sleep(0.1)
    return humidity, temperature


# 28-031651fb6bff  28-051684c1c6ff
base_dir = '/sys/bus/w1/devices/'
device_folder_t1 = '28-031651fb6bff'
device_folder_t2 = '28-051684c1c6ff'
DS18B20_t1 = base_dir + device_folder_t1 + '/w1_slave'
DS18B20_t2 = base_dir + device_folder_t2 + '/w1_slave'

def read_temp_DS18B20_raw_1():
    f = open(DS18B20_t1, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp_DS18B20_raw_2():
    f = open(DS18B20_t2, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp_DS18B20_1():
    lines = read_temp_DS18B20_raw_1()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_DS18B20_raw_1()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def read_temp_DS18B20_2():
    lines = read_temp_DS18B20_raw_2()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_DS18B20_raw_2()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

is_time = 0
hot_end = 0
#for i in range(40):
while True:
    #print("Taking readings")
    #print("Hot End")
    hot_end = read_temp_DS18B20_1()
    #print("Cool End")
    cool_end = read_temp_DS18B20_2()
    #print("Roof")
    dht22_h, dht22_t = read_dht22(humidity_gpio_pin)
    logger.info(str(round(hot_end,1)) + " " +str(round(dht22_t,1)) + " " + str(round(cool_end,1)) + " " + str(round(dht22_h,1)))
    viv_display(round(hot_end,1),round(dht22_t,1),round(cool_end,1),round(dht22_h))
    if is_time > 2:
        try:
            logger.debug("Uploading to InitialState")
            streamer.log(":sunny: " + SENSOR_LOCATION_NAME + " Hot End temp (C)", round(hot_end,2) )
            streamer.log(":sunny: " + SENSOR_LOCATION_NAME + " Roof Temp (C)", round(dht22_t,2) )
            streamer.log(":sunny: " + SENSOR_LOCATION_NAME + " Cool End temp (C)", round(cool_end,2) )
            streamer.log(":sweat_drops: " + SENSOR_LOCATION_NAME + " Humidity (%)", round(dht22_h,2) )
            streamer.flush()
            is_time = 0
        except Exception:
            logger.error("InitialState upload failed")
            continue

    time.sleep(600)
    is_time+=1

GPIO.cleanup()
logger.debug("Exiting")
