from pygame import Rect

from ..core.ui_node import UiNode


class LabelControl(UiNode):
    """Simple text label control."""

    def __init__(self, control_id: str, rect: Rect, text: str) -> None:
        super().__init__(control_id, rect)
        self.text = text
        self.title = False
        self.text_size = 16

    def draw(self, surface, theme) -> None:
        rendered = theme.render_text(self.text, size=self.text_size, title=self.title, shadow=True)
        surface.blit(rendered, self.rect.topleft)
