from ..constants import colours, GType
from ..command import render_text, render_text, centre
from .widget import Widget

class Label(Widget):
    def __init__(self, position, text, shadow=False):
        # initialize common widget values
        self.shadow = shadow
        self.render(text)
        self.rect = self.text_bitmap.get_rect()
        if len(position) == 2:
            self.rect.x, self.rect.y = position[0], position[1]
        else:
            x = position[0] + centre(position[2], self.rect.width)
            y = position[1] + centre(position[3], self.rect.height)
            self.rect.x, self.rect.y = x, y
        super().__init__('label', self.rect)
        self.GType = GType.Label

    def set_label(self, text):
        # text bitmap
        self.render(text)

    def render(self, text):
        if self.shadow:
            self.text_bitmap = render_text(text, colours['text'], True)
        else:
            self.text_bitmap = render_text(text)

    def handle_event(self, _, _a):
        return False

    def draw(self):
        self.surface.blit(self.text_bitmap, (self.rect.x, self.rect.y))
