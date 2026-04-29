from __future__ import annotations

from typing import Callable, Optional
from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from ...events.gui_event import GuiEvent
from ..base._hover_press_control_base import _HoverPressControlBase

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class ArrowBoxControl(_HoverPressControlBase):
    """Arrow button with optional repeat activation while held.

    Direction is accepted in true mathematical degrees:
    0=right, 90=up, 180=left, 270=down.
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        direction: int,
        on_activate: Optional[Callable[[], None]] = None,
        repeat_interval_seconds: float = 0.08,
    ) -> None:
        super().__init__(control_id, rect)
        self.direction = int(direction) % 360
        self.on_activate = on_activate
        self.repeat_interval_seconds = float(repeat_interval_seconds)
        self._timer_id = ("arrow_repeat", self.control_id)
        self._visuals = None
        self._visual_key = None

    def _invoke(self) -> None:
        if self.on_activate is not None:
            self.on_activate()

    def _invoke_click(self) -> None:
        """Keyboard-activation entry point used by the focus manager's armed-visual path."""
        self._invoke()

    def set_on_activate(self, callback: Optional[Callable[[], None]]) -> None:
        """Replace the activation callback at runtime. Pass None to remove it."""
        if callback is not None and not callable(callback):
            raise ValueError("on_activate callback must be callable or None")
        self.on_activate = callback

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            self.hovered = False
            if self.pressed:
                self.pressed = False
                app.timers.remove_timer(self._timer_id)
            return False

        raw = event.pos
        if isinstance(raw, tuple) and len(raw) == 2:
            self.hovered = self.rect.collidepoint(raw)
        if event.is_mouse_motion() and self.pressed and not self.hovered:
            self.pressed = False
            app.timers.remove_timer(self._timer_id)
            return True
        if event.is_mouse_down(1):
            if isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw):
                self.pressed = True
                self._invoke()
                if self.repeat_interval_seconds > 0:
                    app.timers.add_timer(self._timer_id, self.repeat_interval_seconds, self._invoke)
                return True
        if event.is_mouse_up(1):
            if self.pressed:
                self.pressed = False
                app.timers.remove_timer(self._timer_id)
                return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        factory = theme.graphics_factory
        render_direction = int(self.direction) % 360
        visual_key = (self.rect.width, self.rect.height, render_direction)
        if self._visuals is None or self._visual_key != visual_key:
            self._visuals = factory.draw_arrow_visuals(self.rect, render_direction)
            self._visual_key = visual_key
        selected = factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=self.pressed or self._focus_activation_armed,
            hovered=self.hovered,
        )
        surface.blit(selected, self.rect)
