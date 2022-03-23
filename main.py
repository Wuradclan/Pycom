# https://github.com/micropython/micropython-lib/blob/master/umqtt.simple/example_sub_led.py
#edited on march 22nd by ait abdellah

from cmath import e
from network import WLAN      # For operation of WiFi network
import time                   # Allows use of time.sleep() for delays
import pycom                  # Base library for Pycom devices
from umqtt import MQTTClient  # For use of MQTT protocol to talk to Adafruit IO
import ubinascii              # Needed to run any MicroPython code
import machine                # Interfaces with hardware components
import micropython            # Needed to run any MicroPython code
##################
#imports for pysence
#import time
#import pycom
from pycoproc_1 import Pycoproc
#import machine
import struct

from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE

# BEGIN SETTINGS
# These need to be change to suit your environment
RANDOMS_INTERVAL = 5000 # milliseconds
last_random_sent_ticks = 0  # milliseconds

# Wireless network
WIFI_SSID = "BELL036"
WIFI_PASS = "your wifi oassword" # No this is not our regular password. :)

# Adafruit IO (AIO) configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "your user"
AIO_KEY = "your Adafruite key"
AIO_CLIENT_ID = ubinascii.hexlify(machine.unique_id())  # Can be anything
AIO_CONTROL_FEED = "wurad/feeds/lights"
AIO_TEMPERATURE_FEED = "wurad/feeds/temperature"
AIO_PRESSURE_FEED = "wurad/feeds/pressure"
AIO_HUMIDITY_FEED = "wurad/feeds/humidity"

#AIO_RANDOMS_FEED = "wurad/feeds/temperature"
# setting pycom variable that will receive the sensors data
temperature = 0
pressure = 0
humidity = 0


# END SETTINGS

# RGBLED
# Disable the on-board heartbeat (blue flash every 4 seconds)
# We'll use the LED to respond to messages from Adafruit IO
pycom.heartbeat(False)
time.sleep(0.1) # Workaround for a bug.
                # Above line is not actioned if another
                # process occurs immediately afterwards
pycom.rgbled(0xff0000)  # Status red = not working

# WIFI
# We need to have a connection to WiFi for Internet access
# Code source: https://docs.pycom.io/chapter/tutorials/all/wlan.html

wlan = WLAN(mode=WLAN.STA)
wlan.connect(WIFI_SSID, auth=(WLAN.WPA2, WIFI_PASS), timeout=5000)

while not wlan.isconnected():    # Code waits here until WiFi connects
    machine.idle()

print("Connected to Wifi")
pycom.rgbled(0xffd7000) # Status orange: partially working

# FUNCTIONS

# Function to respond to messages from Adafruit IO
def sub_cb(topic, msg):          # sub_cb means "callback subroutine"
    print((topic, msg))          # Outputs the message that was received. Debugging use.
    if msg == b"ON":             # If message says "ON" ...
        pycom.rgbled(0xffffff)   # ... then LED on
    elif msg == b"OFF":          # If message says "OFF" ...
        pycom.rgbled(0x000000)   # ... then LED off
    else:                        # If any other message is received ...
        print("Unknown message") # ... do nothing but output that it happened.

# def random_integer(upper_bound):
#     return machine.rng() % upper_bound

# def send_random():
#     global last_random_sent_ticks
#     global RANDOMS_INTERVAL

#     if ((time.ticks_ms() - last_random_sent_ticks) < RANDOMS_INTERVAL):
#         return; # Too soon since last one sent.

#     some_number = random_integer(100)
#     print("Publishing: {0} to {1} ... ".format(some_number, AIO_RANDOMS_FEED), end='')
#     try:
#         client.publish(topic=AIO_RANDOMS_FEED, msg=str(some_number))
#         print("DONE")
#     except Exception as e:
#         print("FAILED")
#     finally:
#         last_random_sent_ticks = time.ticks_ms()

# send data function
#data is the message to send and the feed put one of those variables AIO_CONTROL_FEED AIO_TEMPERATURE_FEED AIO_PRESSURE_FEED AIO_HUMIDITY_FEED 
def publish(feed,data):
   
    print("Publishing: {0} to {1} ... ".format(data, feed), end='')
    try:
        client.publish(topic=feed, msg=str(data))
        print("DONE")
    except Exception as e:
        print("FAILED")
    finally:
        last_random_sent_ticks = time.ticks_ms()


## read sensors data on pysense
py = Pycoproc(Pycoproc.PYSENSE)
# Temperature 
mp = MPL3115A2(py,mode=ALTITUDE) # Returns height in meters. Mode may also be set to PRESSURE, returning a value in Pascals
temperature = mp.temperature() # setting the data sensor to the varible

print("MPL3115A2 temperature: " + str(mp.temperature()))
print("Altitude: " + str(mp.altitude()))
mpp = MPL3115A2(py,mode=PRESSURE) # Returns pressure in Pa. Mode may also be set to ALTITUDE, returning a value in meters
pressure = mpp.pressure() # setting the data to the pressure variable
print("Pressure: " + str(mpp.pressure()))
#
si = SI7006A20(py)
print("Temperature: " + str(si.temperature())+ " deg C and Relative Humidity: " + str(si.humidity()) + " %RH")

print("Dew point: "+ str(si.dew_point()) + " deg C")
temperature = si.temperature()
humidity = si.humidity()
payload = struct.pack(">ff", temperature, humidity)
print(payload)
t_ambient = 24.4
print("Humidity Ambient for " + str(t_ambient) + " deg C is " + str(si.humid_ambient(t_ambient)) + "%RH")


# Use the MQTT protocol to connect to Adafruit IO
client = MQTTClient(AIO_CLIENT_ID, AIO_SERVER, AIO_PORT, AIO_USER, AIO_KEY)

# Subscribed messages will be delivered to this callback
client.set_callback(sub_cb)
client.connect()
client.subscribe(AIO_LIGHTS_FEED)
print("Connected to %s, subscribed to %s topic" % (AIO_SERVER, AIO_LIGHTS_FEED))

pycom.rgbled(0x00ff00) # Status green: online to Adafruit IO

try:                      # Code between try: and finally: may cause an error
                          # so ensure the client disconnects the server if
                          # that happens.
    while 1:              # Repeat this loop forever
        client.check_msg()# Action a message if one is received. Non-blocking.
        publish(AIO_TEMPERATURE_FEED,str(temperature))     # Send temperature sensor data  to Adafruit IO if it's time.
        print("temperature published")
        client.check_msg()
        publish(AIO_PRESSURE_FEED,str(pressure))     # Send pressure sensor data  to Adafruit IO if it's time.
        print("Pressure published")
        client.check_msg()
        publish(AIO_HUMIDITY_FEED,str(humidity))     # Send pressure sensor data  to Adafruit IO if it's time.
        print("Humidity published")
        time.sleep(10)

except Exception as e:
        print("publishing FAILED")

        
finally:                  # If an exception is thrown ...
    client.disconnect()   # ... disconnect the client and clean up.
    client = None
    wlan.disconnect()
    wlan = None
    pycom.rgbled(0x000022)# Status blue: stopped
    print("Disconnected from Adafruit IO.")
