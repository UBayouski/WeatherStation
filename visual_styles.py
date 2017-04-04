from abc import ABCMeta, abstractmethod, abstractproperty

class VisualStyle(object):
    """description of class"""
    __metaclass__ = ABCMeta

    def __init__(self, positive_color, negative_color):
        self._e = (0, 0, 0) # no color for led

        self._p = positive_color
        self._n = negative_color

    @property
    def rotation(self):
        return 0

    @abstractmethod
    def apply_style(self, value):
        pass

class ArrowStyle(VisualStyle):

    def __init__(self, positive_color, negative_color):
        super(ArrowStyle, self).__init__(positive_color, negative_color)

        self._previous_value = 0

        self._arrow_up = (
            self._e, self._e, self._e, self._p, self._p, self._e, self._e, self._e, #0
            self._e, self._e, self._p, self._p, self._p, self._p, self._e, self._e, #1
            self._e, self._p, self._e, self._p, self._p, self._e, self._p, self._e, #2
            self._p, self._e, self._e, self._p, self._p, self._e, self._e, self._p, #3
            self._e, self._e, self._e, self._p, self._p, self._e, self._e, self._e, #4
            self._e, self._e, self._e, self._p, self._p, self._e, self._e, self._e, #5
            self._e, self._e, self._e, self._p, self._p, self._e, self._e, self._e, #6
            self._e, self._e, self._e, self._p, self._p, self._e, self._e, self._e  #7
        )

        self._arrow_down = tuple(self._n if pixel is self._p else self._e for pixel in self._arrow_up[::-1])

        self._equals = (
            self._e, self._e, self._e, self._e, self._e, self._e, self._e, self._e, #0
            self._e, self._e, self._e, self._e, self._e, self._e, self._e, self._e, #1
            self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p, #2
            self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p, #3
            self._n, self._n, self._n, self._n, self._n, self._n, self._n, self._n, #4
            self._n, self._n, self._n, self._n, self._n, self._n, self._n, self._n, #5
            self._e, self._e, self._e, self._e, self._e, self._e, self._e, self._e, #6
            self._e, self._e, self._e, self._e, self._e, self._e, self._e, self._e, #7
        )
    
    def apply_style(self, value):
        new_value = value
        new_value -= self._previous_value
        self._previous_value = value

        if not new_value:
            return self._equals

        return self._arrow_up if new_value > 0 else self._arrow_down

class NumericStyle(VisualStyle):
    
    def __init__(self, positive_color, negative_color):
        super(NumericStyle, self).__init__(positive_color, negative_color)

        self._empty_line = (self._e, self._e, self._e, self._e, self._e, self._e, self._e, self._e)
        self._dot_line = (self._e, self._e, self._e, self._e, self._e, self._e, self._e, self._p)
        self._numbers = {
            '0': (
                self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p,
                self._p, self._e, self._e, self._e, self._e, self._e, self._e, self._p,
                self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p,
            ),
            '1': (
                self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p,
                self._e, self._p, self._e, self._e, self._e, self._e, self._e, self._e,
                self._e, self._e, self._p, self._e, self._e, self._e, self._e, self._e,
            ),
            '2': (
                self._p, self._p, self._p, self._p, self._p, self._e, self._e, self._p,
                self._p, self._e, self._e, self._e, self._p, self._e, self._e, self._p,
                self._p, self._e, self._e, self._e, self._p, self._p, self._p, self._p,
            ),
            '3': (
                self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p,
                self._p, self._e, self._e, self._e, self._p, self._e, self._e, self._p,
                self._p, self._e, self._e, self._e, self._p, self._e, self._e, self._p,
            ),
            '4': (
                self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p,
                self._e, self._e, self._e, self._e, self._p, self._e, self._e, self._e,
                self._p, self._p, self._p, self._p, self._p, self._e, self._e, self._e,
            ),
            '5': (
                self._p, self._e, self._e, self._e, self._p, self._p, self._p, self._p,
                self._p, self._e, self._e, self._e, self._p, self._e, self._e, self._p,
                self._p, self._p, self._p, self._p, self._p, self._e, self._e, self._p,
            ),
            '6': (
                self._p, self._e, self._e, self._e, self._p, self._p, self._p, self._p,
                self._p, self._e, self._e, self._e, self._p, self._e, self._e, self._p,
                self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p,
            ),
            '7': (
                self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p,
                self._p, self._e, self._e, self._e, self._e, self._e, self._e, self._e,
                self._p, self._e, self._e, self._e, self._e, self._e, self._e, self._e,
            ),
            '8': (
                self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p,
                self._p, self._e, self._e, self._e, self._p, self._e, self._e, self._p,
                self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p,
            ),
            '9': (
                self._p, self._p, self._p, self._p, self._p, self._p, self._p, self._p,
                self._p, self._e, self._e, self._e, self._p, self._e, self._e, self._p,
                self._p, self._p, self._p, self._p, self._p, self._e, self._e, self._p,
            )
        }

    @property
    def rotation(self):
        return 90

    def apply_style(self, value):
        str_value = str(abs(int(value)))

        if len(str_value) == 2:
            result = list(self._numbers[str_value[1]]) #0-2
            result += self._empty_line * 2             #3-4
            result += self._numbers[str_value[0]]      #5-7
        else:
            result = list(self._empty_line * 2)        #0-1
            result += self._numbers[str_value]         #2-4
            result += self._empty_line * 3             #5-7

        if value <= 0:
            result = tuple(self._n if pixel is self._p else self._e for pixel in result)

        return result
            

class SquareStyle(VisualStyle):
    def __init__(self, positive_color, negative_color):
        super(SquareStyle, self).__init__(positive_color, negative_color)

    def apply_style(self, value):
        if value > 0:
            return tuple(self._p if i < value else self._n for i in range(64))

        return tuple(self._n if i < -value else self._p for i in range(64))
