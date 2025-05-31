from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from .button import Button
from .frame import FrameState
from ..bitmapfactory import BitmapFactory
from ..utility import convert_to_window

class ToggleButton(Button):
    def __init__(self, id, rect, pressed, pressed_text, raised_text=None):
        super().__init__(id, rect, 'None')
        if raised_text == None:
            raised_text = pressed_text
        if pressed:
            self.pushed = FrameState.ARMED
        else:
            self.pushed = FrameState.IDLE
        factory = BitmapFactory()
        self.text1_idle, _, self.text1_armed = factory.draw_button_bitmaps(pressed_text, rect)
        self.text2_idle, _, self.text2_armed = factory.draw_button_bitmaps(raised_text, rect)

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            # no matching events for toggle button logic
            return False
        # manage the state of the toggle button
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(convert_to_window(event.pos, window)):
                    # button was clicked
                    if self.pushed == FrameState.ARMED:
                        self.pushed = FrameState.IDLE
                    elif self.pushed == FrameState.IDLE:
                        self.pushed = FrameState.ARMED
                    return True
        # button not clicked
        return False

    def draw(self):
        if self.pushed == FrameState.ARMED:
            self.surface.blit(self.text1_armed, self.rect)
        else:
            self.surface.blit(self.text2_idle, self.rect)

    def read(self):
        # return the state of the button as a bool
        return self.pushed == FrameState.ARMED
