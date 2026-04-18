from __future__ import annotations

from typing import Optional

from .widget import Widget


class FocusState:
    """Mutable focus state shared by focus-related controller logic."""

    def __init__(self) -> None:
        """Initialize the FocusState instance."""
        self.current_widget: Optional[Widget] = None

    def read_current_widget(self) -> Optional[Widget]:
        """Run read current widget and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        return self.current_widget

    def set_current_widget(self, widget: Optional[Widget]) -> None:
        """Run set current widget and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.current_widget = widget

    def clear_current_widget(self) -> None:
        """Run clear current widget and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.current_widget = None
