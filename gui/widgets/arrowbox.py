# a box that displays a triangle graphic pointing at an angle.  Up, Down, Left, and Right presets
# are built in.  Or pass a degree between 0 and 360 during initialization
#
# this widget will be used for scrollbar buttons controlling the bar
#
# arrows are always in a square area, so if the rect isn't square then the drawn arrow area will be the
# smaller dimension, either horizontal or vertical, squared, centered in the rect
#
# To-do: the arrowbox can have a repeating signal or callback by tracking time in it, and when the interval
# is reached then signal the widget
from ..bitmapfactory import BitmapFactory
from .button import Button

class ArrowBox(Button):
    def __init__(self, id, rect, direction, callback=None):
        # initialize common widget values, skipping the button factory with the True
        super().__init__(id, rect, None, callback, True)
        factory = BitmapFactory()
        self.idle, self.hover, self.armed = factory.draw_arrow_state_bitmaps(rect, direction)

    def handle_event(self, event, window):
        super().handle_event(event, window)
        # here is where it implement repeating
        # if event.button = 1, do the timing logic

    def leave(self):
        super().leave()

    def draw(self):
        super().draw()
