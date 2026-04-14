from ..values.constants import colours, WidgetKind
from .utility.widget import Widget
from pygame import Rect
from .utility.registry import register_widget

@register_widget("Label")
class Label(Widget):
    def __init__(self, gui, position, text, shadow=False):
        super().__init__(gui, 'label', Rect(0, 0, 0, 0))
        # initialize common widget values
        self.shadow = shadow
        self.font = self.gui.bitmap_factory.get_current_font_name()
        self.render(text)
        self.rect = self.text_bitmap.get_rect()
        if len(position) == 2:
            self.rect.x, self.rect.y = position[0], position[1]
        else:
            x = position[0] + self.gui.bitmap_factory.centre(position[2], self.rect.width)
            y = position[1] + self.gui.bitmap_factory.centre(position[3], self.rect.height)
            self.rect.x, self.rect.y = x, y
        self.WidgetKind = WidgetKind.Label

    def set_label(self, text):
        # text bitmap
        self.gui.bitmap_factory.set_font(self.font)
        self.render(text)
        self.gui.bitmap_factory.set_last_font()

    def render(self, text):
        if self.shadow:
            self.text_bitmap = self.gui.bitmap_factory.render_text(text, colours['text'], True)
        else:
            self.text_bitmap = self.gui.bitmap_factory.render_text(text)

    def handle_event(self, _, _a):
        return False

    def draw(self):
        self.surface.blit(self.text_bitmap, (self.rect.x, self.rect.y))
