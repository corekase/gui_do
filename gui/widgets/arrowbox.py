# a box that displays a triangle graphic pointing at an angle.  Up, Down, Left, and Right presets
# are built in.  Or pass a degree between 0 and 360 during initialization
#
# this widget will be used for scrollbar buttons controlling the bar
#
# arrows are always in a square area, so if the rect isn't square then the drawn arrow area will be the
# smaller dimension, either horizontal or vertical, squared, centered in the rect
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..guimanager import GuiManager
from ..utility import convert_to_window
from ..bitmapfactory import BitmapFactory
from .button import Button, State

class ArrowBox(Button):
    def __init__(self, id, rect, direction):
        # initialize common widget values
        super().__init__(id, rect, None)
        factory = BitmapFactory()
        self.idle, self.hover, self.armed = factory.draw_arrow_state_bitmaps(rect, direction)
        self.state = State.Idle

    def handle_event(self, event, window):
        super().handle_event(event, window)

    def leave(self):
        super().leave()

    def draw(self):
        super().draw()
