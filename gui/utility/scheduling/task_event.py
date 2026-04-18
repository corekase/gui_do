from __future__ import annotations

from typing import Hashable, Optional

from ..events import BaseEvent, Event
from .task_kind import TaskKind


class TaskEvent(BaseEvent):
    """Event emitted for task completion or failure."""

    def __init__(self, operation: TaskKind, task_id: Optional[Hashable] = None, error: Optional[str] = None) -> None:
        """Initialize the TaskEvent instance."""
        super().__init__(Event.Task)
        self.operation: TaskKind = operation
        self.id: Optional[Hashable] = task_id
        self.error: Optional[str] = error
