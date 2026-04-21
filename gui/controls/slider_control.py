from pygame import Rect
from pygame.draw import rect as draw_rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL

from ..core.ui_node import UiNode
from ..layout.layout_axis import LayoutAxis


class SliderControl(UiNode):
    """Single-value slider with capture-locked drag behavior."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        axis: LayoutAxis,
        minimum: float,
        maximum: float,
        value: float,
    ) -> None:
        super().__init__(control_id, rect)
        self.axis = axis
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.value = float(value)
        self.dragging = False
        self.handle_size = 16
        self._drag_anchor_offset = 0
        self._track_visuals = None
        self._handle_visuals = None
        self._track_visuals_size = None
        self._handle_visuals_size = None
        self._clamp_value()

    def _clamp_value(self) -> None:
        self.value = min(max(self.value, self.minimum), self.maximum)

    def _travel_rect(self) -> Rect:
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(self.rect.x + 8, self.rect.centery - 4, max(1, self.rect.width - 16), 8)
        return Rect(self.rect.centerx - 4, self.rect.y + 8, 8, max(1, self.rect.height - 16))

    def _to_pixel(self, value: float) -> int:
        travel = self._travel_rect()
        span = self.maximum - self.minimum
        ratio = 0.0 if span <= 0 else (value - self.minimum) / span
        if self.axis == LayoutAxis.HORIZONTAL:
            return int(round(travel.left + (ratio * travel.width)))
        return int(round(travel.top + (ratio * travel.height)))

    def _to_value(self, pixel: int) -> float:
        travel = self._travel_rect()
        if self.axis == LayoutAxis.HORIZONTAL:
            ratio = 0.0 if travel.width <= 0 else (pixel - travel.left) / float(travel.width)
        else:
            ratio = 0.0 if travel.height <= 0 else (pixel - travel.top) / float(travel.height)
        ratio = min(max(ratio, 0.0), 1.0)
        return self.minimum + ((self.maximum - self.minimum) * ratio)

    def handle_rect(self) -> Rect:
        pixel = self._to_pixel(self.value)
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(pixel - (self.handle_size // 2), self.rect.centery - (self.handle_size // 2), self.handle_size, self.handle_size)
        return Rect(self.rect.centerx - (self.handle_size // 2), pixel - (self.handle_size // 2), self.handle_size, self.handle_size)

    def _build_lock_rect(self, pointer_pos) -> Rect:
        travel = self._travel_rect()
        if self.axis == LayoutAxis.HORIZONTAL:
            return Rect(travel.left, pointer_pos[1], travel.width + 1, 1)
        return Rect(pointer_pos[0], travel.top, 1, travel.height + 1)

    def handle_event(self, event, app) -> bool:
        raw = getattr(event, "pos", None)
        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            if isinstance(raw, tuple) and len(raw) == 2 and self.handle_rect().collidepoint(raw):
                handle = self.handle_rect()
                if self.axis == LayoutAxis.HORIZONTAL:
                    self._drag_anchor_offset = raw[0] - handle.x
                else:
                    self._drag_anchor_offset = raw[1] - handle.y
                app.pointer_capture.begin(self.control_id, self._build_lock_rect(raw))
                self.dragging = True
                return True

        if event.type == MOUSEMOTION and self.dragging and app.pointer_capture.is_owned_by(self.control_id):
            pos = app.pointer_capture.clamp(app.input_state.pointer_pos)
            if self.axis == LayoutAxis.HORIZONTAL:
                axis_pixel = pos[0] - self._drag_anchor_offset + (self.handle_size // 2)
            else:
                axis_pixel = pos[1] - self._drag_anchor_offset + (self.handle_size // 2)
            self.value = self._to_value(axis_pixel)
            self._clamp_value()
            return True

        if event.type == MOUSEBUTTONUP and getattr(event, "button", None) == 1 and self.dragging:
            self.dragging = False
            app.pointer_capture.end(self.control_id)
            return True

        if event.type == MOUSEWHEEL and self.rect.collidepoint(app.input_state.pointer_pos):
            self.value += float(getattr(event, "y", 0)) * ((self.maximum - self.minimum) * 0.05)
            self._clamp_value()
            return True
        return False

    def draw(self, surface, theme) -> None:
        travel = self._travel_rect()
        handle = self.handle_rect()
        factory = getattr(theme, "graphics_factory", None)
        if factory is None:
            draw_rect(surface, theme.dark, travel, 0)
            fill = theme.dark if self.dragging else theme.light
            draw_rect(surface, fill, handle, 0)
            draw_rect(surface, theme.dark, handle, 2)
            return
        travel_size = (travel.width, travel.height)
        handle_size = (handle.width, handle.height)
        if self._track_visuals is None or self._track_visuals_size != travel_size:
            self._track_visuals = factory.build_frame_visuals(travel)
            self._track_visuals_size = travel_size
        if self._handle_visuals is None or self._handle_visuals_size != handle_size:
            self._handle_visuals = factory.build_frame_visuals(handle)
            self._handle_visuals_size = handle_size
        surface.blit(self._track_visuals.idle, travel)
        if self.dragging:
            surface.blit(self._handle_visuals.armed, handle)
        else:
            surface.blit(self._handle_visuals.hover, handle)
