import inspect
import pygame
from typing import Callable, Optional, TYPE_CHECKING

from pygame import Rect

from ..core.gui_event import GuiEvent
from ..core.ui_node import UiNode
from ..layout.layout_axis import LayoutAxis

if TYPE_CHECKING:
    import pygame
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class ScrollbarControl(UiNode):
    """Viewport scrollbar with captured handle drag and wheel stepping."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        axis: LayoutAxis,
        content_size: int,
        viewport_size: int,
        offset: int = 0,
        step: int = 16,
        on_change: Optional[Callable[[int], None]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self.axis = axis
        self.content_size = max(1, int(content_size))
        self.viewport_size = max(1, int(viewport_size))
        self.offset = max(0, int(offset))
        self.step = max(1, int(step))
        self.on_change = on_change
        self.dragging = False
        self._drag_anchor_offset = 0
        self._track_visuals = None
        self._handle_visuals = None
        self._track_visuals_size = None
        self._handle_visuals_size = None
        self._clamp_offset()

    @staticmethod
    def _accepts_reason(callback: Callable) -> bool:
        try:
            signature = inspect.signature(callback)
        except (TypeError, ValueError):
            return False
        for parameter in signature.parameters.values():
            if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
                return True
        positional = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        return len(positional) >= 2

    def _notify_change(self, reason: str) -> None:
        if self.on_change is None:
            return
        if self._accepts_reason(self.on_change):
            self.on_change(self.offset, str(reason))
            return
        self.on_change(self.offset)

    def _normalize_geometry(self) -> None:
        self.content_size = max(1, int(self.content_size))
        self.viewport_size = max(1, int(self.viewport_size))
        self.step = max(1, int(self.step))

    def _max_offset(self) -> int:
        self._normalize_geometry()
        return max(0, self.content_size - self.viewport_size)

    def _clamp_offset(self) -> None:
        self._normalize_geometry()
        self.offset = min(max(0, self.offset), self._max_offset())

    def _page_step(self) -> int:
        return max(self.step, int(round(self.viewport_size * 0.9)))

    def _nudge(self, delta: int) -> None:
        self._set_offset(self.offset + int(delta))

    def set_offset(self, offset: int) -> bool:
        """Set offset programmatically with clamp and on_change callback semantics."""
        return self._set_offset(offset, reason="programmatic")

    def adjust_offset(self, delta: int) -> bool:
        """Adjust offset programmatically by a delta with clamp and callbacks."""
        return self._set_offset(self.offset + int(delta), reason="programmatic")

    def _set_offset(self, new_offset: int, reason: str = "programmatic") -> bool:
        old_offset = self.offset
        self.offset = int(new_offset)
        self._clamp_offset()
        changed = self.offset != old_offset
        if changed:
            self._notify_change(reason)
        return changed

    def _track_rect(self) -> Rect:
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(self.rect.x + 4, self.rect.centery - 5, max(1, self.rect.width - 8), 10)
        return Rect(self.rect.centerx - 5, self.rect.y + 4, 10, max(1, self.rect.height - 8))

    def _handle_length(self) -> int:
        track = self._track_rect()
        if self.content_size <= 0:
            return 12
        ratio = min(1.0, self.viewport_size / float(self.content_size))
        if self.axis == LayoutAxis.HORIZONTAL:
            track_span = max(1, track.width)
        else:
            track_span = max(1, track.height)
        base = int(round(track_span * ratio))
        return max(1, min(track_span, max(12, base)))

    def _offset_to_pixel(self) -> int:
        track = self._track_rect()
        max_offset = self._max_offset()
        handle_len = self._handle_length()
        travel_span = max(1, (track.width - handle_len) if self.axis == LayoutAxis.HORIZONTAL else (track.height - handle_len))
        ratio = 0.0 if max_offset <= 0 else self.offset / float(max_offset)
        return int(round(ratio * travel_span))

    def _pixel_to_offset(self, pixel: int) -> int:
        track = self._track_rect()
        handle_len = self._handle_length()
        travel_span = max(1, (track.width - handle_len) if self.axis == LayoutAxis.HORIZONTAL else (track.height - handle_len))
        max_offset = self._max_offset()
        ratio = min(max(pixel / float(travel_span), 0.0), 1.0)
        return int(round(ratio * max_offset))

    def handle_rect(self) -> Rect:
        self._clamp_offset()
        track = self._track_rect()
        handle_len = self._handle_length()
        pixel = self._offset_to_pixel()
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(track.left + pixel, track.top, handle_len, track.height)
        return Rect(track.left, track.top + pixel, track.width, handle_len)

    def _lock_rect(self, pointer_pos) -> Rect:
        track = self._track_rect()
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(track.left, pointer_pos[1], track.width + 1, 1)
        return Rect(pointer_pos[0], track.top, 1, track.height + 1)

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            if self.dragging and app.pointer_capture.is_owned_by(self.control_id):
                app.pointer_capture.end(self.control_id)
            self.dragging = False
            return False

        if event.is_key_down(pygame.K_HOME):
            return self._set_offset(0, reason="keyboard")
        if event.is_key_down(pygame.K_END):
            return self._set_offset(self._max_offset(), reason="keyboard")
        if event.is_key_down(pygame.K_PAGEUP):
            return self._set_offset(self.offset - self._page_step(), reason="keyboard")
        if event.is_key_down(pygame.K_PAGEDOWN):
            return self._set_offset(self.offset + self._page_step(), reason="keyboard")
        if self.axis == LayoutAxis.HORIZONTAL:
            if event.is_key_down(pygame.K_LEFT):
                return self._set_offset(self.offset - self.step, reason="keyboard")
            if event.is_key_down(pygame.K_RIGHT):
                return self._set_offset(self.offset + self.step, reason="keyboard")
        else:
            if event.is_key_down(pygame.K_UP):
                return self._set_offset(self.offset - self.step, reason="keyboard")
            if event.is_key_down(pygame.K_DOWN):
                return self._set_offset(self.offset + self.step, reason="keyboard")

        raw = event.pos
        if event.is_mouse_down(1):
            if isinstance(raw, tuple) and len(raw) == 2 and self.handle_rect().collidepoint(raw):
                handle = self.handle_rect()
                if self.axis == LayoutAxis.HORIZONTAL:
                    self._drag_anchor_offset = raw[0] - handle.x
                else:
                    self._drag_anchor_offset = raw[1] - handle.y
                app.pointer_capture.begin(self.control_id, self._lock_rect(raw))
                self.dragging = True
                return True

        if event.is_mouse_motion() and self.dragging and app.pointer_capture.is_owned_by(self.control_id):
            pos = app.pointer_capture.clamp(app.input_state.pointer_pos)
            track = self._track_rect()
            if self.axis == LayoutAxis.HORIZONTAL:
                axis_pixel = pos[0] - track.left - self._drag_anchor_offset
            else:
                axis_pixel = pos[1] - track.top - self._drag_anchor_offset
            return self._set_offset(self._pixel_to_offset(axis_pixel), reason="mouse_drag")

        if event.is_mouse_up(1) and self.dragging:
            self.dragging = False
            app.pointer_capture.end(self.control_id)
            return True

        if event.is_mouse_wheel() and self.rect.collidepoint(app.input_state.pointer_pos):
            return self._set_offset(self.offset - (int(event.wheel_delta) * self.step), reason="wheel")
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        track = self._track_rect()
        handle = self.handle_rect()
        factory = theme.graphics_factory
        track_size = (track.width, track.height)
        handle_size = (handle.width, handle.height)
        if self._track_visuals is None or self._track_visuals_size != track_size:
            self._track_visuals = factory.build_frame_visuals(track)
            self._track_visuals_size = track_size
        if self._handle_visuals is None or self._handle_visuals_size != handle_size:
            self._handle_visuals = factory.build_frame_visuals(handle)
            self._handle_visuals_size = handle_size
        track_selected = factory.resolve_visual_state(
            self._track_visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=False,
            hovered=False,
        )
        handle_selected = factory.resolve_visual_state(
            self._handle_visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=self.dragging,
            hovered=not self.dragging,
        )
        surface.blit(track_selected, track)
        surface.blit(handle_selected, handle)
