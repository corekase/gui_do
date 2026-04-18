from typing import Optional

from .widget import Widget


class FocusState:
    """Mutable focus state shared by focus-related controller logic."""

    def __init__(self) -> None:
        self.current_widget: Optional[Widget] = None

    def read_current_widget(self) -> Optional[Widget]:
        return self.current_widget

    def set_current_widget(self, widget: Optional[Widget]) -> None:
        self.current_widget = widget

    def clear_current_widget(self) -> None:
        self.current_widget = None
