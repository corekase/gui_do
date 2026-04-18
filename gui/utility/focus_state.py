from typing import Optional, TYPE_CHECKING

from .widget import Widget

if TYPE_CHECKING:
    from .guimanager import GuiManager
    from ..widgets.window import Window as gWindow


class FocusStateController:
    """Owns current hover focus and active-window refresh rules."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def _is_registered_object(self, value: Widget) -> bool:
        registry = getattr(self.gui, 'object_registry', None)
        if registry is not None and hasattr(registry, 'is_registered_object'):
            return bool(registry.is_registered_object(value))
        return False

    def set_current_widget(self, value: Optional[Widget]) -> None:
        if value is not None:
            if not isinstance(value, Widget) or not self._is_registered_object(value):
                value = None
        current = self.resolve_current_widget()
        if current != value:
            if current is not None:
                current.leave()
            self.gui.focus_state_data.current_widget = value

    def resolve_current_widget(self) -> Optional[Widget]:
        if self.gui.focus_state_data.current_widget is None:
            return None
        if not self._is_registered_object(self.gui.focus_state_data.current_widget):
            self.gui.focus_state_data.current_widget = None
            return None
        return self.gui.focus_state_data.current_widget

    def update_focus(self, new_hover: Optional[Widget]) -> None:
        self.set_current_widget(new_hover)

    def update_active_window(self) -> None:
        top_window: Optional["gWindow"] = None
        for window in self.gui.windows[::-1]:
            if window.visible and window.get_window_rect().collidepoint(self.gui.get_mouse_pos()):
                top_window = window
                break
        self.gui.active_window = top_window
