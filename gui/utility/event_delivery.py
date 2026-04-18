from typing import Hashable, Optional, TYPE_CHECKING, cast

from .constants import Event
from ..widgets.window import Window as gWindow

if TYPE_CHECKING:
    from .guimanager import BaseEvent, GuiManager


class EventDeliveryCoordinator:
    """Owns GuiEvent delivery policy across task owners, panel, windows, and screen."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def dispatch_event(self, event: "BaseEvent") -> None:
        task_owner = self.resolve_task_event_owner(event)
        if task_owner is not None:
            task_owner.handle_event(event)
            return
        if getattr(event, 'task_panel', False):
            if self.gui.task_panel is not None and self.gui.task_panel.visible:
                self.gui.task_panel.handle_event(event)
                return
        event_window = getattr(event, 'window', None)
        if not isinstance(event_window, gWindow):
            event_window = None
        if event_window is not None and event_window in self.gui.windows and event_window.visible:
            event_window.handle_event(event)
            return
        self.gui._screen_event_handler(event)

    def resolve_task_event_owner(self, event: "BaseEvent") -> Optional[gWindow]:
        if getattr(event, 'type', None) != Event.Task:
            return None
        task_id = cast(Optional[Hashable], getattr(event, 'id', None))
        if task_id is None:
            return None
        try:
            hash(task_id)
        except TypeError:
            return None
        owner = self.gui._task_owner_by_id.get(task_id)
        if owner is None:
            return None
        if owner not in self.gui.windows or not owner.visible:
            return None
        return owner
