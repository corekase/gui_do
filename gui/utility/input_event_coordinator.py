from typing import Iterable, TYPE_CHECKING

from .constants import Event
from .gui_event import GuiEvent

if TYPE_CHECKING:
    from .guimanager import GuiManager


class InputEventCoordinator:
    """Owns GuiEvent construction and filtered event stream production."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def event(self, event_type: Event, **kwargs: object) -> "GuiEvent":
        if event_type in (Event.MouseButtonUp, Event.MouseButtonDown, Event.MouseMotion):
            kwargs.setdefault('pos', self.gui.get_mouse_pos())
        return GuiEvent(event_type, **kwargs)

    def events(self) -> Iterable["GuiEvent"]:
        for raw_event in self.gui.input_providers.event_getter():
            event = self.gui.handle_event(raw_event)
            if event.type == Event.Pass:
                continue
            yield event
