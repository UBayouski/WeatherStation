#!/usr/bin/python
'''*****************************************************************************************************************
    Raspberry Pi Weather Station
    By Uladzislau Bayouski
    https://www.linkedin.com/in/uladzislau-bayouski-a7474111b/

    A Raspberry Pi based weather station that measures temperature, humidity and pressure using
    the Astro Pi Sense HAT then uploads the data to a Weather Underground weather station. 
    Completely configurable and working asyncroniously in multi threads.
********************************************************************************************************************'''
from __future__ import print_function
from collections import deque
from sense_hat import SenseHat, ACTION_RELEASED, DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT
from signal import pause
from urllib import urlencode
from threading import Timer

import datetime
import logging 
import os
import sys
import urllib2
import time

from config import Config
from weather_entities import DEFAULT_WEATHER_ENTITIES, CarouselContainer, WeatherEntityType

class WeatherStation(CarouselContainer):
    # Constants
    SMOOTH_READINGS_NUMBER = 3

    def __init__(self, sense_hat):
        super(WeatherStation, self).__init__()

        self._sense_hat = sense_hat
        self._log_timer = None
        self._upload_timer = None
        self._last_readings = None

        # Setup Sense Hat joystic
        self._sense_hat.stick.direction_up = self._change_weather_entity
        self._sense_hat.stick.direction_down = self._change_weather_entity
        self._sense_hat.stick.direction_left = self._change_weather_entity
        self._sense_hat.stick.direction_right = self._change_weather_entity

    @property
    def carousel_items(self):
        return DEFAULT_WEATHER_ENTITIES

    @property
    def current_style(self):
        return self.current_item.current_style
    
    def start_station(self):
        if Config.LOG_TO_CONSOLE and Config.LOG_INTERVAL:
            self._log_results()

        if Config.UPLOAD_INTERVAL:
            self._upload_results()

    def stop_station(self):
        if self._log_timer:
            self._log_timer.cancel()

        if self._upload_timer:
            self._upload_timer.cancel()

        if self._sense_hat:
            self._sense_hat.clear()

    @staticmethod
    def to_fahrenheit(value):
        """Converts celsius temperature to fahrenheit"""
        return (value * 1.8) + 32

    def get_temperature(self):
        # ====================================================================
        # Unfortunately, getting an accurate temperature reading from the
        # Sense HAT is improbable, see here:
        # https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
        # so we'll have to do some approximation of the actual temp
        # taking CPU temp into account. The Pi foundation recommended
        # using the following:
        # http://yaab-arduino.blogspot.co.uk/2016/08/accurate-temperature-reading-sensehat.html
        # ====================================================================
        # First, get temp readings from both sensors
        t1 = self._sense_hat.get_temperature_from_humidity()
        t2 = self._sense_hat.get_temperature_from_pressure()
        # t becomes the average of the temperatures from both sensors
        t = (t1 + t2) / 2
        # Now, grab the CPU temperature
        t_cpu = self._get_cpu_temp()
        # Calculate the 'real' temperature compensating for CPU heating
        t_corr = t - ((t_cpu - t) / 1.5)
        # Finally, average out that value across the last three readings
        t_corr = self._get_smooth(t_corr)
        # convoluted, right?
        # Return the calculated temperature
        return t_corr

    def get_humidity(self):
        return self._sense_hat.get_humidity()

    def get_pressure(self):
        # convert pressure from millibars to inHg before posting
        return self._sense_hat.get_pressure() * 0.0295300

    def _change_weather_entity(self, event):
        if event.action == ACTION_RELEASED:
            sensors_data = self._get_sensors_data()
            self._sense_hat.clear()

            if event.direction == DIRECTION_UP:
                self._show_message(self.next_item.entity_messsage)
            elif event.direction == DIRECTION_DOWN:
                self._show_message(self.previous_item.entity_messsage)
            elif event.direction == DIRECTION_LEFT:
                self.current_item.previous_item
            else:
                self.current_item.next_item

            self._update_display(sensors_data)

    def _show_message(self, message):
        self._sense_hat.rotation = 0
        self._sense_hat.show_message(message, Config.SCROLL_TEXT_SPEED)

    def _update_display(self, sensors_data):
        if self.current_item.entity_type is WeatherEntityType.TEMPERATURE:
            pixels = self.current_item.show_pixels(sensors_data[0])
        elif self.current_item.entity_type is WeatherEntityType.HUMIDITY:
            pixels = self.current_item.show_pixels(sensors_data[2])
        else:
            pixels = self.current_item.show_pixels(sensors_data[3])

        self._sense_hat.set_rotation(self.current_style.rotation)
        self._sense_hat.set_pixels(pixels)
    
    def _get_sensors_data(self):
        temp_in_celsius = self.get_temperature()
        return (
            round(temp_in_celsius, 1), 
            round(self.to_fahrenheit(temp_in_celsius), 1), 
            round(self.get_humidity(), 0), 
            round(self.get_pressure(), 1)
        )    
    
    def _log_results(self, first_time=True):
        if not first_time:
            print('Temp: %sC (%sF), Pressure: %s inHg, Humidity: %s%%' % self._get_sensors_data())

        self._log_timer = Timer(Config.LOG_INTERVAL, self._log_results, [False])
        self._log_timer.daemon = True
        self._log_timer.start()

    def _upload_results(self, first_time=True):
        if not first_time:
            sensors_data = self._get_sensors_data()
            self._update_display(sensors_data)
            # ========================================================
            # Upload the weather data to Weather Underground
            # ========================================================
            # is weather upload enabled (True)?
            if Config.WEATHER_UPLOAD:
                # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol
                print('Uploading data to Weather Underground')
                # build a weather data object
                weather_data = {
                    'action': 'updateraw',
                    'ID': Config.STATION_ID,
                    'PASSWORD': Config.STATION_KEY,
                    'dateutc': 'now',
                    'tempf': str(sensors_data[1]),
                    'humidity': str(sensors_data[2]),
                    'baromin': str(sensors_data[3]),
                }
                try:
                    upload_url = Config.WU_URL + '?' + urlencode(weather_data)
                    response = urllib2.urlopen(upload_url)
                    html = response.read()
                    print('Server response: ', html)
                    # do something
                    response.close()  # best practice to close the file
                except:
                    print('Exception: %s\n' % sys.exc_info()[0])
            else:
                print('Skipping Weather Underground upload')

        self._upload_timer = Timer(Config.UPLOAD_INTERVAL, self._upload_results, [False])
        self._upload_timer.daemon = True
        self._upload_timer.start()

    def _get_cpu_temp(self):        
        # 'borrowed' from https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
        # executes a command at the OS to pull in the CPU temperature
        res = os.popen('vcgencmd measure_temp').readline()
        return float(res.replace('temp=', '').replace("'C\n", ''))

    # use moving average to smooth readings
    def _get_smooth(self, value):
        # do we have the t object?
        if not self._last_readings:
            # then create it
            self._last_readings = deque((value, ) * 3, self.SMOOTH_READINGS_NUMBER)
        else:
            # manage the rolling previous values
            self._last_readings.appendleft(value)
        # average the three last temperatures
        return sum(self._last_readings) / self.SMOOTH_READINGS_NUMBER

# ============================================================================
#  Read Weather Underground Configuration Parameters
# ============================================================================
print('\nInitializing Weather Underground configuration')
if (Config.STATION_ID is None) or (Config.STATION_KEY is None):
    print('Missing values from the Weather Underground configuration file\n')
    sys.exit(1)

# make sure we don't have a MEASUREMENT_INTERVAL > 60
if (Config.UPLOAD_INTERVAL is None) or (Config.UPLOAD_INTERVAL > 600):
    print("The application's 'MEASUREMENT_INTERVAL' cannot be empty or greater than 600")
    sys.exit(1)

# we made it this far, so it must have worked...
print('Successfully read Weather Underground configuration values')
print('Station ID: ', Config.STATION_ID)

# ============================================================================
# initialize the Sense HAT object
# ============================================================================
try:
    print('Initializing the Sense HAT client')
    sense = SenseHat()
    # sense.set_rotation(180)
    # then write some text to the Sense HAT's 'screen'
    # sense.show_message('Init', text_colour=[255, 255, 0], back_colour=[0, 0, 255])
    # clear the screen
    sense.clear()
    # get the current temp to use when checking the previous measurement
    #last_temp = round(get_temp(), 1)
    #print('Current temperature reading: ', last_temp, 'C')
except:
    print('Unable to initialize the Sense HAT library: ', sys.exc_info()[0])
    sys.exit(1)

print('Initialization complete!')

# Now see what we're supposed to do next
if __name__ == '__main__':
    try:
        station = WeatherStation(sense)
        station.start_station()
        pause()
    except:
        logging.basicConfig(
            filename='./weather_station/error.log', 
            filemode='w', 
            format='%(asctime)s %(levelname)s %(message)s', 
            level=logging.ERROR
        )
        logging.error('', exc_info=True)
        station.stop_station();
        print('\nExiting application\n')
        sys.exit(0)
