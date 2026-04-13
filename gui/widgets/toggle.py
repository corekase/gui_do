from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..constants import GType
from .widget import Widget
from ..bitmapfactory import BitmapFactory
from enum import Enum

State = Enum('State', ['Idle', 'Hover', 'Armed'])
from ..widgets.registry import register_widget

@register_widget("Toggle")
class Toggle(Widget):
    def __init__(self, gui, id, rect, style, pushed, pressed_text, raised_text=None):
        super().__init__(gui, id, rect)
        self.GType = GType.Toggle
        self.pushed = pushed
        self.state = State.Idle
        if raised_text == None:
            raised_text = pressed_text
        factory = self.gui.get_bitmapfactory()
        (_, _, self.pressed_text_bitmap), rect1 = \
            factory.get_styled_bitmaps(style, pressed_text, rect)
        (self.raised_text_bitmap, self.hovered_bitmap, _), rect2 = \
            factory.get_styled_bitmaps(style, raised_text, rect)
        # out of rect1 or rect2 choose the longer width
        if rect1.width > rect2.width:
            self.hit_rect = rect1
        else:
            self.hit_rect = rect2

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            return False
        collision = self.get_collide(window)
        # manage the state of the push button
        if (self.state == State.Idle) and collision:
            self.state = State.Hover
        elif not collision:
            self.state = State.Idle
        if self.state == State.Hover:
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = State.Idle
            if (event.type == MOUSEBUTTONDOWN) and collision:
                if event.button == 1:
                    # push button was clicked
                    self.pushed = not self.pushed
                    return True
        # button not clicked
        return False

    def draw(self):
        if self.pushed:
            self.surface.blit(self.pressed_text_bitmap, self.draw_rect)
        else:
            if self.state == State.Hover:
                self.surface.blit(self.hovered_bitmap, self.draw_rect)
            elif self.state == State.Idle:
                self.surface.blit(self.raised_text_bitmap, self.draw_rect)

    def leave(self):
        self.state = State.Idle

    def set(self, pushed):
        # set the boolean of the togglebutton
        self.pushed = pushed

    def read(self):
        # return the state of the button as a bool
        return self.pushed
