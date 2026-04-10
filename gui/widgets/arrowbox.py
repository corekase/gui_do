from ..bitmapfactory import BitmapFactory
from ..constants import GType
from .button import Button

class ArrowBox(Button):
    def __init__(self, id, rect, direction, callback=None):
        # initialize common widget values, skipping the button factory with the True
        super().__init__(id, rect, 1, None, callback, True)
        self.GType = GType.Arrowbox
        factory = BitmapFactory()
        self.idle, self.hover, self.armed = factory.draw_arrow_state_bitmaps(rect, direction)

    def handle_event(self, event, window):
        super().handle_event(event, window)

    def leave(self):
        super().leave()

    def draw(self):
        super().draw()
