# slider
# has a range, with a bar optionally shown. has a bitmap drawn somewhere along the
# range to indicate a position
# can be either horizontal or vertical

from typing import Any
from ..values.constants import WidgetKind, Orientation
from .utility.widget import Widget
from .utility.registry import register_widget

@register_widget("Slider")
class Slider(Widget):
    """A slider widget for selecting a value within a range."""

    def __init__(self, gui: Any, id: Any, rect: Any, horizontal: Orientation = Orientation.Horizontal,
                 show_bar: bool = True) -> None:
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.Slider
        self.horizontal: Orientation = horizontal
        self.show_bar: bool = show_bar
        self.value: float = 0.0
        self.min_value: float = 0.0
        self.max_value: float = 100.0

    def handle_event(self, event: Any, window: Any) -> bool:
        return False

    def draw(self) -> None:
        super().draw()

    def set_range(self, min_val: float, max_val: float) -> None:
        """Set the range for the slider."""
        self.min_value = min_val
        self.max_value = max_val

    def set_value(self, value: float) -> None:
        """Set the current slider value."""
        self.value = max(self.min_value, min(value, self.max_value))

    def get_value(self) -> float:
        """Get the current slider value."""
        return self.value
