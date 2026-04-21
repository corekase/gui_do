from typing import Optional
from typing import TYPE_CHECKING

from pygame import Rect

from .gui_event import GuiEvent

if TYPE_CHECKING:
    import pygame
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class UiNode:
    """Base node for all controls in the rebased package."""

    def __init__(self, control_id: str, rect: Rect) -> None:
        self.control_id = control_id
        self.rect = Rect(rect)
        self.enabled = True
        self._visible = True
        self.parent: Optional["UiNode"] = None
        self.children: list["UiNode"] = []

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        previous = self._visible
        self._visible = bool(value)
        if previous != self._visible:
            self._on_visibility_changed(previous, self._visible)

    def _on_visibility_changed(self, _old_visible: bool, _new_visible: bool) -> None:
        """Hook for controls that need side effects when visibility changes."""

    def is_window(self) -> bool:
        return False

    def is_task_panel(self) -> bool:
        return False

    def set_active(self, _value: bool) -> None:
        """Hook for controls that support active-state semantics."""

    def _clear_active_windows(self) -> None:
        """Hook for container nodes that manage active window state."""

    def update(self, _dt_seconds: float) -> None:
        """Per-frame state update."""

    def handle_event(self, _event: GuiEvent, _app: "GuiApplication") -> bool:
        """Handle one normalized GuiEvent and return whether consumed."""
        return False

    def draw(self, _surface: "pygame.Surface", _theme: "ColorTheme") -> None:
        """Draw control onto target surface."""
