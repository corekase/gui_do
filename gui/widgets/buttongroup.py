from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Optional, TYPE_CHECKING
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..utility.constants import ButtonStyle, WidgetKind
from ..utility.interactive import BaseInteractive, InteractiveState
from ..utility.constants import GuiError

if TYPE_CHECKING:
    from ..utility.guimanager import GuiManager
    from .window import Window

class ButtonGroup(BaseInteractive):
    """A radio-button style group widget.

    Mutually exclusive buttons where only one button in a group can be selected
    at a time. Automatically tracks the currently selected button per group.

    Selection state is managed per GuiManager instance.
    """
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
        if not isinstance(group, str) or group == '':
            raise GuiError('button group name must be a non-empty string')
        super().__init__(gui, id, rect)
        self.WidgetKind = WidgetKind.ButtonGroup
        self.group: str = group
        (self.idle, self.hover, self.armed), self.hit_rect = \
            self.gui.bitmap_factory.get_styled_bitmaps(style, text, rect)
        self.gui.button_group_mediator.register(group, self)
        if self.gui.button_group_mediator.get_selection(group) is self:
            # the first item added to a group is automatically selected
            self.select()

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
                if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', None) == 1:
                    self.select()
                    return True
        return False

    def select(self) -> None:
        """Select this button, deselecting the previously selected button in the group.

        This is called automatically when the button is clicked, but can also be
        called programmatically to change the selection.
        """
        # clear armed state for previous object
        previous = self.gui.button_group_mediator.get_selection(self.group)
        if previous is not None and previous is not self:
            previous.state = InteractiveState.Idle
        # mark this object armed
        self.state = InteractiveState.Armed
        # make this object the currently armed one
        self.gui.button_group_mediator.select(self.group, self)

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
        selection = self.gui.button_group_mediator.get_selection(self.group)
        if selection is None:
            return self.id
        if getattr(selection, 'group', None) != self.group:
            return self.id
        selected_id = getattr(selection, 'id', None)
        if not isinstance(selected_id, str) or selected_id == '':
            return self.id
        return selected_id
