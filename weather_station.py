#!/usr/bin/python
'''*****************************************************************************************************************
    Pi Temperature Station
    By John M. Wargo
    www.johnwargo.com

    This is a Raspberry Pi project that measures weather values (temperature, humidity and pressure) using
    the Astro Pi Sense HAT then uploads the data to a Weather Underground weather station.
********************************************************************************************************************'''

import datetime
import os
import sys
import time
from threading import Timer
from urllib import urlencode

import urllib2
from sense_hat import SenseHat

from config import Config
from weather_entities import DEFAULT_WEATHER_ENTITIES, CarouselContainer

# ============================================================================
# Constants
# ============================================================================

# constants used to display an up and down arrows plus bars
# modified from https://www.raspberrypi.org/learning/getting-started-with-the-sense-hat/worksheet/
# set up the colours (blue, red, empty)
b = [0, 0, 255]  # blue
r = [255, 0, 0]  # red
e = [0, 0, 0]  # empty

# create images for up and down arrows
arrow_up = [
    e, e, e, r, r, e, e, e,
    e, e, r, r, r, r, e, e,
    e, r, e, r, r, e, r, e,
    r, e, e, r, r, e, e, r,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e
]

arrow_down = [
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    b, e, e, b, b, e, e, b,
    e, b, e, b, b, e, b, e,
    e, e, b, b, b, b, e, e,
    e, e, e, b, b, e, e, e
]

bars = [
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    r, r, r, r, r, r, r, r,
    r, r, r, r, r, r, r, r,
    b, b, b, b, b, b, b, b,
    b, b, b, b, b, b, b, b,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e
]

class WeatherStation(CarouselContainer):
    def __init__(self):
        self._weather_entities = DEFAULT_WEATHER_ENTITIES
        self._current_index = 0
        self._log_timer = None
        self._upload_timer = None

    @property
    def carousel_items(self):
        return self._weather_entities
    
    def start_station(self):
        if Config.LOG_TO_CONSOLE and Config.LOG_INTERVAL:
            self._log_results()

        if Config.WEATHER_UPLOAD and Config.UPLOAD_INTERVAL:
            self._upload_results()

    def stop_station(self):
        if self._log_timer:
            self._log_timer.cancel()

        if self._upload_timer:
            self._upload_timer.cancel()

    def _log_results(self, first_time=True):
        if not first_time:
            print 'Async logging thread'

        self._log_timer = Timer(Config.LOG_INTERVAL, self._log_results, [False])
        self._log_timer.daemon = True
        self._log_timer.start()

    def _upload_results(self, first_time=True):
        if not first_time:
            print 'Async upload thread'

        self._upload_timer = Timer(Config.UPLOAD_INTERVAL, self._upload_results, [False])
        self._upload_timer.daemon = True
        self._upload_timer.start()

    def _get_cpu_temp(self):        
        # 'borrowed' from https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
        # executes a command at the OS to pull in the CPU temperature
        res = os.popen('vcgencmd measure_temp').readline()
        return float(res.replace('temp=', '').replace("'C\n", ''))

    def _celsius_to_fahrenheit(self, value):
        """Converts celsius temperature to fahrenheit"""
        return (value * 1.8) + 32
        

def c_to_f(input_temp):
    # convert input_temp from Celsius to Fahrenheit
    return (input_temp * 1.8) + 32


def get_cpu_temp():
    # 'borrowed' from https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
    # executes a command at the OS to pull in the CPU temperature
    res = os.popen('vcgencmd measure_temp').readline()
    return float(res.replace('temp=', '').replace("'C\n", ''))


# use moving average to smooth readings
def get_smooth(x):
    # do we have the t object?
    if not hasattr(get_smooth, 't'):
        # then create it
        get_smooth.t = [x, x, x]
    # manage the rolling previous values
    get_smooth.t[2] = get_smooth.t[1]
    get_smooth.t[1] = get_smooth.t[0]
    get_smooth.t[0] = x
    # average the three last temperatures
    xs = (get_smooth.t[0] + get_smooth.t[1] + get_smooth.t[2]) / 3
    return xs


def get_temp():
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
    t1 = sense.get_temperature_from_humidity()
    t2 = sense.get_temperature_from_pressure()
    # t becomes the average of the temperatures from both sensors
    t = (t1 + t2) / 2
    # Now, grab the CPU temperature
    t_cpu = get_cpu_temp()
    # Calculate the 'real' temperature compensating for CPU heating
    t_corr = t - ((t_cpu - t) / 1.5)
    # Finally, average out that value across the last three readings
    t_corr = get_smooth(t_corr)
    # convoluted, right?
    # Return the calculated temperature
    return t_corr


def main():
    global last_temp

    # initialize the lastMinute variable to the current time to start
    last_minute = datetime.datetime.now().minute
    # on startup, just use the previous minute as lastMinute
    last_minute -= 1
    if last_minute == 0:
        last_minute = 59

    # infinite loop to continuously check weather values
    while 1:
        # The temp measurement smoothing algorithm's accuracy is based
        # on frequent measurements, so we'll take measurements every 5 seconds
        # but only upload on measurement_interval
        current_second = datetime.datetime.now().second
        # are we at the top of the minute or at a 5 second interval?
        if (current_second == 0) or ((current_second % 5) == 0):
            # ========================================================
            # read values from the Sense HAT
            # ========================================================
            # calculate the temperature
            calc_temp = get_temp()
            # now use it for our purposes
            temp_c = round(calc_temp, 1)
            temp_f = round(c_to_f(calc_temp), 1)
            humidity = round(sense.get_humidity(), 0)
            # convert pressure from millibars to inHg before posting
            pressure = round(sense.get_pressure() * 0.0295300, 1)
            print 'Temp: %sF (%sC), Pressure: %s inHg, Humidity: %s%%' % (temp_f, temp_c, pressure, humidity)

            # get the current minute
            current_minute = datetime.datetime.now().minute
            # is it the same minute as the last time we checked?
            if current_minute != last_minute:
                # reset last_minute to the current_minute
                last_minute = current_minute
                # is minute zero, or divisible by 10?
                # we're only going to take measurements every MEASUREMENT_INTERVAL minutes
                if (current_minute == 0) or ((current_minute % Config.UPLOAD_INTERVAL) == 0):
                    # get the reading timestamp
                    now = datetime.datetime.now()
                    print '\n%d minute mark (%d @ %s)' % (Config.UPLOAD_INTERVAL, current_minute, str(now))
                    # did the temperature go up or down?
                    if last_temp != temp_f:
                        if last_temp > temp_f:
                            # display a blue, down arrow
                            sense.set_pixels(arrow_down)
                        else:
                            # display a red, up arrow
                            sense.set_pixels(arrow_up)
                    else:
                        # temperature stayed the same
                        # display red and blue bars
                        sense.set_pixels(bars)
                    # set last_temp to the current temperature before we measure again
                    last_temp = temp_f

                    # ========================================================
                    # Upload the weather data to Weather Underground
                    # ========================================================
                    # is weather upload enabled (True)?
                    if Config.WEATHER_UPLOAD:
                        # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol
                        print 'Uploading data to Weather Underground'
                        # build a weather data object
                        weather_data = {
                            'action': 'updateraw',
                            'ID': Config.STATION_ID,
                            'PASSWORD': Config.STATION_KEY,
                            'dateutc': 'now',
                            'tempf': str(temp_f),
                            'humidity': str(humidity),
                            'baromin': str(pressure),
                        }
                        try:
                            upload_url = Config.WU_URL + '?' + urlencode(weather_data)
                            response = urllib2.urlopen(upload_url)
                            html = response.read()
                            print 'Server response: %s' % html
                            # do something
                            response.close()  # best practice to close the file
                        except:
                            print 'Exception: %s\n' % sys.exc_info()[0]
                    else:
                        print 'Skipping Weather Underground upload'

        # wait a second then check again
        # You can always increase the sleep value below to check less often
        time.sleep(1)  # this should never happen since the above is an infinite loop

    print 'Leaving main()'

# ============================================================================
#  Read Weather Underground Configuration Parameters
# ============================================================================
print '\nInitializing Weather Underground configuration'
if (Config.STATION_ID is None) or (Config.STATION_KEY is None):
    print 'Missing values from the Weather Underground configuration file\n'
    sys.exit(1)

# make sure we don't have a MEASUREMENT_INTERVAL > 60
if (Config.UPLOAD_INTERVAL is None) or (Config.UPLOAD_INTERVAL > 60):
    print "The application's 'MEASUREMENT_INTERVAL' cannot be empty or greater than 60"
    sys.exit(1)

# we made it this far, so it must have worked...
print 'Successfully read Weather Underground configuration values'
print 'Station ID: %s' % Config.STATION_ID

# ============================================================================
# initialize the Sense HAT object
# ============================================================================
try:
    print 'Initializing the Sense HAT client'
    sense = SenseHat()
    # sense.set_rotation(180)
    # then write some text to the Sense HAT's 'screen'
    sense.show_message('Init', text_colour=[255, 255, 0], back_colour=[0, 0, 255])
    # clear the screen
    sense.clear()
    # get the current temp to use when checking the previous measurement
    print int(get_temp())
    print sense.get_pressure() / 1000
    last_temp = round(c_to_f(get_temp()), 1)
    print 'Current temperature reading: %s' % last_temp
except:
    print 'Unable to initialize the Sense HAT library: %s' % sys.exc_info()[0]
    sys.exit(1)

print 'Initialization complete!'

# Now see what we're supposed to do next
if __name__ == '__main__':
    try:
        station = WeatherStation()
        station.start_station()
        main()
    except KeyboardInterrupt:
        station.stop_station();
        print '\nExiting application\n'
        sys.exit(0)
