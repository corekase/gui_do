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
        self.pressed = pressed
        if self.pressed == True:
            self.state = FrameState.ARMED
        else:
            self.state = FrameState.IDLE
        factory = BitmapFactory()
        self.text1_idle, self.text1_hover, self.text1_armed = factory.draw_button_bitmaps(pressed_text, rect)
        self.text2_idle, self.text2_hover, self.text2_armed = factory.draw_button_bitmaps(raised_text, rect)

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            # no matching events for toggle button logic
            return False
        # is the mouse position within the toggle button rect
        collision = self.rect.collidepoint(convert_to_window(self.gui.lock_area(event.pos), window))
        # manage the state of the toggle button
        if (self.state == FrameState.IDLE) and collision:
            self.state = FrameState.HOVER
        if self.state == FrameState.HOVER:
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = FrameState.IDLE
            if (event.type == MOUSEBUTTONDOWN) and collision:
                if event.button == 1:
                    # button was clicked
                    self.pressed = not self.pressed
                    return True
        # button not clicked
        return False

    def draw(self):
        if self.pressed:
            self.surface.blit(self.text1_armed, self.rect)
        else:
            self.surface.blit(self.text2_idle, self.rect)

    def read(self):
        # return the state of the button as a bool
        return self.pressed
