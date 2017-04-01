from abc import ABCMeta, abstractmethod, abstractproperty

from config import Config
from visual_styles import ArrowStyle, NumericStyle, SquareStyle, VisualStyle

class CarouselContainer(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.current_index = 0

    @abstractproperty
    def carousel_items(self):
        pass
   
    @property
    def next_item(self):
        if self.current_index < len(self.carousel_items) - 1:
            self.current_index += 1
        else:
            self.current_index = 0
            
        return self.current_item

    @property
    def previous_item(self):
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.carousel_items) - 1
            
        return self.current_item

    @property
    def current_item(self):
        return self.carousel_items[self.current_index]


class WeatherEntity(CarouselContainer):
    __metaclass__ = ABCMeta

    def __init__(self):
        super(WeatherEntity, self).__init__()

    def __init__(self):
        self._visual_styles = (
            ArrowStyle(self.positive_color, self.negative_color), 
            NumericStyle(self.positive_color, self.negative_color), 
            SquareStyle(self.positive_color, self.negative_color)
        )
        self._current_style_index = 0

    @abstractproperty
    def entity_messsage(self):
        pass

    @abstractproperty
    def positive_color(self):
        pass

    @abstractproperty
    def negative_color(self):
        pass

    @property
    def carousel_items(self):
        return self._visual_styles
   
    @property
    def next_style(self):
        if self._current_style_index < len(self._visual_styles) - 1:
            self._current_style_index += 1
        else:
            self._current_style_index = 0
            
        return self.current_style

    @property
    def previous_style(self):
        if self._current_style_index > 0:
            self._current_style_index -= 1
        else:
            self._current_style_index = len(self._visual_styles) - 1
            
        return self.current_style

    @property
    def current_style(self):
        return self._visual_styles[self._current_style_index]

class HumidityEntity(WeatherEntity):
    
    @property
    def entity_messsage(self):
        return 'Humidity'

    @property
    def positive_color(self):
        return Config.HUM_POSITIVE

    @property
    def negative_color(self):
        return Config.HUM_NEGATIVE

class PressureEntity(WeatherEntity):
    
    @property
    def entity_messsage(self):
        return 'Pressure'

    @property
    def positive_color(self):
        return Config.PRESS_POSITIVE

    @property
    def negative_color(self):
        return Config.PRESS_NEGATIVE

class TemperatureEntity(WeatherEntity):
    
    @property
    def entity_messsage(self):
        return 'Temperature'

    @property
    def positive_color(self):
        return Config.TEMP_POSITIVE

    @property
    def negative_color(self):
        return Config.PRESS_NEGATIVE

# Predefined weather entities tuple
DEFAULT_WEATHER_ENTITIES = (TemperatureEntity(), HumidityEntity(), PressureEntity())
