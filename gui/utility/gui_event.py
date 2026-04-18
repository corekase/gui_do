from __future__ import annotations

from typing import Optional, Tuple

from .events import BaseEvent, Event
from ..widgets.window import Window as Window


class GuiEvent(BaseEvent):
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        super().__init__(event_type)
        # Normalize optional payloads defensively so malformed external event data
        # cannot corrupt GUI event routing.
        self.key: Optional[int] = self._as_optional_int(kwargs.get('key'))
        self.pos: Optional[Tuple[int, int]] = self._as_optional_int_pair(kwargs.get('pos'))
        self.rel: Optional[Tuple[int, int]] = self._as_optional_int_pair(kwargs.get('rel'))
        self.button: Optional[int] = self._as_optional_int(kwargs.get('button'))
        self.widget_id: Optional[str] = kwargs.get('widget_id') if isinstance(kwargs.get('widget_id'), str) else None
        self.group: Optional[str] = kwargs.get('group') if isinstance(kwargs.get('group'), str) else None
        self.window: Optional[Window] = kwargs.get('window') if isinstance(kwargs.get('window'), Window) else None
        self.task_panel: bool = kwargs.get('task_panel') is True

    @staticmethod
    def _as_optional_int(value: object) -> Optional[int]:
        if type(value) is int:
            return value
        return None

    @staticmethod
    def _as_optional_int_pair(value: object) -> Optional[Tuple[int, int]]:
        if not isinstance(value, tuple) or len(value) != 2:
            return None
        if type(value[0]) is not int or type(value[1]) is not int:
            return None
        return (value[0], value[1])
