from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..guimanager import GuiManager
from ..utility import convert_to_window
from ..bitmapfactory import BitmapFactory
from .widget import Widget
from enum import Enum

State = Enum('State', ['Idle', 'Hover', 'Armed'])

class Button(Widget):
    def __init__(self, id, rect, text, callback=None):
        # initialize common widget values
        super().__init__(id, rect)
        self.gui = GuiManager()
        factory = BitmapFactory()
        self.idle, self.hover, self.armed = factory.draw_box_button_bitmaps(text, rect)
        self.state = State.Idle
        self.callback = callback

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            # no matching events for button logic
            return False
        # is the mouse position within the button rect
        collision = self.rect.collidepoint(convert_to_window(event.pos, window))
        # manage the state of the button
        if (self.state == State.Idle) and collision:
            self.state = State.Hover
        if self.state == State.Hover:
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = State.Idle
            if (event.type == MOUSEBUTTONDOWN) and collision:
                if event.button == 1:
                    self.state = State.Armed
        if self.state == State.Armed:
            if (event.type == MOUSEBUTTONUP) and collision:
                if event.button == 1:
                    # button clicked
                    self.state = State.Idle
                    # invoke callback if present
                    if self.callback != None:
                        self.callback()
                    return True
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = State.Idle
        # button not clicked
        return False

    def leave(self):
        self.state = State.Idle

    def draw(self):
        if self.state == State.Idle:
            self.surface.blit(self.idle, (self.rect.x, self.rect.y))
        elif self.state == State.Hover:
            self.surface.blit(self.hover, (self.rect.x, self.rect.y))
        elif self.state == State.Armed:
            self.surface.blit(self.armed, (self.rect.x, self.rect.y))
