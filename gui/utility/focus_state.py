from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .geometry import point_in_rect
from .intermediates.widget import Widget

if TYPE_CHECKING:
    from .gui_manager import GuiManager
    from ..widgets.window import Window


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

    def _resolve_hovered_window(self) -> Optional["Window"]:
        """Resolve the topmost visible window under the current pointer."""
        mouse_pos = self.gui._get_mouse_pos()
        for window in self.gui.windows[::-1]:
            if not window.visible:
                continue
            if point_in_rect(mouse_pos, window.get_window_rect()):
                return window
        return None

    def _is_pointer_over_task_panel(self) -> bool:
        """Return whether pointer is currently over a visible task panel."""
        task_panel = getattr(self.gui, 'task_panel', None)
        if task_panel is None or not getattr(task_panel, 'visible', False):
            return False
        mouse_pos = self.gui._get_mouse_pos()
        return point_in_rect(mouse_pos, task_panel.get_rect())

    def activate_window_at_pointer(self) -> None:
        """Activate hovered window, or clear active window when clicking outside all windows."""
        hovered_window = self._resolve_hovered_window()
        if hovered_window is not None:
            self.gui.active_window = hovered_window
            return
        if self._is_pointer_over_task_panel():
            return
        if self.gui.active_window is not None:
            self.gui.active_window = None

    def update_active_window(self) -> None:
        """Refresh active window validity without implicit promotion."""
        current = self.gui.active_window
        if current is None:
            return
        if current in self.gui.windows and current.visible:
            return
        self.gui.active_window = None
