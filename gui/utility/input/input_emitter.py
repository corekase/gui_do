from __future__ import annotations

from pygame.event import Event as PygameEvent
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from typing import Optional, TYPE_CHECKING
from ..events import Event
from .normalized_event import NormalizedInputEvent
from .input_actions import InputAction

if TYPE_CHECKING:
    from ..gui_utils.gui_event import GuiEvent
    from ..gui_manager import GuiManager


class InputEventEmitter:
    """Centralized translation from routed input outcomes to GuiEvent values."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create InputEventEmitter."""
        self.gui: "GuiManager" = gui_manager

    def emit_action(self, action: InputAction) -> "GuiEvent":
        """Emit action."""
        if action.builder is not None:
            return action.builder()
        if action.event_type is None:
            return self.gui.event(Event.Pass)
        return self.gui.event(action.event_type, **action.kwargs)

    def base_mouse_event(self, event: PygameEvent, normalized: NormalizedInputEvent) -> "GuiEvent":
        """Base mouse event."""
        if event.type == MOUSEBUTTONUP:
            return self.gui.event(Event.MouseButtonUp, button=normalized.button)
        if event.type == MOUSEBUTTONDOWN:
            return self.gui.event(Event.MouseButtonDown, button=normalized.button)
        if event.type == MOUSEMOTION:
            return self.gui.event(Event.MouseMotion, rel=normalized.rel)
        return self.pass_event()

    def system_event(self, event: PygameEvent, normalized: NormalizedInputEvent) -> "GuiEvent":
        """System event."""
        if event.type == QUIT:
            return self.gui.event(Event.Quit)
        if event.type == KEYUP:
            return self.gui.event(Event.KeyUp, key=normalized.key)
        if event.type == KEYDOWN:
            return self.gui.event(Event.KeyDown, key=normalized.key)
        return self.pass_event()

    def widget_event(self, widget_id: Optional[str] = None, *, window=None, task_panel: bool = False) -> "GuiEvent":
        """Widget event."""
        kwargs = {}
        if widget_id is not None:
            kwargs['widget_id'] = widget_id
        if window is not None:
            kwargs['window'] = window
        if task_panel:
            kwargs['task_panel'] = True
        return self.gui.event(Event.Widget, **kwargs)

    def pass_event(self) -> "GuiEvent":
        """Pass event."""
        return self.gui.event(Event.Pass)
