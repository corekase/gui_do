from enum import Enum
from math import cos, sin, radians
import pygame
from pygame import Rect
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..utility import centre, convert_to_window
from .button import Button
from .frame import FrameState
from .widget import colours
from ..graphicfactory import GraphicFactory

PushButtonKind = Enum('PushButtonKind', ['BOX', 'RADIO'])

class PushButtonGroup(Button):
    # dictionary of key:value -> key, name of the group. value, list of PushButtonGroup objects
    groups = {}
    # dictionary of key:value -> key, name of the group. value, armed object
    selections = {}

    def __init__(self, id, rect, text, group, kind=PushButtonKind.BOX):
        super().__init__(id, rect, text)
        factory = GraphicFactory()
        self.group = group
        self.kind = kind
        if self.kind == PushButtonKind.BOX:
            self.box_idle, self.box_hover, self.box_armed = factory.draw_button_graphic(text, rect)
        elif self.kind == PushButtonKind.RADIO:
            self.radio_idle, self.radio_hover, self.radio_armed = factory.draw_radio_graphic(text, rect)
            self.transparent = True
        if group not in PushButtonGroup.groups.keys():
            # the first item added to a group is automatically selected
            PushButtonGroup.groups[group] = []
            PushButtonGroup.selections[group] = self
            self.select()
        PushButtonGroup.groups[group].append(self)
        self.add_dirty()

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            # no matching events for push button logic
            return False
        # is the mouse position within the push button rect
        collision = self.check_collision(convert_to_window(self.gui.lock_area(event.pos), window))
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
            if self.transparent:
                self.surface.blit(self.pristine, (self.rect.x, self.rect.y))
            if self.state == FrameState.IDLE:
                self.surface.blit(self.radio_idle, self.rect)
            elif self.state == FrameState.HOVER:
                self.surface.blit(self.radio_hover, self.rect)
            elif self.state == FrameState.ARMED:
                self.surface.blit(self.radio_armed, self.rect)
        self.add_dirty()

    def adjust_rect(self, bitmap):
        x, y, w, h = bitmap.get_rect()
        smaller = bitmap.get_rect().height
        offset = centre(self.rect.height, smaller)
        self.rect = Rect(self.rect.x, self.rect.y + offset, w, h)
