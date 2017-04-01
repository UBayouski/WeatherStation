from sense_hat import SenseHat  
from signal import pause
sense = SenseHat()  

  
x = 3  
y = 3  
  
def draw_dot():  
 sense.clear()  
 sense.set_pixel(x,y,255,90,90)  
  
def pushed_up():  
 global y  
 y = y - 1  
 if y < 0:  
  y = 0  
 draw_dot()  
  
def pushed_down():  
 global y  
 y = y + 1  
 if y > 7:  
  y = 7  
 draw_dot()  
  
def pushed_left():  
 global x  
 x = x - 1  
 if x < 0:  
  x = 0  
 draw_dot()  
  
def pushed_right():  
 global x  
 x = x + 1  
 if x > 7:  
  x = 7  
 draw_dot()  
  
sense.stick.direction_up = pushed_up  
sense.stick.direction_down = pushed_down  
sense.stick.direction_left = pushed_left  
sense.stick.direction_right = pushed_right  
  
draw_dot()  
pause()