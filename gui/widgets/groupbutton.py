from pygame import Rect
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..bitmapfactory import BitmapFactory
from ..command import centre
from .widget import Widget
from enum import Enum

State = Enum('State', ['Idle', 'Hover', 'Armed'])

class GroupButton(Widget):
    # dictionary of key:value -> key, name of the group. value, list of PushButtonGroup objects
    groups = {}
    # dictionary of key:value -> key, name of the group. value, armed object
    selections = {}
    def __init__(self, id, rect, style, text, group):
        super().__init__(id, rect)
        self.state = State.Idle
        factory = BitmapFactory()
        self.group = group
        (self.idle, self.hover, self.armed), self.hit_rect = \
            factory.get_styled_bitmaps(style, text, rect)
        if group not in GroupButton.groups.keys():
            # the first item added to a group is automatically selected
            GroupButton.groups[group] = []
            GroupButton.selections[group] = self
            self.select()
        GroupButton.groups[group].append(self)

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            # no matching events for push button logic
            return False
        # is the mouse position within the push button rect
        collision = self.get_collide(window)
        # manage the state of the push button
        if (self.state == State.Idle) and collision:
            self.state = State.Hover
        if self.state == State.Hover:
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = State.Idle
            if (event.type == MOUSEBUTTONDOWN) and collision:
                if event.button == 1:
                    # push button was clicked
                    self.select()
                    return True
        # push button not clicked
        return False

    def select(self):
        # clear armed state for previous object
        GroupButton.selections[self.group].state = State.Idle
        # mark this object armed
        self.state = State.Armed
        # make this object the currently armed one
        GroupButton.selections[self.group] = self

    def read(self):
        # return the id of the armed pushbutton
        return GroupButton.selections[self.group].id

    def leave(self):
        # if hover then idle when left
        if self.state == State.Hover:
            self.state = State.Idle

    def draw(self):
        if self.state == State.Idle:
            self.surface.blit(self.idle, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == State.Hover:
            self.surface.blit(self.hover, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == State.Armed:
            self.surface.blit(self.armed, (self.draw_rect.x, self.draw_rect.y))
