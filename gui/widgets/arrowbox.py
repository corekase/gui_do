from ..constants import GType, BStyle
from .button import Button
from ..widgets.registry import register_widget

@register_widget("ArrowBox")
class ArrowBox(Button):
    def __init__(self, gui, id, rect, direction, callback=None):
        # initialize common widget values, skipping the button factory with the True
        super().__init__(gui, id, rect, BStyle.Box, None, callback, True)
        self.GType = GType.Arrowbox
        factory = self.gui.get_bitmapfactory()
        self.idle, self.hover, self.armed = factory.draw_arrow_state_bitmaps(rect, direction)

    def handle_event(self, event, window):
        super().handle_event(event, window)

    def leave(self):
        super().leave()

    def draw(self):
        super().draw()
