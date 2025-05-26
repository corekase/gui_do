import pygame
from math import cos, sin, radians
from pygame import Rect
from .button import Button
from .frame import State
from .utility import render_text, centre, convert_to_window
from .widget import colours
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from enum import Enum

PushButtonKind = Enum('PushButtonKind', ['BOX', 'RADIO'])

class PushButtonGroup(Button):
    # dictionary of key:value -> key, name of the group. value, list of PushButtonGroup objects
    groups = {}
    # dictionary of key:value -> key, name of the group. value, armed object
    selections = {}

    def __init__(self, id, rect, text, group, kind=PushButtonKind.BOX):
        super().__init__(id, rect, text)
        self.group = group
        self.kind = kind
        if self.kind == PushButtonKind.RADIO:
            # idle radio
            self.idle_bitmap = self.make_radio_button(text, colours['light'], colours['dark'])
            # hover radio
            self.hover_bitmap = self.make_radio_button(text, colours['highlight'], colours['dark'])
            # armed radio
            self.armed_bitmap = self.make_radio_button(text, colours['highlight'], colours['dark'])
            # adjust vertical centre
            self.adjust_rect(self.idle_bitmap)
        if group not in PushButtonGroup.groups.keys():
            # the first item added to a group is automatically selected
            PushButtonGroup.groups[group] = []
            PushButtonGroup.selections[group] = self
            self.select()
        PushButtonGroup.groups[group].append(self)

    def make_radio_button(self, text, col1, col2, highlight=False):
        # -> To-do: make utility functions that cache and reuse just the graphical part of the
        #           radio bitmap.  That is then combined with text in the bitmaps here
        text_bitmap = render_text(text, highlight)
        text_height = text_bitmap.get_rect().height
        radio_bitmap = pygame.surface.Surface((text_height, text_height), pygame.SRCALPHA)
        y_offset = int(round(text_height / 2))
        radius = text_height / 4.0
        points = []
        for point in range(0, 360, 5):
            x1 = int(round(radius * cos(radians(point))))
            y1 = int(round(radius * sin(radians(point))))
            points.append((int(radius) + x1, y_offset + y1))
        pygame.draw.polygon(radio_bitmap, col1, points, 0)
        pygame.draw.polygon(radio_bitmap, col2, points, 1)
        x_size = int((radius * 2) + 4 + text_bitmap.get_rect().width + 1)
        button_complete = pygame.surface.Surface((x_size, text_height), pygame.SRCALPHA)
        button_complete.blit(radio_bitmap, (0, 0))
        button_complete.blit(text_bitmap, (int(radius * 2) + 4, 0))
        return button_complete

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            # no matching events for push button logic
            return False
        # is the mouse position within the push button rect
        collision = self.check_collision(convert_to_window(self.gui.lock_area(event.pos), window))
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
                if (position[0] - self.rect.left) < self.idle_bitmap.get_rect().width:
                    return True
            return False

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
        elif self.kind == PushButtonKind.RADIO:
            if self.state == State.IDLE:
                self.surface.blit(self.idle_bitmap, self.rect)
            elif self.state == State.HOVER:
                self.surface.blit(self.hover_bitmap, self.rect)
            elif self.state == State.ARMED:
                self.surface.blit(self.armed_bitmap, self.rect)

    def adjust_rect(self, bitmap):
        x, y, w, h = self.rect
        smaller = bitmap.get_rect().height
        offset = centre(h, smaller)
        self.rect = Rect(x, y + offset, w, h)
