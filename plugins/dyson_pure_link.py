import base64, json, hashlib, os, time
import paho.mqtt.client as mqtt
from Queue import Queue, Empty

from base_plugin import BasePlugin

"""Mappings and enums like"""

# Map for connection return code and its meaning
CONNECTION_STATE = {
    0: 'Connection successful',
    1: 'Connection refused: incorrect protocol version',
    2: 'Connection refused: invalid client identifier',
    3: 'Connection refused: server unavailable',
    4: 'Connection refused: bad username or password',
    5: 'Connection refused: not authorised',
    99: 'Connection refused: timeout'
}

DISCONNECTION_STATE = {
    0: 'Disconnection successful',
    50: 'Disconnection error: unexpected error',
    99: 'Disconnection error: timeout'
}

class FanMode(object):
    """Enum for fan mode"""

    OFF = 'OFF'
    FAN = 'FAN'
    AUTO = 'AUTO'

class StandbyMonitoring(object):
    """Enum for monitor air quality when on standby"""

    ON = 'ON'
    OFF = 'OFF'

"""Custom Errors"""

class ConnectionError(Exception):
    """Custom error to handle connect device issues"""

    def __init__(self, return_code, *args):
        super(ConnectionError, self).__init__(*args)
        self.message = CONNECTION_STATE[return_code]

class DisconnectionError(Exception):
    """Custom error to handle disconnect device issues"""
    def __init__(self, return_code, *args):
        super(DisconnectionError, self).__init__(*args)
        self.message = DISCONNECTION_STATE[return_code] if return_code in DISCONNECTION_STATE else DISCONNECTION_STATE[50]

class DataRetrieveError(Exception):
    """Custom error to handle retrieve data from device"""
    def __init__(self, *args):
        super(DataRetrieveError, self).__init__(*args)
        self.message = 'Could not get state/sensors data'

"""Value types to be data containers"""

class SensorsData(object):
    """Value type for sensors data"""

    def __init__(self, message):
        data = message['data']
        humidity = data['hact']
        temperature = data['tact']
        volatile_compounds = data['vact']

        self.humidity = None if humidity == 'OFF' else int(humidity)
        self.temperature = None if temperature == 'OFF' else self.kelvin_to_fahrenheit(float(temperature) / 10)
        self.volatile_compounds = 0 if volatile_compounds == 'INIT' else int(volatile_compounds)
        self.particles = int(data['pact'])

    def __repr__(self):
        """Return a String representation"""
        return 'Temperature: {0} F, Humidity: {1} %, Volatile Compounds: {2}, Particles: {3}'.format(
            self.temperature, self.humidity, self.volatile_compounds, self.particles)

    @property
    def has_data(self):
        return self.temperature is not None or self.humidity is not None

    @staticmethod
    def is_sensors_data(message):
        return message['msg'] in ['ENVIRONMENTAL-CURRENT-SENSOR-DATA']

    @staticmethod
    def kelvin_to_fahrenheit (kelvin_value):
        return round(kelvin_value * 9 / 5 - 459.67, 2)

class StateData(object):
    """Value type for state data"""

    def __init__(self, message):
        data = message['product-state']

        self.fan_mode = self._get_field_value(data['fmod'])
        self.fan_state = self._get_field_value(data['fnst'])
        self.night_mode = self._get_field_value(data['nmod'])
        self.speed = self._get_field_value(data['fnsp'])
        self.oscillation = self._get_field_value(data['oson'])
        self.filter_life = self._get_field_value(data['filf'])
        self.quality_target = self._get_field_value(data['qtar'])
        self.standby_monitoring = self._get_field_value(data['rhtm'])

    def __repr__(self):
        """Return a String representation"""
        return 'Fan mode: {0}, Oscillation: {1}, Filter life: {2}, Standby monitoring: {3}'.format(
            self.fan_mode, self.oscillation, self.filter_life, self.standby_monitoring)

    @staticmethod
    def _get_field_value(field):
        """Get field value"""
        return field[-1] if isinstance(field, list) else field

    @staticmethod
    def is_state_data(message):
        return message['msg'] in ['CURRENT-STATE', 'STATE-CHANGE']

class DysonPureLink(BasePlugin):
    """Plugin to connect to Dyson Pure Link device and get its sensors readings"""

    def __init__(self):
        super(DysonPureLink, self).__init__(self)

        self.client = None
        self.connected = Queue()
        self.disconnected = Queue()
        self.state_data_available = Queue()
        self.sensor_data_available = Queue()
        self.sensor_data = None
        self.state_data = None

        # In case sensors were disabled we upload previous readings
        # Required for Weather Underground data consistency
        self.previous_data = None

    @property
    def plugin_name(self):
       return 'Dyson Pure Link Plugin'

    @property
    def has_valid_data(self):
        return self.sensor_data and self.sensor_data.has_data

    @property
    def config_file_name(self):
        return '{}/dyson_pure_link.yaml'.format(os.path.dirname(os.path.abspath(__file__)))

    @property
    def password(self):
        return self.config['DYSON_PASSWORD']

    @property
    def serial_number(self):
        return self.config['DYSON_SERIAL']

    @property
    def device_type(self):
        return self.config['DYSON_TYPE']

    @property
    def ip_address(self):
        return self.config['DYSON_IP']

    @property
    def port_number(self):
        return self.config['DYSON_PORT']

    @property
    def device_command(self):
        return '{0}/{1}/command'.format(self.device_type, self.serial_number)

    @property
    def device_status(self):
        return '{0}/{1}/status/current'.format(self.device_type, self.serial_number)

    @staticmethod
    def on_connect(client, userdata, flags, return_code):
        """Static callback to handle on_connect event"""
        # Connection is successful with return_code: 0
        if return_code:
            userdata.connected.put_nowait(False)
            self.errors.append(ConnectionError(return_code))

        # We subscribe to the status message
        client.subscribe(userdata.device_status)
        userdata.connected.put_nowait(True)

    @staticmethod
    def on_disconnect(client, userdata, return_code):
        """Static callback to handle on_disconnect event"""
        if return_code:
            self.errors.append(DisconnectionError(return_code))
            userdata.disconnected.put_nowait(False)

        userdata.disconnected.put_nowait(True)

    @staticmethod
    def on_message(client, userdata, message):
        """Static callback to handle incoming messages"""
        payload = message.payload.decode("utf-8")
        json_message = json.loads(payload)
        
        if StateData.is_state_data(json_message):
            userdata.state_data_available.put_nowait(StateData(json_message))

        if SensorsData.is_sensors_data(json_message):
            userdata.sensor_data_available.put_nowait(SensorsData(json_message))

    def _request_state(self):
        """Publishes request for current state message"""
        if self.client:
            command = json.dumps({
                    'msg': 'REQUEST-CURRENT-STATE',
                    'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
            
            self.client.publish(self.device_command, command)

    def _change_state(self, data):
        """Publishes request for change state message"""
        if self.client:
            
            command = json.dumps({
                'msg': 'STATE-SET',
                'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'mode-reason': 'LAPP',
                'data': data
            })

            self.client.publish(self.device_command, command, 1)

            try:
                self.state_data = self.state_data_available.get(timeout=5)
            except Empty:
                self.errors.append(DataRetrieveError())

    def _hashed_password(self):
        """Hash password (found in manual) to a base64 encoded of its shad512 value"""
        hash = hashlib.sha512()
        hash.update(self.password.encode('utf-8'))
        return base64.b64encode(hash.digest()).decode('utf-8')
        

    def connect_device(self):
        """
        Connects to device using provided connection arguments

        Returns: True/False depending on the result of connection
        """
        if not self.config:
            self.parse_config()

        self.client = mqtt.Client(clean_session=True, protocol=mqtt.MQTTv311, userdata=self)
        self.client.username_pw_set(self.serial_number, self._hashed_password())
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.connect(self.ip_address, port=self.port_number)
        self.client.loop_start()

        try:
            if self.connected.get(timeout=10):
                self._request_state()

                try:
                    self.state_data = self.state_data_available.get(timeout=5)
                    self.sensor_data = self.sensor_data_available.get(timeout=5)

                    # Return True in case of successful connect and data retrieval
                    return True
                except Empty:
                    self.errors.append(DataRetrieveError())
        except Empty:
            self.errors.append(ConnectionError(99))

        # If any issue occurred return False
        self.client = None
        return False

    def set_fan_mode(self, mode):
        """Changes fan mode: ON|OFF|AUTO"""
        self._change_state({'fmod': mode})

    def set_standby_monitoring(self, mode):
        """Changes standby monitoring: ON|OFF"""
        self._change_state({'rhtm': mode})

    def get_data(self):
        result = {}

        if self.connect_device():
            if self.has_valid_data:
                # Dictionary data for Weather Underground upload  
                if self.sensor_data.temperature is not None:
                    result['indoortempf'] = self.sensor_data.temperature

                if self.sensor_data.humidity is not None:
                    result['indoorhumidity'] = self.sensor_data.humidity
                
                # Update previous readings value
                self.previous_data = result
            else:
                # If humidity and temperature are None, return previous value
                result = self.previous_data

        self.disconnect_device()

        return result

    def disconnect_device(self):
        """Disconnects device and return the boolean result"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            
            # Wait until we get on disconnect message
            try:
                return self.disconnected.get(timeout=5)
            except Empty:
                self.errors.append(DisconnectionError(99))
                return False
