from typing import Optional

from .widget import Widget


class FocusState:
    """Mutable focus state shared by focus-related controller logic."""

    def __init__(self) -> None:
        self.current_widget: Optional[Widget] = None
