from typing import Any, Dict, List
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..utility.values.constants import WidgetKind
from ..utility.interactive import BaseInteractive, InteractiveState

class ButtonGroup(BaseInteractive):
    # dictionary of key:value -> key, name of the group. value, list of PushButtonGroup objects
    groups: Dict[str, List["ButtonGroup"]] = {}
    # dictionary of key:value -> key, name of the group. value, armed object
    selections: Dict[str, "ButtonGroup"] = {}

    def __init__(self, gui: Any, group: str, id: Any, rect: Any, style: Any, text: str) -> None:
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.ButtonGroup
        self.group: str = group
        (self.idle, self.hover, self.armed), self.hit_rect = \
            self.gui.bitmap_factory.get_styled_bitmaps(style, text, rect)
        if group not in ButtonGroup.groups.keys():
            # the first item added to a group is automatically selected
            ButtonGroup.groups[group] = []
            ButtonGroup.selections[group] = self
            self.select()
        ButtonGroup.groups[group].append(self)

    def handle_event(self, event: Any, window: Any) -> bool:
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            return False

        # Collision detection
        collision = self.get_collide(window)

        # Handle interaction
        if collision:
            if self.state == InteractiveState.Idle:
                self.state = InteractiveState.Hover

            if self.state == InteractiveState.Hover:
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    self.select()
                    return True
        return False

    def select(self) -> None:
        # clear armed state for previous object
        ButtonGroup.selections[self.group].state = InteractiveState.Idle
        # mark this object armed
        self.state = InteractiveState.Armed
        # make this object the currently armed one
        ButtonGroup.selections[self.group] = self

    def read_id(self) -> Any:
        return ButtonGroup.selections[self.group].id

    def read_group(self) -> str:
        return self.group
