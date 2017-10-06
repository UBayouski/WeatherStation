from abc import ABCMeta, abstractmethod, abstractproperty
import os, yaml

class BasePlugin(object):
    """
    Base class for plugin like classes.
    
    These classes contain logic to connect and get data from additional sources (smart devices, sensors, etc.).
    """
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        # Parsed to dictionary config file
        self.config = None

        # List of errors occured
        self.errors = []

    @abstractproperty
    def plugin_name(self):
        """Returns plugin name"""
        pass

    @abstractproperty
    def has_valid_data(self):
        """Returns if data is valid"""
        pass

    @abstractproperty
    def config_file_name(self):
        """Returns config file name, should return None if no config file"""
        pass

    @abstractmethod
    def get_data(self):
        """Gets valid data for plugin, should return empty dictionary if no data"""
        pass

    def parse_config(self):
        """Parses config file if any"""
        if self.config_file_name and os.path.isfile(self.config_file_name):
            self.config = yaml.safe_load(open(self.config_file_name))