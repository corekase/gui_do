from __future__ import annotations

from typing import Optional

from ..intermediates.widget import Widget


class FocusState:
    """Mutable focus state shared by focus-related controller logic."""

    def __init__(self) -> None:
        """Create FocusState."""
        self.current_widget: Optional[Widget] = None

    def read_current_widget(self) -> Optional[Widget]:
        """Read current widget."""
        return self.current_widget

    def set_current_widget(self, widget: Optional[Widget]) -> None:
        """Set current widget."""
        self.current_widget = widget

    def clear_current_widget(self) -> None:
        """Clear current widget."""
        self.current_widget = None
