from __future__ import annotations

from typing import Callable, Optional
from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class ArrowBoxControl(UiNode):
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
        self._pressed = False
        self._hovered = False
        self._focus_activation_armed = False
        self._timer_id = ("arrow_repeat", self.control_id)
        self._visuals = None
        self._visual_key = None

    def _invoke(self) -> None:
        if self.on_activate is not None:
            self.on_activate()

    def _invoke_click(self) -> None:
        """Keyboard-activation entry point used by the focus manager's armed-visual path."""
        self._invoke()

    def begin_focus_activation_visual(self) -> None:
        """Show a temporary armed visual after focus-driven activation."""
        if self._focus_activation_armed:
            return
        self._focus_activation_armed = True
        self.invalidate()

    def end_focus_activation_visual(self) -> None:
        """Clear temporary armed visual after focus activation hint timeout."""
        if not self._focus_activation_armed:
            return
        self._focus_activation_armed = False
        self.invalidate()

    def set_on_activate(self, callback: Optional[Callable[[], None]]) -> None:
        """Replace the activation callback at runtime. Pass None to remove it."""
        if callback is not None and not callable(callback):
            raise ValueError("on_activate callback must be callable or None")
        self.on_activate = callback

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        if old_enabled != new_enabled:
            self._hovered = False
            self._pressed = False
            self._focus_activation_armed = False
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        if old_visible != new_visible:
            self._hovered = False
            self._pressed = False
            self._focus_activation_armed = False
        super()._on_visibility_changed(old_visible, new_visible)

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            self._hovered = False
            if self._pressed:
                self._pressed = False
                app.timers.remove_timer(self._timer_id)
            return False

        raw = event.pos
        if isinstance(raw, tuple) and len(raw) == 2:
            self._hovered = self.rect.collidepoint(raw)
        if event.is_mouse_motion() and self._pressed and not self._hovered:
            self._pressed = False
            app.timers.remove_timer(self._timer_id)
            return True
        if event.is_mouse_down(1):
            if isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw):
                self._pressed = True
                self._invoke()
                if self.repeat_interval_seconds > 0:
                    app.timers.add_timer(self._timer_id, self.repeat_interval_seconds, self._invoke)
                return True
        if event.is_mouse_up(1):
            if self._pressed:
                self._pressed = False
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
        hovered = self._hovered
        selected = factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=self._pressed or self._focus_activation_armed,
            hovered=hovered,
        )
        surface.blit(selected, self.rect)
