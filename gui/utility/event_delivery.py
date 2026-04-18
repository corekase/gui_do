from __future__ import annotations

from typing import Hashable, Optional, TYPE_CHECKING, cast

from .events import Event, GuiError
from ..widgets.window import Window as Window

if TYPE_CHECKING:
    from .gui_manager import BaseEvent, GuiManager


class EventDeliveryCoordinator:
    """Owns GuiEvent delivery policy across task owners, panel, windows, and screen."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Initialize the EventDeliveryCoordinator instance."""
        self.gui: "GuiManager" = gui_manager
        self._task_owner_by_id: dict[Hashable, Window] = {}

    def dispatch_event(self, event: "BaseEvent") -> None:
        """Run dispatch event and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        task_owner = self.resolve_task_event_owner(event)
        if task_owner is not None:
            task_owner.handle_event(event)
            return
        if getattr(event, 'task_panel', False):
            if self.gui.task_panel is not None and self.gui.task_panel.visible:
                self.gui.task_panel.handle_event(event)
                return
        event_window = getattr(event, 'window', None)
        if not isinstance(event_window, Window):
            event_window = None
        if event_window is not None and event_window in self.gui.windows and event_window.visible:
            event_window.handle_event(event)
            return
        self.gui.screen_lifecycle.handle_event(event)

    def resolve_task_event_owner(self, event: "BaseEvent") -> Optional[Window]:
        """Run resolve task event owner and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        if getattr(event, 'type', None) != Event.Task:
            return None
        task_id = cast(Optional[Hashable], getattr(event, 'id', None))
        if task_id is None:
            return None
        try:
            hash(task_id)
        except TypeError:
            return None
        owner = self._task_owner_by_id.get(task_id)
        if owner is None:
            return None
        if owner not in self.gui.windows or not owner.visible:
            return None
        return owner

    def clear_task_owners_for_window(self, window: Window) -> None:
        """Run clear task owners for window and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        if window not in self.gui.windows:
            return
        stale_ids = [task_id for task_id, owner in self._task_owner_by_id.items() if owner is window]
        for task_id in stale_ids:
            del self._task_owner_by_id[task_id]

    def set_task_owner(self, task_id: Hashable, window: Optional[Window]) -> None:
        """Run set task owner and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        try:
            hash(task_id)
        except TypeError as exc:
            raise GuiError(f'task id must be hashable: {task_id!r}') from exc
        if window is None:
            self._task_owner_by_id.pop(task_id, None)
            return
        if window not in self.gui.windows:
            raise GuiError('task owner window must be registered')
        self._task_owner_by_id[task_id] = window

    def set_task_owners(self, window: Optional[Window], *task_ids: Hashable) -> None:
        """Run set task owners and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        for task_id in task_ids:
            self.set_task_owner(task_id, window)
