from pygame.locals import MOUSEBUTTONDOWN
from .widget import Widget
from ..bitmapfactory import BitmapFactory
from ..utility import convert_to_window

class ToggleButton(Widget):
    def __init__(self, id, rect, pushed, pressed_text, raised_text=None):
        from ..guimanager import GuiManager
        self.gui = GuiManager()
        super().__init__(id, rect)
        self.pushed = pushed
        if raised_text == None:
            raised_text = pressed_text
        factory = BitmapFactory()
        _, _, self.pressed_text_bitmap = factory.draw_button_bitmaps(pressed_text, rect)
        self.raised_text_bitmap, _, _ = factory.draw_button_bitmaps(raised_text, rect)

    def handle_event(self, event, window):
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(convert_to_window(self.gui.lock_area(event.pos), window)):
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

    def read(self):
        # return the state of the button as a bool
        return self.pushed
