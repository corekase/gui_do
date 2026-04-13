from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..values.constants import GType
from .interactive import BaseInteractive, State
from ..widgets.registry import register_widget

@register_widget("ButtonGroup")
class ButtonGroup(BaseInteractive):
    # dictionary of key:value -> key, name of the group. value, list of PushButtonGroup objects
    groups = {}
    # dictionary of key:value -> key, name of the group. value, armed object
    selections = {}
    def __init__(self, gui, group, id, rect, style, text):
        super().__init__(gui, id, rect)
        self.GType = GType.ButtonGroup
        factory = self.gui.get_bitmapfactory()
        self.group = group
        (self.idle, self.hover, self.armed), self.hit_rect = \
            factory.get_styled_bitmaps(style, text, rect)
        if group not in ButtonGroup.groups.keys():
            # the first item added to a group is automatically selected
            ButtonGroup.groups[group] = []
            ButtonGroup.selections[group] = self
            self.select()
        ButtonGroup.groups[group].append(self)

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            return False
        
        # Call base logic to update state (Hover/Idle)
        collision = self.get_collide(window)
        if not collision:
            if self.state != State.Armed:
                self.state = State.Idle
            return False
        
        if self.state != State.Armed:
            self.state = State.Hover
            
        if self.state == State.Hover:
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                self.select()
                return True
        return False

    def select(self):
        # clear armed state for previous object
        ButtonGroup.selections[self.group].state = State.Idle
        # mark this object armed
        self.state = State.Armed
        # make this object the currently armed one
        ButtonGroup.selections[self.group] = self

    def read_id(self):
        return ButtonGroup.selections[self.group].id

    def read_group(self):
        return self.group
