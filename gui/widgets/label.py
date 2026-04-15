from typing import Optional, Tuple, Union, Any
from ..utility.constants import colours, WidgetKind
from ..utility.widget import Widget
from pygame import Rect

class Label(Widget):
    """A non-interactive text label widget.

    Renders text to the GUI with optional shadow effect. Labels do not respond to
    user input and cannot be activated.
    """
    def __init__(self, gui: Any, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False) -> None:
        super().__init__(gui, 'label', Rect(0, 0, 0, 0))
        # initialize common widget values
        self.shadow: bool = shadow
        self._font: Optional[str] = self.gui.bitmap_factory.get_current_font_name()
        self._text_bitmap: Any
        self._render(text)
        self.draw_rect = self._text_bitmap.get_rect()
        if len(position) == 2:
            self.draw_rect.x, self.draw_rect.y = position[0], position[1]
        else:
            x = position[0] + self.gui.bitmap_factory.centre(position[2], self.draw_rect.width)
            y = position[1] + self.gui.bitmap_factory.centre(position[3], self.draw_rect.height)
            self.draw_rect.x, self.draw_rect.y = x, y
        self.WidgetKind = WidgetKind.Label

    def _render(self, text: str) -> None:
        if self.shadow:
            self._text_bitmap = self.gui.bitmap_factory.render_text(text, colours['text'], True)
        else:
            self._text_bitmap = self.gui.bitmap_factory.render_text(text)

    def set_label(self, text: str) -> None:
        # text bitmap
        self.gui.bitmap_factory.set_font(self._font)
        self._render(text)
        self.gui.bitmap_factory.set_last_font()

    def draw(self) -> None:
        """Draw the label text to the surface."""
        self.surface.blit(self._text_bitmap, (self.draw_rect.x, self.draw_rect.y))

    def handle_event(self, _, _a) -> bool:
        return False
