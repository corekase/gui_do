from pygame import Rect
from typing import Callable, Hashable, Optional, TYPE_CHECKING
from ..utility.constants import WidgetKind, ButtonStyle
from .button import Button

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager

class ArrowBox(Button):
    def __init__(self, gui: "GuiManager", id: Hashable, rect: Rect, direction: float, callback: Optional[Callable[[], None]] = None) -> None:
        # initialize common widget values, skipping the button factory with the True
        super().__init__(gui, id, rect, ButtonStyle.Box, None, callback, True)
        self.WidgetKind = WidgetKind.ArrowBox
        self.idle, self.hover, self.armed = self.gui.bitmap_factory.draw_arrow_state_bitmaps(rect, direction)
