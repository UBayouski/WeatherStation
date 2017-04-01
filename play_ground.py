import sys, getopt
from signal import pause
from sense_hat import SenseHat

from visual_styles import ArrowStyle, SquareStyle, NumericStyle, VisualStyle

red = [255, 0, 0]
blue = [0, 0, 255]
black = [0, 0, 0]
num = [
    red, black, red, black, black, red, red, red,
    red, black, red, black, black, red, black, red,
    red, black, red, black, black, red, black, red,
    red, black, red, black, black, red, black, red,
    red, red, red, black, black, red, black, red,
    black, black, red, black, black, red, black, red,
    black, black, red, black, black, red, black, red,
    black, black, red, black, black, red, red, red,
]
num1 = [
    black, black, red, black, black, red, red, red,
    black, red, red, black, black, red, black, red,
    red, black, red, black, black, red, black, red,
    black, black, red, black, black, red, black, red,
    black, black, red, black, black, red, black, red,
    black, black, red, black, black, red, black, red,
    black, black, red, black, black, red, black, red,
    black, black, red, black, black, red, red, red,
]

t = [
    red, red, red, red, red, red, red, red,
    red, black,  black, black,  black, black,  black, red,
    red, red, red, red, red, red, red, red
]
t1 = [
    black, black,  black, black,  black, black,  black, black
]
t3 = [
    red, red, red, red, red, red, red, red,
    black, red, black, black, black, black, black, black,
    black, black, red, black, black, black, black, black
]

def main():
    opts, args = getopt.getopt(sys.argv[1:],"tnn1TVl:")
    sense = SenseHat()
    for opt, arg in opts:
        if opt == '-l':
            sense.show_letter(arg, red)
    if '-t' in sys.argv:
        temp = 36
        pixels = [red if temp > i else blue for i in range(64)]
        sense.set_pixels(pixels)
    elif '-n' in sys.argv:
        sense.set_pixels(num)
    elif '-n1' in sys.argv:
        sense.set_pixels(num1)
    elif '-T' in sys.argv:
        sense.rotation = 90
        newT = list(t1)
        newT.extend(t)
        newT.extend(t1)
        newT.extend(t3)
        print len(newT)
        sense.set_pixels(newT)
    elif '-V' in sys.argv:
        a = NumericStyle((255, 0, 0), (0, 0, 255))
        sense.rotation = a.rotation
        sense.set_pixels(a.show(9.9))
        
    sense.stick.direction_up = up
    sense.stick.direction_down = down  
    sense.stick.direction_left = left  
    sense.stick.direction_right = right  

def up():
    print 'up'
def down():
    print 'down'
def left():
    print 'left'
def right():
    print 'right'

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print '\nExiting application\n'
        sys.exit(0)
    pause()