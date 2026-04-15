from typing import Any, Optional, Callable
from ..utility.constants import WidgetKind, ButtonStyle
from .button import Button

class ArrowBox(Button):
    def __init__(self, gui: Any, id: Any, rect: Any, direction: float, callback: Optional[Callable] = None) -> None:
        # initialize common widget values, skipping the button factory with the True
        super().__init__(gui, id, rect, ButtonStyle.Box, None, callback, True)
        self.WidgetKind = WidgetKind.ArrowBox
        self.idle, self.hover, self.armed = self.gui.bitmap_factory.draw_arrow_state_bitmaps(rect, direction)
