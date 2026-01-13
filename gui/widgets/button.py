from pygame import Rect
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..guimanager import GuiManager
from ..bitmapfactory import BitmapFactory
from ..timers import Timers
from ..command import centre
from .widget import Widget
from enum import Enum

State = Enum('State', ['Idle', 'Hover', 'Armed'])

class Button(Widget):
    def __init__(self, id, rect, style, text, button_callback=None, skip_factory=False):
        # initialize common widget values
        super().__init__(id, rect)
        self.gui = GuiManager()
        # this object's timer
        self.timer = None
        if not skip_factory:
            factory = BitmapFactory()
            self.idle, self.hover, self.armed = factory.get_styled_bitmaps(style, text, rect)
            if style == 2 or style == 3:
                containing_rect = self.idle.get_rect()
                y_offset = centre(self.rect.height, containing_rect.height)
                self.rect = Rect(self.rect.x, self.rect.y + y_offset,
                                containing_rect.width, containing_rect.height)
        self.state = State.Idle
        # button specific callback, this callback is separate from the add() callback
        self.button_callback = button_callback
        # whether the mouse position is in collision with this rect
        self.active = False

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            # no matching events for button logic
            return False
        # is the mouse position within the button rect
        collision = self.get_collide(window)
        if not collision:
            if self.timer != None:
                self.gui.timers.remove_timer(self.timer)
                self.timer = None
            self.state = State.Idle
            return False
        # manage the state of the button
        if self.state == State.Idle:
            self.state = State.Hover
        if self.state == State.Hover:
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.state = State.Armed
                    if self.button_callback != None:
                        self.button_callback()
                        if self.timer == None:
                            self.timer = self.gui.timers.add_timer(self.button_callback, 0.15)
                    # don't signal a widget change, consume the signal by returning False
                    return False
        if self.state == State.Armed:
            if event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    # button clicked
                    if self.timer != None:
                        self.gui.timers.remove_timer(self.timer)
                        self.timer = None
                    self.state = State.Hover
                    if self.button_callback != None:
                        # if a callback exists, consume the event
                        return False
                    # no callback, signal event
                    return True
        # button not clicked
        return False

    def leave(self):
        if self.timer != None:
            self.gui.timers.remove_timer(self.timer)
            self.timer = None
        self.state = State.Idle

    def draw(self):
        if self.state == State.Idle:
            self.surface.blit(self.idle, (self.rect.x, self.rect.y))
        elif self.state == State.Hover:
            self.surface.blit(self.hover, (self.rect.x, self.rect.y))
        elif self.state == State.Armed:
            self.surface.blit(self.armed, (self.rect.x, self.rect.y))
