from .button import Button
from .frame import State
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN

class PushButtonGroup(Button):
    # dictionary of key:value -> key is the name of the group. value is a list of
    # PushButtonGroup objects
    groups = {}
    # dictionary of which id is selected for each group
    selections = {}

    def __init__(self, id, rect, text, group):
        super().__init__(id, rect, text)
        self.group = group
        if group not in PushButtonGroup.groups.keys():
            # the first item added to a group is automatically selected
            PushButtonGroup.groups[group] = []
            PushButtonGroup.selections[group] = self
            self.select()
        PushButtonGroup.groups[group].append(self)

    def handle_event(self, event):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            # no matching events for push button logic
            return False
        # is the mouse position within the push button rect
        collision = self.rect.collidepoint(event.pos)
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

    def select(self):
        # clear all other armed states in the group
        PushButtonGroup.selections[self.group].state = State.IDLE
        # mark this item armed
        self.state = State.ARMED
        # make this id the currently selected one
        PushButtonGroup.selections[self.group] = self

    def read(self):
        # return the id of the active pushbutton
        return PushButtonGroup.selections[self.group].id

    def draw(self):
        super().draw()
