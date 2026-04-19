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
        return bool(self.gui.object_registry.is_registered_object(value))

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
        hovered_window: Optional["Window"] = None
        top_visible_window: Optional["Window"] = None
        mouse_pos = self.gui.get_mouse_pos()
        for window in self.gui.windows[::-1]:
            if not window.visible:
                continue
            if top_visible_window is None:
                top_visible_window = window
            if window.get_window_rect().collidepoint(mouse_pos):
                hovered_window = window
                break
        if hovered_window is not None:
            self.gui.active_window = hovered_window
            return
        current = self.gui.active_window
        if current is not None and current in self.gui.windows and current.visible:
            return
        self.gui.active_window = top_visible_window
