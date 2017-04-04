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

class WeatherEntityType(object):
    HUMIDITY, PRESSURE, TEMPERATURE = range(3)

class WeatherEntity(CarouselContainer):
    __metaclass__ = ABCMeta

    def __init__(self):
        super(WeatherEntity, self).__init__()

        self._visual_styles = (
            NumericStyle(self.positive_color, self.negative_color),
            ArrowStyle(self.positive_color, self.negative_color),
            SquareStyle(self.positive_color, self.negative_color)
        )

    @abstractproperty
    def entity_messsage(self):
        pass

    @abstractproperty
    def positive_color(self):
        pass

    @abstractproperty
    def negative_color(self):
        pass

    @abstractproperty
    def entity_type(self):
        pass

    @property
    def carousel_items(self):
        return self._visual_styles

    @property
    def current_style(self):
        return self.current_item

    def show_pixels(self, value):
        return self.current_item.apply_style(value)

class HumidityEntity(WeatherEntity):

    def __init__(self):
        super(HumidityEntity, self).__init__()

    @property
    def entity_messsage(self):
        return 'Humidity'

    @property
    def positive_color(self):
        return Config.HUM_POSITIVE

    @property
    def negative_color(self):
        return Config.HUM_NEGATIVE

    @property
    def entity_type(self):
        return WeatherEntityType.HUMIDITY

    def show_pixels(self, value):
        if self.current_style is SquareStyle:
            value = 64 * value / 100

        return super(HumidityEntity, self).show_pixels(value)

class PressureEntity(WeatherEntity):

    def __init__(self):
        super(PressureEntity, self).__init__()
    
    @property
    def entity_messsage(self):
        return 'Pressure'

    @property
    def positive_color(self):
        return Config.PRESS_POSITIVE

    @property
    def negative_color(self):
        return Config.PRESS_NEGATIVE

    @property
    def entity_type(self):
        return WeatherEntityType.PRESSURE

class TemperatureEntity(WeatherEntity):

    def __init__(self):
        super(TemperatureEntity, self).__init__()
    
    @property
    def entity_messsage(self):
        return 'Temperature'

    @property
    def positive_color(self):
        return Config.TEMP_POSITIVE

    @property
    def negative_color(self):
        return Config.TEMP_NEGATIVE

    @property
    def entity_type(self):
        return WeatherEntityType.TEMPERATURE

# Predefined weather entities tuple
DEFAULT_WEATHER_ENTITIES = (TemperatureEntity(), HumidityEntity(), PressureEntity())
