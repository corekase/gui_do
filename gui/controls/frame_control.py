from pygame import Rect
from pygame.draw import rect as draw_rect

from ..core.ui_node import UiNode


class FrameControl(UiNode):
    """Decorative frame control."""

    def __init__(self, control_id: str, rect: Rect, border_width: int = 1) -> None:
        super().__init__(control_id, rect)
        self.border_width = max(1, int(border_width))
        self._visuals = None

    def draw(self, surface, theme) -> None:
        factory = getattr(theme, "graphics_factory", None)
        if factory is None:
            draw_rect(surface, theme.medium, self.rect, 0)
            draw_rect(surface, theme.dark, self.rect, self.border_width)
            return
        if self._visuals is None:
            self._visuals = factory.build_frame_visuals(self.rect)
        if not self.enabled:
            surface.blit(self._visuals.disabled, self.rect)
        else:
            surface.blit(self._visuals.idle, self.rect)
