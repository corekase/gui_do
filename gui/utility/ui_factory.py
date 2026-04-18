from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING, Tuple, Union

from pygame import Rect

from .events import ArrowPosition, BaseEvent, ButtonStyle, Orientation
from ..widgets.arrowbox import ArrowBox
from ..widgets.button import Button
from ..widgets.buttongroup import ButtonGroup
from ..widgets.canvas import Canvas
from ..widgets.frame import Frame
from ..widgets.image import Image
from ..widgets.label import Label
from ..widgets.scrollbar import Scrollbar
from ..widgets.toggle import Toggle
from ..widgets.window import Window

if TYPE_CHECKING:
    from .gui_manager import GuiManager


class GuiUiFactory:
    """Owns GUI widget/window construction helper methods."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Bind widget/window construction helpers to a GUI manager."""
        self.gui: "GuiManager" = gui_manager
        self._label_sequence: int = 0

    def arrow_box(self, id: str, rect: Rect, direction: float, on_activate: Optional[Callable[[], None]] = None) -> ArrowBox:
        """Create and register an `ArrowBox` widget."""
        return self.gui.add(ArrowBox(self.gui, id, rect, direction, on_activate))

    def button(self, id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None) -> Button:
        """Create and register a `Button` widget."""
        safe_text = '' if text is None else text
        return self.gui.add(Button(self.gui, id, rect, style, safe_text, on_activate))

    def button_group(self, group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> ButtonGroup:
        """Create and register a grouped `ButtonGroup` widget."""
        return self.gui.add(ButtonGroup(self.gui, group, id, rect, style, text))

    def canvas(self, id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> Canvas:
        """Create and register a `Canvas` widget."""
        return self.gui.add(Canvas(self.gui, id, rect, backdrop, on_activate, automatic_pristine))

    def frame(self, id: str, rect: Rect) -> Frame:
        """Create and register a `Frame` widget."""
        return self.gui.add(Frame(self.gui, id, rect))

    def image(self, id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> Image:
        """Create and register an `Image` widget."""
        return self.gui.add(Image(self.gui, id, rect, image, automatic_pristine, scale))

    def label(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False, id: Optional[str] = None) -> Label:
        """Create and register a `Label`, generating a unique id when omitted."""
        if id is None:
            self._label_sequence += 1
            id = f'label_{self._label_sequence}'
        return self.gui.add(Label(self.gui, id, position, text, shadow))

    def scrollbar(self, id: str, overall_rect: Rect, horizontal: Orientation, style: ArrowPosition, params: Tuple[int, int, int, int]) -> Scrollbar:
        """Create and register a `Scrollbar` widget."""
        return self.gui.add(Scrollbar(self.gui, id, overall_rect, horizontal, style, params))

    def toggle(self, id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> Toggle:
        """Create and register a `Toggle` widget."""
        return self.gui.add(Toggle(self.gui, id, rect, style, pushed, pressed_text, raised_text))

    def window(
        self,
        title: str,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        backdrop: Optional[str] = None,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> Window:
        """Create and register a `Window` with optional lifecycle callbacks."""
        return self.gui.add(Window(self.gui, title, pos, size, backdrop, preamble, event_handler, postamble))
