from pygame import Rect
from pygame.draw import rect as draw_rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL

from ..core.ui_node import UiNode
from ..layout.layout_axis import LayoutAxis


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
    ) -> None:
        super().__init__(control_id, rect)
        self.axis = axis
        self.content_size = max(1, int(content_size))
        self.viewport_size = max(1, int(viewport_size))
        self.offset = max(0, int(offset))
        self.step = max(1, int(step))
        self.dragging = False
        self._drag_anchor_offset = 0
        self._track_visuals = None
        self._handle_visuals = None
        self._track_visuals_size = None
        self._handle_visuals_size = None
        self._clamp_offset()

    def _max_offset(self) -> int:
        return max(0, self.content_size - self.viewport_size)

    def _clamp_offset(self) -> None:
        self.offset = min(max(0, self.offset), self._max_offset())

    def _track_rect(self) -> Rect:
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(self.rect.x + 4, self.rect.centery - 5, max(1, self.rect.width - 8), 10)
        return Rect(self.rect.centerx - 5, self.rect.y + 4, 10, max(1, self.rect.height - 8))

    def _handle_length(self) -> int:
        track = self._track_rect()
        if self.content_size <= 0:
            return 12
        ratio = self.viewport_size / float(self.content_size)
        if self.axis == LayoutAxis.HORIZONTAL:
            return max(12, int(round(track.width * ratio)))
        return max(12, int(round(track.height * ratio)))

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

    def handle_event(self, event, app) -> bool:
        raw = getattr(event, "pos", None)
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            if isinstance(raw, tuple) and len(raw) == 2 and self.handle_rect().collidepoint(raw):
                handle = self.handle_rect()
                if self.axis == LayoutAxis.HORIZONTAL:
                    self._drag_anchor_offset = raw[0] - handle.x
                else:
                    self._drag_anchor_offset = raw[1] - handle.y
                app.pointer_capture.begin(self.control_id, self._lock_rect(raw))
                self.dragging = True
                return True

        if event.type == MOUSEMOTION and self.dragging and app.pointer_capture.is_owned_by(self.control_id):
            pos = app.pointer_capture.clamp(app.input_state.pointer_pos)
            track = self._track_rect()
            if self.axis == LayoutAxis.HORIZONTAL:
                axis_pixel = pos[0] - track.left - self._drag_anchor_offset
            else:
                axis_pixel = pos[1] - track.top - self._drag_anchor_offset
            self.offset = self._pixel_to_offset(axis_pixel)
            self._clamp_offset()
            return True

        if event.type == MOUSEBUTTONUP and getattr(event, "button", None) == 1 and self.dragging:
            self.dragging = False
            app.pointer_capture.end(self.control_id)
            return True

        if event.type == MOUSEWHEEL and self.rect.collidepoint(app.input_state.pointer_pos):
            self.offset -= int(getattr(event, "y", 0)) * self.step
            self._clamp_offset()
            return True
        return False

    def draw(self, surface, theme) -> None:
        track = self._track_rect()
        handle = self.handle_rect()
        factory = getattr(theme, "graphics_factory", None)
        if factory is None:
            draw_rect(surface, theme.dark, track, 0)
            fill = theme.dark if self.dragging else theme.light
            draw_rect(surface, fill, handle, 0)
            draw_rect(surface, theme.dark, handle, 2)
            return
        track_size = (track.width, track.height)
        handle_size = (handle.width, handle.height)
        if self._track_visuals is None or self._track_visuals_size != track_size:
            self._track_visuals = factory.build_frame_visuals(track)
            self._track_visuals_size = track_size
        if self._handle_visuals is None or self._handle_visuals_size != handle_size:
            self._handle_visuals = factory.build_frame_visuals(handle)
            self._handle_visuals_size = handle_size
        surface.blit(self._track_visuals.idle, track)
        if self.dragging:
            surface.blit(self._handle_visuals.armed, handle)
        else:
            surface.blit(self._handle_visuals.hover, handle)
