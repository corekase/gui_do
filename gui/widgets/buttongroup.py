from __future__ import annotations

from pygame import Rect
from pygame.event import Event as PygameEvent
from typing import Optional, TYPE_CHECKING
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN
from ..utility.input.normalized_event import normalize_input_event
from ..utility.events import Event, GuiError, ButtonStyle
from ..utility.intermediates.interactive import BaseInteractive, InteractiveState
from ..utility.intermediates.widget import Widget

if TYPE_CHECKING:
    from ..utility.gui_utils.gui_event import GuiEvent
    from ..utility.gui_manager import GuiManager
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
        if selection.group != self.group:
            return self.id
        selected_id = selection.id
        if not isinstance(selected_id, str) or selected_id == '':
            return self.id
        return selected_id

    def __init__(self, gui: "GuiManager", group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> None:
        """Create one selectable member of a named group."""
        if not isinstance(group, str) or group == '':
            raise GuiError('button group name must be a non-empty string')
        super().__init__(gui, id, rect)
        self.group: str = group
        visuals = self.gui.graphics_factory.build_interactive_visuals(style, text, rect)
        self.idle = visuals.idle
        self.hover = visuals.hover
        self.armed = visuals.armed
        self.disabled_graphic = visuals.disabled
        self.disabled_armed_graphic = self.gui.graphics_factory.build_disabled_bitmap(self.armed)
        self.hit_rect = visuals.hit_rect
        selected_before_register = self.gui.button_group_mediator.get_selection(group)
        self.gui.button_group_mediator.register(group, self)
        if selected_before_register is None:
            self.state = InteractiveState.Armed

    def _is_selected(self) -> bool:
        """Return True when this button is the mediator-selected member for its group."""
        selection = self.gui.button_group_mediator.get_selection(self.group)
        return selection is self

    def handle_event(self, event: PygameEvent, window: Optional["Window"]) -> bool:
        """Handle event."""
        if self.disabled:
            return False
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN):
            return False
        normalized = normalize_input_event(event)
        collision = self.get_collide(window)
        if collision:
            if self.state == InteractiveState.Idle:
                self.state = InteractiveState.Hover
            if self.state == InteractiveState.Hover:
                if event.type == MOUSEBUTTONDOWN and normalized.is_left_down:
                    self.select()
                    return True
        return False

    def build_gui_event(self, window: Optional["Window"] = None) -> "GuiEvent":
        """Emit a group-selection event with mediator-resolved selected id."""
        return self.gui.event(Event.Group, group=self.button_group, widget_id=self.button_id, window=window)

    def should_handle_outside_collision(self) -> bool:
        """Keep receiving events while selected so state can transition correctly."""
        return self.state == InteractiveState.Armed

    def draw(self) -> None:
        """Draw selected groups as selected even while disabled."""
        if self.disabled:
            Widget.draw(self)
            if self._is_selected() and self.disabled_armed_graphic is not None:
                self.surface.blit(self.disabled_armed_graphic, (self.draw_rect.x, self.draw_rect.y))
                return
            if self.disabled_graphic is not None:
                self.surface.blit(self.disabled_graphic, (self.draw_rect.x, self.draw_rect.y))
                return
        super().draw()

    def select(self) -> None:
        """Mark this button selected and clear the previous group selection."""
        previous = self.gui.button_group_mediator.get_selection(self.group)
        if previous is not None and previous is not self:
            previous.state = InteractiveState.Idle
        self.state = InteractiveState.Armed
        self.gui.button_group_mediator.select(self.group, self)
