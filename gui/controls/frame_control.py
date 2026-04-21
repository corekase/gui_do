from pygame import Rect
from pygame.draw import rect as draw_rect

from ..core.ui_node import UiNode


class FrameControl(UiNode):
    """Decorative frame control."""

    def __init__(self, control_id: str, rect: Rect, border_width: int = 1) -> None:
        super().__init__(control_id, rect)
        self.border_width = max(1, int(border_width))

    def draw(self, surface, theme) -> None:
        draw_rect(surface, theme.medium, self.rect, 0)
        draw_rect(surface, theme.dark, self.rect, self.border_width)
