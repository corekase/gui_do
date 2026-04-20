from __future__ import annotations

from typing import Callable, Optional, Tuple, Union, TYPE_CHECKING

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
from ..widgets.slider import Slider
from ..widgets.toggle import Toggle

if TYPE_CHECKING:
    from .gui_manager import GuiManager


class TaskPanelWidgetBuilder:
    """Typed OOP-style widget builder that routes creations into the task panel."""

    def __init__(self, gui: "GuiManager") -> None:
        self.gui: "GuiManager" = gui

    def arrow_box(self, id: str, rect: Rect, direction: float, on_activate: Optional[Callable[[], None]] = None) -> ArrowBox:
        return self.gui._task_panel_add_widget(self.gui.arrow_box, id, rect, direction, on_activate)

    def button(self, id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None) -> Button:
        return self.gui._task_panel_add_widget(self.gui.button, id, rect, style, text, on_activate)

    def button_group(self, group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> ButtonGroup:
        return self.gui._task_panel_add_widget(self.gui.button_group, group, id, rect, style, text)

    def canvas(self, id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> Canvas:
        return self.gui._task_panel_add_widget(self.gui.canvas, id, rect, backdrop, on_activate, automatic_pristine)

    def frame(self, id: str, rect: Rect) -> Frame:
        return self.gui._task_panel_add_widget(self.gui.frame, id, rect)

    def image(self, id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> Image:
        return self.gui._task_panel_add_widget(self.gui.image, id, rect, image, automatic_pristine, scale)

    def label(self, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False, id: Optional[str] = None) -> Label:
        return self.gui._task_panel_add_widget(self.gui.label, position, text, shadow, id)

    def scrollbar(
        self,
        id: str,
        overall_rect: Rect,
        horizontal: Orientation,
        style: ArrowPosition,
        params: Tuple[int, int, int, int],
        wheel_positive_to_max: bool = False,
    ) -> Scrollbar:
        return self.gui._task_panel_add_widget(self.gui.scrollbar, id, overall_rect, horizontal, style, params, wheel_positive_to_max)

    def slider(
        self,
        id: str,
        rect: Rect,
        horizontal: Orientation,
        total_range: int,
        position: float = 0.0,
        integer_type: bool = False,
        notch_interval_percent: float = 5.0,
        wheel_positive_to_max: bool = False,
        wheel_step: Optional[float] = None,
    ) -> Slider:
        return self.gui._task_panel_add_widget(
            self.gui.slider,
            id,
            rect,
            horizontal,
            total_range,
            position,
            integer_type,
            notch_interval_percent,
            wheel_positive_to_max,
            wheel_step,
        )

    def toggle(self, id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> Toggle:
        return self.gui._task_panel_add_widget(self.gui.toggle, id, rect, style, pushed, pressed_text, raised_text)

    def set_lifecycle(
        self,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        """Convenience proxy for task-panel lifecycle configuration."""
        self.gui.set_task_panel_lifecycle(preamble=preamble, event_handler=event_handler, postamble=postamble)
