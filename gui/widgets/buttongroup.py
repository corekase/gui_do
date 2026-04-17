from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Optional, TYPE_CHECKING
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..utility.constants import Event, GuiError, ButtonStyle
from ..utility.interactive import BaseInteractive, InteractiveState

if TYPE_CHECKING:
    from ..utility.guimanager import GuiEvent
    from ..utility.guimanager import GuiManager
    from .window import Window

class ButtonGroup(BaseInteractive):
    """Radio-style button that shares exclusive selection within a group."""

    @property
    def button_group(self) -> str:
        """Return this button's group name."""
        return self.group

    @property
    def button_id(self) -> str:
        """Return the selected button id for this group."""
        selection = self.gui.button_group_mediator.get_selection(self.group)
        if selection is None:
            return self.id
        if getattr(selection, 'group', None) != self.group:
            return self.id
        selected_id = getattr(selection, 'id', None)
        if not isinstance(selected_id, str) or selected_id == '':
            return self.id
        return selected_id

    def __init__(self, gui: "GuiManager", group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> None:
        """Create one selectable member of a named group."""
        if not isinstance(group, str) or group == '':
            raise GuiError('button group name must be a non-empty string')
        super().__init__(gui, id, rect)
        self.group: str = group
        (self.idle, self.hover, self.armed), self.hit_rect = \
            self.gui.bitmap_factory.get_styled_bitmaps(style, text, rect)
        self.gui.button_group_mediator.register(group, self)
        if self.gui.button_group_mediator.get_selection(group) is self:
            self.select()

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            return False
        collision = self.get_collide(window)
        if collision:
            if self.state == InteractiveState.Idle:
                self.state = InteractiveState.Hover
            if self.state == InteractiveState.Hover:
                if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', None) == 1:
                    self.select()
                    return True
        return False

    def build_gui_event(self, window: Optional["Window"] = None) -> "GuiEvent":
        """Emit a group-selection event with mediator-resolved selected id."""
        return self.gui.event(Event.Group, group=self.button_group, widget_id=self.button_id, window=window)

    def should_handle_outside_collision(self) -> bool:
        """Keep receiving events while selected so state can transition correctly."""
        return self.state == InteractiveState.Armed

    def select(self) -> None:
        """Mark this button selected and clear the previous group selection."""
        previous = self.gui.button_group_mediator.get_selection(self.group)
        if previous is not None and previous is not self:
            previous.state = InteractiveState.Idle
        self.state = InteractiveState.Armed
        self.gui.button_group_mediator.select(self.group, self)
