from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ...events.gui_event import GuiEvent
from ..base._hover_press_control_base import _HoverPressControlBase
from ...graphics.built_in_factory import InteractiveVisuals
from ...app.error_handling import logical_error

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme


class ImageButtonControl(_HoverPressControlBase):
    """Button-like control that renders state-specific bitmap surfaces."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        idle_bitmap: pygame.Surface,
        hover_bitmap: pygame.Surface,
        armed_bitmap: pygame.Surface,
        on_click: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self.on_click = on_click
        self._visuals: Optional[InteractiveVisuals] = None
        self._visual_size = (0, 0)
        self.set_bitmaps(idle_bitmap, hover_bitmap, armed_bitmap)

    def _invoke_click(self) -> None:
        if self.on_click is not None:
            self.on_click()

    def set_on_click(self, callback: Optional[Callable[[], None]]) -> None:
        if callback is not None and not callable(callback):
            raise logical_error("on_click callback must be callable or None", subsystem="gui.controls", operation="ImageButtonControl.set_on_click", source_skip_frames=1)
        self.on_click = callback

    @staticmethod
    def _validate_bitmap(bitmap: pygame.Surface, name: str) -> pygame.Surface:
        if not isinstance(bitmap, pygame.Surface):
            raise logical_error(f"{name} must be a pygame.Surface", subsystem="gui.controls", operation="ImageButtonControl.set_bitmaps", source_skip_frames=1)
        return bitmap.copy()

    def set_bitmaps(
        self,
        idle_bitmap: pygame.Surface,
        hover_bitmap: pygame.Surface,
        armed_bitmap: pygame.Surface,
        *,
        factory=None,
    ) -> None:
        idle = self._validate_bitmap(idle_bitmap, "idle_bitmap")
        hover = self._validate_bitmap(hover_bitmap, "hover_bitmap")
        armed = self._validate_bitmap(armed_bitmap, "armed_bitmap")
        if hover.get_size() != idle.get_size() or armed.get_size() != idle.get_size():
            raise logical_error(
                "idle/hover/armed bitmaps must have matching sizes",
                subsystem="gui.controls",
                operation="ImageButtonControl.set_bitmaps",
                source_skip_frames=1,
            )

        disabled_factory = factory
        if disabled_factory is None:
            class _FallbackFactory:
                @staticmethod
                def build_disabled_bitmap(bitmap: pygame.Surface) -> pygame.Surface:
                    out = bitmap.copy()
                    out.fill((160, 160, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    return out

                @staticmethod
                def build_hidden_bitmap(size) -> pygame.Surface:
                    return pygame.Surface(size, pygame.SRCALPHA)

            disabled_factory = _FallbackFactory()

        disabled = disabled_factory.build_disabled_bitmap(idle)
        disabled_armed = disabled_factory.build_disabled_bitmap(armed)
        hidden = disabled_factory.build_hidden_bitmap(idle.get_size())
        self._visuals = InteractiveVisuals(
            idle=idle,
            hover=hover,
            armed=armed,
            disabled=disabled,
            disabled_armed=disabled_armed,
            hidden=hidden,
            hit_rect=Rect(0, 0, idle.get_width(), idle.get_height()),
        )
        self._visual_size = idle.get_size()
        self.invalidate()

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            self.hovered = False
            self.pressed = False
            return False

        raw = event.pos
        has_pointer = isinstance(raw, tuple) and len(raw) == 2
        is_hover = bool(has_pointer and self.rect.collidepoint(raw))
        if has_pointer:
            self.hovered = is_hover

        if event.is_mouse_down(1) and is_hover:
            self.pressed = True
            return True

        if event.is_mouse_up(1):
            was_pressed = self.pressed
            self.pressed = False
            if was_pressed and self.hovered:
                self._invoke_click()
                return True
            return was_pressed

        return False

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        if self._visuals is None:
            return
        selected = theme.graphics_factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=self.pressed and self.hovered,
            hovered=self.hovered,
        )
        surface.blit(selected, self.rect)
