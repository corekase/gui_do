from enum import Enum
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..bitmapfactory import BitmapFactory
from ..utility import convert_to_window
from .button import Button
from .frame import FrameState

PushButtonKind = Enum('PushButtonKind', ['BOX', 'RADIO'])

class PushButtonGroup(Button):
    # dictionary of key:value -> key, name of the group. value, list of PushButtonGroup objects
    groups = {}
    # dictionary of key:value -> key, name of the group. value, armed object
    selections = {}
    def __init__(self, id, rect, text, group, kind=PushButtonKind.BOX):
        super().__init__(id, rect, text)
        factory = BitmapFactory()
        self.group = group
        self.kind = kind
        if self.kind == PushButtonKind.BOX:
            self.box_idle, self.box_hover, self.box_armed = factory.draw_box_button_bitmaps(text, rect)
        elif self.kind == PushButtonKind.RADIO:
            self.radio_idle, self.radio_hover, self.radio_armed = factory.draw_radio_pushbutton_bitmaps(text, rect)
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
        collision = self.check_collision(convert_to_window(event.pos, window))
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

    def check_collision(self, position):
        if self.kind == PushButtonKind.BOX:
            return self.rect.collidepoint(position)
        elif self.kind == PushButtonKind.RADIO:
            collided = self.rect.collidepoint(position)
            if collided:
                if (position[0] - self.rect.left) < self.radio_idle.get_rect().width:
                    return True
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
        if self.kind == PushButtonKind.BOX:
            if self.state == FrameState.IDLE:
                self.surface.blit(self.box_idle, (self.rect.x, self.rect.y))
            elif self.state == FrameState.HOVER:
                self.surface.blit(self.box_hover, (self.rect.x, self.rect.y))
            elif self.state == FrameState.ARMED:
                self.surface.blit(self.box_armed, (self.rect.x, self.rect.y))
        elif self.kind == PushButtonKind.RADIO:
            if self.pristine == None:
                self.save_pristine()
            self.surface.blit(self.pristine, (self.rect.x, self.rect.y))
            if self.state == FrameState.IDLE:
                self.surface.blit(self.radio_idle, self.rect)
            elif self.state == FrameState.HOVER:
                self.surface.blit(self.radio_hover, self.rect)
            elif self.state == FrameState.ARMED:
                self.surface.blit(self.radio_armed, self.rect)
