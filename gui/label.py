from .widget import Widget
from .utility import render_text

class Label(Widget):
    def __init__(self, position, text):
        # initialize common widget values
        self.label(text)
        rect = self.text_bitmap.get_rect()
        rect.x, rect.y = position[0], position[1]
        super().__init__('label', rect)

    def label(self, text):
        # text bitmap
        self.text_bitmap = render_text(text)

    def handle_event(self, _, _a):
        return False

    def draw(self):
        self.surface.blit(self.text_bitmap, (self.rect.x, self.rect.y))
