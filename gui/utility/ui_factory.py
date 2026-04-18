from typing import Callable, Optional, TYPE_CHECKING, Tuple, Union

from pygame import Rect

from .events import ArrowPosition, BaseEvent, ButtonStyle, Orientation
from ..widgets.arrowbox import ArrowBox as gArrowBox
from ..widgets.button import Button as gButton
from ..widgets.buttongroup import ButtonGroup as gButtonGroup
from ..widgets.canvas import Canvas as gCanvas
from ..widgets.frame import Frame as gFrame
from ..widgets.image import Image as gImage
from ..widgets.label import Label as gLabel
from ..widgets.scrollbar import Scrollbar as gScrollbar
from ..widgets.toggle import Toggle as gToggle
from ..widgets.window import Window as gWindow

if TYPE_CHECKING:
    from .gui_manager import GuiManager


class GuiUiFactory:
    """Owns GUI widget/window construction helper methods."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager
        self._label_sequence: int = 0

    def arrow_box(self, id: str, rect: Rect, direction: float, on_activate: Optional[Callable[[], None]] = None) -> gArrowBox:
        return self.gui.add(gArrowBox(self.gui, id, rect, direction, on_activate))

    def button(self, id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None) -> gButton:
        safe_text = '' if text is None else text
        return self.gui.add(gButton(self.gui, id, rect, style, safe_text, on_activate))

    def button_group(self, group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> gButtonGroup:
        return self.gui.add(gButtonGroup(self.gui, group, id, rect, style, text))

    def canvas(self, id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> gCanvas:
        return self.gui.add(gCanvas(self.gui, id, rect, backdrop, on_activate, automatic_pristine))

    def frame(self, id: str, rect: Rect) -> gFrame:
        return self.gui.add(gFrame(self.gui, id, rect))

    def image(self, id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> gImage:
        return self.gui.add(gImage(self.gui, id, rect, image, automatic_pristine, scale))

    def label(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False, id: Optional[str] = None) -> gLabel:
        if id is None:
            self._label_sequence += 1
            id = f'label_{self._label_sequence}'
        return self.gui.add(gLabel(self.gui, id, position, text, shadow))

    def scrollbar(self, id: str, overall_rect: Rect, horizontal: Orientation, style: ArrowPosition, params: Tuple[int, int, int, int]) -> gScrollbar:
        return self.gui.add(gScrollbar(self.gui, id, overall_rect, horizontal, style, params))

    def toggle(self, id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> gToggle:
        return self.gui.add(gToggle(self.gui, id, rect, style, pushed, pressed_text, raised_text))

    def window(
        self,
        title: str,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        backdrop: Optional[str] = None,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> gWindow:
        return self.gui.add(gWindow(self.gui, title, pos, size, backdrop, preamble, event_handler, postamble))
