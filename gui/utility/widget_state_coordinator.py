from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pygame.event import Event as PygameEvent

from .events import GuiError
from .widget import Widget

if TYPE_CHECKING:
    from .gui_manager import GuiManager
    from ..widgets.window import Window as Window


class WidgetStateCoordinator:
    """Owns widget visibility toggles and per-widget event handling flow."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create WidgetStateCoordinator."""
        self.gui: "GuiManager" = gui_manager

    def hide_widgets(self, *widgets: Widget) -> None:
        """Hide widgets."""
        for widget in widgets:
            if not isinstance(widget, Widget):
                raise GuiError(f'hide_widgets expected Widget, got: {type(widget).__name__}')
            widget.visible = False

    def show_widgets(self, *widgets: Widget) -> None:
        """Show widgets."""
        for widget in widgets:
            if not isinstance(widget, Widget):
                raise GuiError(f'show_widgets expected Widget, got: {type(widget).__name__}')
            widget.visible = True

    def handle_widget(self, widget: Widget, event: PygameEvent, window: Optional["Window"] = None) -> bool:
        """Handle widget."""
        if widget.handle_event(event, window):
            if widget.on_activate is not None:
                if not callable(widget.on_activate):
                    raise GuiError(f'widget callback is not callable for id: {widget.id}')
                widget.on_activate()
                return False
            return True
        return False
