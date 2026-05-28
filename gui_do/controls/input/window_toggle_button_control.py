from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from pygame import Rect
from ...events.gui_event import GuiEvent
from .toggle_control import ToggleControl

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication


class WindowToggleButtonControl(ToggleControl):
    """
    Specialized toggle button for managed window controls in the task panel.
    Uses the shared window presentation model for visibility state.
    """
    def __init__(
        self,
        control_id: str,
        rect: Rect,
        window_id: str,
        text_on: str,
        text_off: Optional[str] = None,
        pushed: bool = False,
        on_toggle=None,
        on_show=None,
        style: str = "box",
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect, text_on, text_off, pushed, on_toggle, style, font_role)
        self.window_id = window_id
        self.on_show = on_show

    def handle_event(self, event: GuiEvent, app: GuiApplication, theme=None) -> bool:
        if not self.visible or not self.enabled:
            self.hovered = False
            return False

        raw = event.pos
        inside = isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw)
        if isinstance(raw, tuple) and len(raw) == 2:
            self.hovered = inside

        window_presentation = getattr(app, "window_presentation", None)
        get_window = getattr(window_presentation, "get_window", None)
        window = get_window(self.window_id) if callable(get_window) else None
        is_visible = bool(getattr(window, "visible", False))
        is_open = bool(is_visible or self.pushed)
        # Raise path should be keyed to actual visibility. The pushed flag can
        # drift stale across external hide/show paths; only use it as a
        # fallback when window resolution is temporarily unavailable.
        should_raise_visible = bool(is_visible or (window is None and self.pushed))

        def _notify_toggle(pushed: bool) -> None:
            if self.on_toggle is None:
                return
            skip_for_presentation = bool(
                window_presentation is not None
                and getattr(self.on_toggle, "_window_presentation_visibility_handler", False)
            )
            if not skip_for_presentation:
                self.on_toggle(bool(pushed))

        if event.is_mouse_down(1) and inside:
            if should_raise_visible:
                self.pushed = True
                show_window = getattr(window_presentation, "show", None)
                if callable(show_window):
                    show_window(self.window_id)
                elif callable(self.on_show):
                    self.on_show()
            else:
                self.pushed = True
                if window_presentation is not None:
                    window_presentation.set_visible(self.window_id, True, from_toggle=True)
                _notify_toggle(True)
            return True

        if event.is_mouse_down(3) and inside:
            if is_open:
                self.pushed = False
                if window_presentation is not None:
                    window_presentation.set_visible(self.window_id, False, from_toggle=True)
                _notify_toggle(False)
            return True

        if event.is_key_down():
            if not is_visible:
                self.pushed = True
                if window_presentation is not None:
                    window_presentation.set_visible(self.window_id, True, from_toggle=True)
                _notify_toggle(True)
            return True

        return False
