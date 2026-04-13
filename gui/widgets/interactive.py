from enum import Enum
from .widget import Widget
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP

State = Enum('State', ['Idle', 'Hover', 'Armed'])

class BaseInteractive(Widget):
    def __init__(self, gui, id, rect):
        super().__init__(gui, id, rect)
        self.state = State.Idle
        self.idle = None
        self.hover = None
        self.armed = None

    def handle_event(self, event, window):
        collision = self.get_collide(window)
        if not collision:
            if self.state != State.Armed:
                self.state = State.Idle
            return False
        
        if self.state == State.Idle:
            self.state = State.Hover
        return True

    def leave(self):
        if self.state != State.Armed:
            self.state = State.Idle

    def draw(self):
        super().draw()
        if self.state == State.Idle and self.idle:
            self.surface.blit(self.idle, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == State.Hover and self.hover:
            self.surface.blit(self.hover, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == State.Armed and self.armed:
            self.surface.blit(self.armed, (self.draw_rect.x, self.draw_rect.y))
