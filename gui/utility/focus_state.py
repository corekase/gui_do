from typing import Optional, TYPE_CHECKING

from .widget import Widget

if TYPE_CHECKING:
    from .guimanager import GuiManager
    from ..widgets.window import Window as gWindow


class FocusStateController:
    """Owns current hover focus and active-window refresh rules."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def set_current_widget(self, value: Optional[Widget]) -> None:
        if value is not None:
            if not isinstance(value, Widget) or not self.gui._is_registered_object(value):
                value = None
        current = self.resolve_current_widget()
        if current != value:
            if current is not None:
                current.leave()
            self.gui._current_widget = value

    def resolve_current_widget(self) -> Optional[Widget]:
        if self.gui._current_widget is None:
            return None
        if not self.gui._is_registered_object(self.gui._current_widget):
            self.gui._current_widget = None
            return None
        return self.gui._current_widget

    def update_focus(self, new_hover: Optional[Widget]) -> None:
        self.set_current_widget(new_hover)

    def update_active_window(self) -> None:
        top_window: Optional["gWindow"] = None
        for window in self.gui.windows[::-1]:
            if window.visible and window.get_window_rect().collidepoint(self.gui.get_mouse_pos()):
                top_window = window
                break
        self.gui.active_window = top_window
