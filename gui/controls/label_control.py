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
        factory = getattr(theme, "graphics_factory", None)
        if factory is not None:
            old = factory.get_current_font_name()
            factory.set_font("titlebar" if self.title else "normal")
            try:
                rendered = factory.render_text(self.text, colour=theme.text, shadow=True)
            finally:
                while factory.get_current_font_name() != old:
                    factory.set_last_font()
        else:
            rendered = theme.render_text(self.text, size=self.text_size, title=self.title, shadow=True)
        surface.blit(rendered, self.rect.topleft)
