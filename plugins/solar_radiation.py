"""Solar Radiation Calculation Logic"""

import datetime, dateutil.parser, json, math, os, pytz, urllib, yaml
from base_plugin import BasePlugin

class SolarRadiation(BasePlugin):
    """Plugin to calculate solar radiation by provided latitude"""

    def __init__(self):
        super(SolarRadiation, self).__init__(self)
        self.sunrise = None
        self.sunset = None

        self._timezone = None
        self._today = None

    @property
    def plugin_name(self):
       return 'Calculate Solar Radiation Plugin'

    @property
    def has_valid_data(self):
        return self.config and self.sunrise and self.sunset

    @property
    def config_file_name(self):
        return '{}/solar_radiaton.yaml'.format(os.path.dirname(os.path.abspath(__file__)))

    @property
    def is_date_today(self):
        """Checks if date is the same as plugin has at start"""
        return self.today == self.current_date.date()

    @property
    def timezone(self):
        """Checks if timezone was populated otherwise loads it from config"""
        if not self._timezone:
            self._timezone = pytz.timezone(self.config['TIME_ZONE'] or pytz.utc)
        
        return self._timezone

    @property
    def today(self):
        """Populates initial today's date"""
        if not self._today:
            self._today = self.current_date.date()
        
        return self._today

    @property
    def current_date(self):
        """Get currents date for provided timezone"""
        return datetime.datetime.now(tz=self.timezone)

    @property
    def current_hour(self):
        """Gets current hour and minutes as float result"""
        current_time =  self.current_date.time()
        return current_time.hour + current_time.minute / 60.0

    @property
    def is_day(self):
        """Checks if currently is a day time"""
        return self.sunrise <= self.current_date <= self.sunset

    @property
    def day_of_year(self):
        """Gets day of year"""
        return self.current_date.timetuple().tm_yday

    @property
    def sunrise_sunset_url(self):
        """Returns link for Sunrise/Sunset API with provided latitude and longitude"""
        return 'https://api.sunrise-sunset.org/json?lat={0}&lng={1}&date=today&formatted=0'.format(self.latitude, self.config['LONGITUDE'])

    @property
    def latitude(self):
        """Returns latitude from config"""
        return self.config['LATITUDE'] if self.config else None

    @staticmethod
    def declination_angle(day):
        """Declination's angle is measured north or south of the celestial equator, along the hour circle passing through the point in question.

        The declination angle, varies seasonally due to the tilt of the Earth on its axis of rotation and the rotation of the Earth around the sun.
        http://www.pveducation.org/pvcdrom/properties-of-sunlight/declination-angle

        Args:
            day (number): day of year

        Returns:
            float: declination angle degrees
        """
        return 23.45 * math.sin(math.radians(360.0 / 365 * (day - 81)))

    @staticmethod
    def air_mass(hour, day, latitude):
        """The Air Mass is the path length which light takes through the atmosphere normalized to the shortest possible path length. 

        The Air Mass quantifies the reduction in the power of light as it passes through the atmosphere and is absorbed by air and dust. 
        http://www.pveducation.org/pvcdrom/properties-of-sunlight/air-mass

        Args:
            hour (float): local solar time
            day (number): day of year
            latitude (float): latitude value between -90 and 90 degrees

        Returns:
            float: path length which light takes through the atmosphere
        """
        declination_angle = math.radians(SolarRadiation.declination_angle(day));
        hour_angle = math.radians(SolarRadiation.hour_angle(hour));
        elevation_angle = SolarRadiation.elevation_angle(hour_angle, declination_angle, latitude)
        declanation = math.radians(90) - elevation_angle;
        return 1 / (1E-4 + math.cos(declanation))

    @staticmethod
    def hour_angle(hour):
        """The Hour Angle converts the local solar time (LST) into the number of degrees which the sun moves across the sky.
 
        By definition, the Hour Angle is 0 at solar noon. Since the Earth rotates 15 per hour,
        each hour away from solar noon corresponds to an angular motion of the sun in the sky of 15.
        In the morning the hour angle is negative, in the afternoon the hour angle is positive.
        https://www.pveducation.org/pvcdrom/2-properties-sunlight/solar-time

        Args:
            hour (float): local solar time

        Returns:
            float: number of degrees which the sun moves across the sky
        """
        return 15 * (hour - 12);

    @staticmethod
    def elevation_angle(hour_angle, declanation_angle, latitude):
        """The elevation angle (used interchangeably with altitude angle) is the angular height of the sun in the sky measured from the horizontal.

        http://www.pveducation.org/pvcdrom/properties-of-sunlight/elevation-angle
        Args:
            hour_angle (float): hour angle in radians
            declanation_angle(float): declanation angle in radians
            latitude (float): latitude value between -90 and 90 degrees
        Returns:
            float: elevation angle in radians
        """
        return math.asin(math.sin(declanation_angle) * math.sin(latitude) + math.cos(declanation_angle) * math.cos(latitude) * math.cos(hour_angle))

    def get_sunrise_sunset(self):
        """Gets sunrise and sunset from API by provided latitude and longitude.

        If date is the same, sunrise and sunset values are set return existing values, without calling API.

        Returns:
            tuple: sunrise and sunset in timezone provided in config
        """
        if (self.config and (not self.sunrise or not self.sunset or not self.is_date_today)):
            self._today = self.current_date.date()
            try:
                response = urllib.urlopen(self.sunrise_sunset_url)
                data = json.loads(response.read())
                result = data['results']
                sunrise = result['sunrise']
                sunset = result['sunset']

                # Convert to provided in config timezone, as API returns in UTC by default
                self.sunrise = dateutil.parser.parse(sunrise).astimezone(self.timezone)
                self.sunset = dateutil.parser.parse(sunset).astimezone(self.timezone)
            except Exception as error:
                self.errors.append(error)
        
        return (self.sunrise, self.sunset)

    def calcluate_solar_radiation(self):
        """Calculates current date and time solar radiation.

        http://www.pveducation.org/pvcdrom/properties-of-sunlight/calculation-of-solar-insolation

        Returns:
            float: solar radiation in W/m2
        """
        if (self.config):
            self.get_sunrise_sunset()

            if self.is_day:
                air_mass = SolarRadiation.air_mass(self.current_hour, self.day_of_year, self.latitude)
                result = math.pow(0.7, air_mass)
                result = 1353 * math.pow(result, 0.678)

                # We ignore case more than 1100 W/m2, because the peak solar radiation is 1 kW/m2
                # http://www.pveducation.org/pvcdrom/average-solar-radiation
                return 0 if result > 1100 else result

        return None

    def get_data(self):
        result = {}

        if not self.config:
            self.parse_config()

        # Dictionary data for Weather Underground upload
        if self.has_valid_data:
            solar_radiation = self.calcluate_solar_radiation()
            if solar_radiation is not None:
                result['solarradiation'] = solar_radiation

        return result
