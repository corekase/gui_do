from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.surface import Surface
from typing import Optional, Tuple, Union, TYPE_CHECKING
from ..utility.constants import colours
from ..utility.widget import Widget

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

class Label(Widget):
    """Non-interactive text widget."""

    def __init__(self, gui: "GuiManager", id: str, position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False) -> None:
        super().__init__(gui, id, Rect(0, 0, 0, 0))
        self.shadow: bool = shadow
        self._font: Optional[str] = self.gui.graphics_factory.get_current_font_name()
        self._text_bitmap: Surface
        self._render(text)
        self.draw_rect = self._text_bitmap.get_rect()
        if len(position) == 2:
            self.draw_rect.x, self.draw_rect.y = position[0], position[1]
        else:
            x = position[0] + self.gui.graphics_factory.centre(position[2], self.draw_rect.width)
            y = position[1] + self.gui.graphics_factory.centre(position[3], self.draw_rect.height)
            self.draw_rect.x, self.draw_rect.y = x, y

    def set_label(self, text: str) -> None:
        if self._font is not None:
            self.gui.graphics_factory.set_font(self._font)
            self._render(text)
            self.gui.graphics_factory.set_last_font()
        else:
            self._render(text)

    def handle_event(self, _: PygameEvent, _a: Optional["Window"]) -> bool:
        return False
    def draw(self) -> None:
        super().draw()
        self.surface.blit(self._text_bitmap, (self.draw_rect.x, self.draw_rect.y))

    def _render(self, text: str) -> None:
        if self.shadow:
            self._text_bitmap = self.gui.graphics_factory.render_text(text, colours['text'], True)
        else:
            self._text_bitmap = self.gui.graphics_factory.render_text(text)
