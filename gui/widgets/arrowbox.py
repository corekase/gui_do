from ..values.constants import WidgetKind, ButtonStyle
from .button import Button
from .utility.registry import register_widget

@register_widget("ArrowBox")
class ArrowBox(Button):
    def __init__(self, gui, id, rect, direction, callback=None):
        # initialize common widget values, skipping the button factory with the True
        super().__init__(gui, id, rect, ButtonStyle.Box, None, callback, True)
        self.WidgetKind = WidgetKind.ArrowBox
        self.idle, self.hover, self.armed = self.gui.bitmap_factory.draw_arrow_state_bitmaps(rect, direction)
