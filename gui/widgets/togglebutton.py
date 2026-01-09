from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN
from .widget import Widget
from ..bitmapfactory import BitmapFactory
from ..command import centre

class ToggleButton(Widget):
    def __init__(self, id, rect, style, pushed, pressed_text, raised_text=None):
        super().__init__(id, rect)
        self.pushed = pushed
        if raised_text == None:
            raised_text = pressed_text
        factory = BitmapFactory()
        _, _, self.pressed_text_bitmap = factory.get_pushbutton_style_bitmaps(style, pressed_text, rect)
        self.raised_text_bitmap, _, _ = factory.get_pushbutton_style_bitmaps(style, raised_text, rect)
        if style != 0:
            self.rect = Rect(rect.x, rect.y + centre(self.rect.height, self.raised_text_bitmap.get_rect().height),
                             self.raised_text_bitmap.get_rect().width, rect.height)

    def handle_event(self, event, window):
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.get_collide(window):
                    # button was clicked
                    self.pushed = not self.pushed
                    return True
        # button not clicked
        return False

    def draw(self):
        if self.pushed:
            self.surface.blit(self.pressed_text_bitmap, self.rect)
        else:
            self.surface.blit(self.raised_text_bitmap, self.rect)

    def set(self, pushed):
        # set the boolean of the togglebutton
        self.pushed = pushed

    def read(self):
        # return the state of the button as a bool
        return self.pushed
