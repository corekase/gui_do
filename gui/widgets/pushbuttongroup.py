from pygame import Rect
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..bitmapfactory import BitmapFactory
from ..utility import convert_to_window
from .button import Button
from .frame import FrameState

class PushButtonGroup(Button):
    # dictionary of key:value -> key, name of the group. value, list of PushButtonGroup objects
    groups = {}
    # dictionary of key:value -> key, name of the group. value, armed object
    selections = {}
    def __init__(self, id, rect, text, group, style):
        super().__init__(id, rect, text)
        factory = BitmapFactory()
        self.group = group
        self.style = style
        self.idle, self.hover, self.armed = factory.get_pushbutton_style_bitmaps(style, text, rect)
        self.rect = Rect(rect.x, rect.y, self.idle.get_rect().width, self.idle.get_rect().height)
        if group not in PushButtonGroup.groups.keys():
            # the first item added to a group is automatically selected
            PushButtonGroup.groups[group] = []
            PushButtonGroup.selections[group] = self
            self.select()
        PushButtonGroup.groups[group].append(self)

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            # no matching events for push button logic
            return False
        # is the mouse position within the push button rect
        collision = self.rect.collidepoint(convert_to_window(event.pos, window))
        # manage the state of the push button
        if (self.state == FrameState.IDLE) and collision:
            self.state = FrameState.HOVER
        if self.state == FrameState.HOVER:
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = FrameState.IDLE
            if (event.type == MOUSEBUTTONDOWN) and collision:
                if event.button == 1:
                    # push button was clicked
                    self.select()
                    return True
        # push button not clicked
        return False

    def select(self):
        # clear armed state for previous object
        PushButtonGroup.selections[self.group].state = FrameState.IDLE
        # mark this object armed
        self.state = FrameState.ARMED
        # make this object the currently armed one
        PushButtonGroup.selections[self.group] = self

    def read(self):
        # return the id of the armed pushbutton
        return PushButtonGroup.selections[self.group].id

    def leave(self):
        # if hover then idle when left
        if self.state == FrameState.HOVER:
            self.state = FrameState.IDLE

    def draw(self):
        if self.style == 1:
            if self.pristine == None:
                self.save_pristine()
            self.surface.blit(self.pristine, (self.rect.x, self.rect.y))
        if self.state == FrameState.IDLE:
            self.surface.blit(self.idle, (self.rect.x, self.rect.y))
        elif self.state == FrameState.HOVER:
            self.surface.blit(self.hover, (self.rect.x, self.rect.y))
        elif self.state == FrameState.ARMED:
            self.surface.blit(self.armed, (self.rect.x, self.rect.y))
