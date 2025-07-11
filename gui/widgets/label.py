from ..command import render_text
from .widget import Widget

class Label(Widget):
    def __init__(self, position, text, minimum_xsize=None, automatic_pristine=False):
        # initialize common widget values
        self.text_bitmap = render_text(text)
        self.rect = self.text_bitmap.get_rect()
        self.rect.x, self.rect.y = position[0], position[1]
        if minimum_xsize != None:
            self.rect.width = minimum_xsize
        super().__init__('label', self.rect)
        self.auto_restore_pristine = automatic_pristine

    def set_label(self, text):
        # text bitmap
        self.text_bitmap = render_text(text)

    def handle_event(self, _, _a):
        return False

    def draw(self):
        super().draw()
        self.surface.blit(self.text_bitmap, (self.rect.x, self.rect.y))
