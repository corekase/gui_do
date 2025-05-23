import pygame
from math import cos, sin, radians
from .button import Button
from .frame import State
from .utility import render_text
from .widget import colours
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from enum import Enum

PushButtonKind = Enum('PushButtonKind', ['BOX', 'RADIO', 'CHECK'])

class PushButtonGroup(Button):
    # dictionary of key:value -> key, name of the group. value, list of PushButtonGroup objects
    groups = {}
    # dictionary of key:value -> key, name of the group. value, armed object
    selections = {}

    def __init__(self, id, rect, text, group, kind=PushButtonKind.BOX):
        super().__init__(id, rect, text)
        self.group = group
        self.kind = kind
        self.idle = self.hover = self.armed = None
        if self.kind == PushButtonKind.RADIO:
            # idle radio
            self.idle = self.make_radio_bitmap(text, colours['medium'], colours['full'])
            # hover radio
            self.hover = self.make_radio_bitmap(text, colours['full'], colours['dark'], True)
            # armed radio
            self.armed = self.make_radio_bitmap(text, colours['full'], colours['dark'], True)
        elif self.kind == PushButtonKind.CHECK:
            pass
        if group not in PushButtonGroup.groups.keys():
            # the first item added to a group is automatically selected
            PushButtonGroup.groups[group] = []
            PushButtonGroup.selections[group] = self
            self.select()
        PushButtonGroup.groups[group].append(self)

    def make_radio_bitmap(self, text, col1, col2, highlight=False):
        # -> To-do: make utility functions that cache and reuse just the graphical part of the
        #           radio bitmap.  That is then combined with text in the bitmaps here
        text_bitmap = render_text(' ' + text, highlight)
        _, _, idle_width, idle_height = text_bitmap.get_rect()
        bitmap = pygame.surface.Surface((idle_height + idle_width, idle_height), pygame.SRCALPHA)
        offset = idle_height // 2
        radius = offset // 2
        points = self.make_polygon((radius, offset), radius)
        pygame.draw.polygon(bitmap, col1, points, 0)
        pygame.draw.polygon(bitmap, col2, points, 1)
        bitmap.blit(text_bitmap, (radius * 2, 0))
        return bitmap

    def make_polygon(self, position, radius):
        points = []
        x, y = position
        for point in range(0, 360, 1):
            x1 = round(radius * cos(radians(point)))
            y1 = round(radius * sin(radians(point)))
            points += [(x + x1, y + y1)]
        return points

    def handle_event(self, event):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            # no matching events for push button logic
            return False
        # is the mouse position within the push button rect
        collision = self.check_collision(event.pos)
        # manage the state of the push button
        if (self.state == State.IDLE) and collision:
            self.state = State.HOVER
        if self.state == State.HOVER:
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = State.IDLE
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
                if (position[0] - self.rect.left) < self.idle.get_rect().width:
                    return True
            return False
        elif self.kind == PushButtonKind.CHECK:
            return self.rect.collidepoint(position)

    def select(self):
        # clear armed state for previous object
        PushButtonGroup.selections[self.group].state = State.IDLE
        # mark this object armed
        self.state = State.ARMED
        # make this object the currently armed one
        PushButtonGroup.selections[self.group] = self

    def read(self):
        # return the id of the armed pushbutton
        return PushButtonGroup.selections[self.group].id

    def draw(self):
        if self.kind == PushButtonKind.BOX:
            super().draw()
        elif (self.kind == PushButtonKind.RADIO) or (self.kind == PushButtonKind.CHECK):
            if self.state == State.IDLE:
                self.surface.blit(self.idle, self.rect)
            elif self.state == State.HOVER:
                self.surface.blit(self.hover, self.rect)
            elif self.state == State.ARMED:
                self.surface.blit(self.armed, self.rect)