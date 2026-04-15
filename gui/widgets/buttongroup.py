from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Dict, List, Optional, TYPE_CHECKING
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..utility.constants import ButtonStyle, WidgetKind
from ..utility.interactive import BaseInteractive, InteractiveState

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

class ButtonGroup(BaseInteractive):
    """A radio-button style group widget.

    Mutually exclusive buttons where only one button in a group can be selected
    at a time. Automatically tracks the currently selected button per group.

    Class Attributes:
        groups: Dictionary mapping group names to lists of ButtonGroup instances.
        selections: Dictionary mapping group names to currently selected button.
    """
    # dictionary of key:value -> key, name of the group. value, list of PushButtonGroup objects
    groups: Dict[str, List["ButtonGroup"]] = {}
    # dictionary of key:value -> key, name of the group. value, armed object
    selections: Dict[str, "ButtonGroup"] = {}

    def __init__(self, gui: "GuiManager", group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> None:
        """Initialize a button group member.

        Args:
            gui: Reference to GuiManager.
            group: Name of the button group this button belongs to.
            id: Unique identifier for this button.
            rect: Rect defining button position and size.
            style: ButtonStyle enum value for visual style.
            text: Text to display on button.
        """
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

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
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
        """Select this button, deselecting the previously selected button in the group.

        This is called automatically when the button is clicked, but can also be
        called programmatically to change the selection.
        """
        # clear armed state for previous object
        ButtonGroup.selections[self.group].state = InteractiveState.Idle
        # mark this object armed
        self.state = InteractiveState.Armed
        # make this object the currently armed one
        ButtonGroup.selections[self.group] = self

    def read_group(self) -> str:
        """Get the group name for this button.

        Returns:
            The group name string.
        """
        return self.group

    def read_id(self) -> str:
        """Get the ID of the currently selected button in this group.

        Returns:
            The ID of the selected button.
        """
        return ButtonGroup.selections[self.group].id
