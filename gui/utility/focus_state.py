from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .intermediates.widget import Widget

if TYPE_CHECKING:
    from .gui_manager import GuiManager
    from ..widgets.window import Window as Window


class FocusStateController:
    """Owns current hover focus and active-window refresh rules."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create FocusStateController."""
        self.gui: "GuiManager" = gui_manager

    def _is_registered_object(self, value: Widget) -> bool:
        """Is registered object."""
        registry = getattr(self.gui, 'object_registry', None)
        if registry is not None and hasattr(registry, 'is_registered_object'):
            return bool(registry.is_registered_object(value))
        return False

    @property
    def current_widget(self) -> Optional[Widget]:
        """Current widget."""
        return self.resolve_current_widget()

    @current_widget.setter
    def current_widget(self, value: Optional[Widget]) -> None:
        """Current widget."""
        self.set_current_widget(value)

    def set_current_widget(self, value: Optional[Widget]) -> None:
        """Set current widget."""
        if value is not None:
            if not isinstance(value, Widget) or not self._is_registered_object(value):
                value = None
        current = self.resolve_current_widget()
        if current != value:
            if current is not None:
                current.leave()
            self.gui.focus_state_data.set_current_widget(value)

    def resolve_current_widget(self) -> Optional[Widget]:
        """Resolve current widget."""
        current = self.gui.focus_state_data.read_current_widget()
        if current is None:
            return None
        if not self._is_registered_object(current):
            self.gui.focus_state_data.clear_current_widget()
            return None
        return current

    def update_focus(self, new_hover: Optional[Widget]) -> None:
        """Update focus."""
        self.set_current_widget(new_hover)

    def update_active_window(self) -> None:
        """Update active window."""
        top_window: Optional["Window"] = None
        for window in self.gui.windows[::-1]:
            if window.visible and window.get_window_rect().collidepoint(self.gui.get_mouse_pos()):
                top_window = window
                break
        self.gui.active_window = top_window
