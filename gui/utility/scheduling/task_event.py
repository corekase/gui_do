from __future__ import annotations

from typing import Hashable, Optional

from ..events import BaseEvent, Event, GuiError
from .task_kind import TaskKind


class TaskEvent(BaseEvent):
    """Event emitted for task completion or failure."""

    def __init__(self, operation: TaskKind, task_id: Optional[Hashable] = None, error: Optional[str] = None) -> None:
        """Create TaskEvent."""
        if not isinstance(operation, TaskKind):
            raise GuiError(f'operation must be a TaskKind, got: {operation!r}')
        if task_id is not None:
            try:
                hash(task_id)
            except TypeError as exc:
                raise GuiError(f'task_id must be hashable when provided, got: {task_id!r}') from exc
        if error is not None and not isinstance(error, str):
            raise GuiError(f'error must be a string when provided, got: {error!r}')
        super().__init__(Event.Task)
        self.operation: TaskKind = operation
        self.id: Optional[Hashable] = task_id
        self.error: Optional[str] = error
