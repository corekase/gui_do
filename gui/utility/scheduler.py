import asyncio
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
import inspect
import os
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Deque, Dict, Hashable, List, Optional, Set, Tuple, TYPE_CHECKING, Any

from .constants import Event

if TYPE_CHECKING:
    from .guimanager import GuiManager

TaskKind = Enum('TaskKind', ['Finished', 'Failed'])


class Interval:
    def __init__(self, duration: float, callback: Callable[[], None]) -> None:
        self.timer: float = 0
        self.previous_time: Optional[float] = None
        self.duration: float = duration
        self.callback: Callable[[], None] = callback


class Timers:
    def __init__(self) -> None:
        self.timers: Dict[Hashable, "Interval"] = {}

    def add_timer(self, id: Hashable, duration: float, callback: Callable[[], None]) -> None:
        try:
            hash(id)
        except TypeError as exc:
            from .guimanager import GuiError
            raise GuiError(f'timer id must be hashable: {id!r}') from exc
        if duration <= 0:
            from .guimanager import GuiError
            raise GuiError(f'timer duration must be > 0, got: {duration}')
        if not callable(callback):
            from .guimanager import GuiError
            raise GuiError('timer callback must be callable')
        self.timers[id] = Interval(duration, callback)

    def remove_timer(self, id: Hashable) -> None:
        try:
            hash(id)
        except TypeError as exc:
            from .guimanager import GuiError
            raise GuiError(f'timer id must be hashable: {id!r}') from exc
        if id in self.timers:
            del self.timers[id]

    def timer_updates(self, now_time: int) -> None:
        # Iterate over a key copy because callbacks may remove timers.
        for id in list(self.timers.keys()):
            interval = self.timers.get(id)
            if interval is None:
                continue
            if interval.previous_time is None:
                interval.previous_time = now_time
            else:
                elapsed_time = now_time - interval.previous_time
                interval.previous_time = now_time
                interval.timer += elapsed_time
                while interval.timer >= interval.duration:
                    interval.timer -= interval.duration
                    interval.callback()
                    interval = self.timers.get(id)
                    if interval is None:
                        break


@dataclass
class Task:
    id: Hashable
    run_callable: Callable[[], object]
    message_method: Optional[Callable[[object], None]] = None
    future: Optional[Future[object]] = None


class TaskEvent:
    # an event object to be returned which includes pygame event information and gui_do information
    def __init__(self) -> None:
        # the event is a Task type
        self.type: Event = Event.Task
        # what the event represents
        self.operation: Optional[TaskKind] = None
        # task id
        self.id: Optional[Hashable] = None
        # optional error details for failed tasks
        self.error: Optional[str] = None


class Scheduler:
    """Concurrent task scheduler.

    This scheduler runs tasks using worker threads and supports callables,
    coroutine functions, and callables that return coroutine objects.

    Cooperative generator scheduling has been removed.
    """

    def __init__(self, gui: "GuiManager") -> None:
        self.gui: "GuiManager" = gui
        self.stop_scheduler: bool = False

        self.tasks: Dict[Hashable, Task] = {}

        self._pending: Deque[Hashable] = deque()
        self._pending_set: Set[Hashable] = set()
        self._suspended: List[Hashable] = []
        self._suspended_set: Set[Hashable] = set()
        self._running: Set[Hashable] = set()

        self._tasks_finished: List[Hashable] = []
        self._tasks_failed: List[Tuple[Hashable, str]] = []
        self._task_results: Dict[Hashable, object] = {}

        self._lock = threading.RLock()
        self._max_workers: int = max(1, os.cpu_count() or 4)
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=self._max_workers)

    def _validate_task_id(self, id: Hashable) -> None:
        try:
            hash(id)
        except TypeError as exc:
            from .guimanager import GuiError
            raise GuiError(f'task id must be hashable: {id!r}') from exc

    def _build_task_callable(self, id: Hashable, logic: Callable[..., object], parameters: Optional[object]) -> Callable[[], object]:
        def run() -> object:
            if parameters is None:
                outcome = logic(id)
            else:
                outcome = logic(id, parameters)

            if inspect.isawaitable(outcome):
                return asyncio.run(outcome)
            return outcome

        return run

    def _remove_from_pending(self, id: Hashable) -> None:
        if id in self._pending_set:
            if id in self._pending:
                self._pending.remove(id)
            self._pending_set.discard(id)

    def _remove_from_suspended(self, id: Hashable) -> None:
        if id in self._suspended_set:
            if id in self._suspended:
                self._suspended.remove(id)
            self._suspended_set.discard(id)

    def _remove_task_internal(self, id: Hashable) -> None:
        self._remove_from_pending(id)
        self._remove_from_suspended(id)
        task = self.tasks.pop(id, None)
        self._task_results.pop(id, None)
        if id in self._running:
            self._running.discard(id)
            if task is not None and task.future is not None:
                task.future.cancel()

    def event(self, operation: TaskKind, item1: Optional[Hashable] = None, item2: Optional[str] = None) -> TaskEvent:
        if operation not in (TaskKind.Finished, TaskKind.Failed):
            from .guimanager import GuiError
            raise GuiError(f'unknown task event operation: {operation}')
        if item1 is not None:
            self._validate_task_id(item1)
        task_event = TaskEvent()
        task_event.operation = operation
        if operation == TaskKind.Finished:
            task_event.id = item1
        elif operation == TaskKind.Failed:
            task_event.id = item1
            task_event.error = '' if item2 is None else str(item2)
        return task_event

    def add_task(
        self,
        id: Hashable,
        logic: Callable[..., object],
        parameters: Optional[object] = None,
        message_method: Optional[Callable[[object], None]] = None,
    ) -> None:
        self._validate_task_id(id)
        if not callable(logic):
            from .guimanager import GuiError
            raise GuiError('task logic must be callable')
        if message_method is not None and not callable(message_method):
            from .guimanager import GuiError
            raise GuiError('task message_method must be callable when provided')

        with self._lock:
            self._tasks_failed = [item for item in self._tasks_failed if item[0] != id]
            self._tasks_finished = [task_id for task_id in self._tasks_finished if task_id != id]
            if id in self.tasks or id in self._running or id in self._pending_set or id in self._suspended_set:
                self._remove_task_internal(id)

            task_callable = self._build_task_callable(id, logic, parameters)
            self.tasks[id] = Task(id=id, run_callable=task_callable, message_method=message_method)
            self._pending.append(id)
            self._pending_set.add(id)

    def send_message(self, id: Hashable, parameters: object) -> None:
        self._validate_task_id(id)
        task = self.tasks.get(id)
        if task is None:
            from .guimanager import GuiError
            raise GuiError(f'unknown task id: {id}')
        if task.message_method is None:
            from .guimanager import GuiError
            raise GuiError(f'task "{id}" has no message handler')
        if not callable(task.message_method):
            from .guimanager import GuiError
            raise GuiError(f'task "{id}" message handler is not callable')
        task.message_method(parameters)

    def remove_all(self) -> None:
        with self._lock:
            ids = list(self.tasks.keys())
            for id in ids:
                self._remove_task_internal(id)
            self._pending.clear()
            self._pending_set.clear()
            self._suspended.clear()
            self._suspended_set.clear()
            self._running.clear()
            self._tasks_finished.clear()
            self._tasks_failed.clear()
            self._task_results.clear()

    def remove_tasks(self, *tasks: Hashable) -> None:
        with self._lock:
            for id in tasks:
                self._validate_task_id(id)
                self._remove_task_internal(id)
            removed = set(tasks)
            self._tasks_finished = [id for id in self._tasks_finished if id not in removed]
            self._tasks_failed = [item for item in self._tasks_failed if item[0] not in removed]

    def suspend_all(self) -> None:
        with self._lock:
            for id in list(self._pending):
                if id not in self._suspended_set:
                    self._suspended.append(id)
                    self._suspended_set.add(id)
            self._pending.clear()
            self._pending_set.clear()

    def resume_all(self) -> None:
        with self._lock:
            for id in list(self._suspended):
                if id in self.tasks and id not in self._pending_set:
                    self._pending.append(id)
                    self._pending_set.add(id)
            self._suspended.clear()
            self._suspended_set.clear()

    def suspend_tasks(self, *tasks: Hashable) -> None:
        with self._lock:
            for id in tasks:
                self._validate_task_id(id)
                if id in self._pending_set:
                    self._remove_from_pending(id)
                    if id not in self._suspended_set:
                        self._suspended.append(id)
                        self._suspended_set.add(id)

    def resume_tasks(self, *tasks: Hashable) -> None:
        with self._lock:
            for id in tasks:
                self._validate_task_id(id)
                if id in self._suspended_set:
                    self._remove_from_suspended(id)
                    if id in self.tasks and id not in self._pending_set:
                        self._pending.append(id)
                        self._pending_set.add(id)

    def read_suspended(self) -> List[Hashable]:
        with self._lock:
            return self._suspended.copy()

    def read_suspended_len(self) -> int:
        with self._lock:
            return len(self._suspended)

    def task_time(self, id: Hashable) -> bool:
        self._validate_task_id(id)
        from .guimanager import GuiError
        raise GuiError('task_time is no longer supported because cooperative scheduling was removed')

    def tasks_active(self) -> bool:
        with self._lock:
            return bool(self._pending_set or self._running)

    def tasks_active_match_any(self, *tasks: Hashable) -> bool:
        with self._lock:
            for task in tasks:
                self._validate_task_id(task)
                if task in self._pending_set or task in self._running:
                    return True
            return False

    def tasks_active_match_all(self, *tasks: Hashable) -> bool:
        with self._lock:
            for task in tasks:
                self._validate_task_id(task)
                if task not in self._pending_set and task not in self._running:
                    return False
            return True

    def _submit_ready_tasks(self) -> None:
        while self._pending and len(self._running) < self._max_workers:
            task_id = self._pending.popleft()
            self._pending_set.discard(task_id)
            task = self.tasks.get(task_id)
            if task is None:
                continue
            task.future = self._executor.submit(task.run_callable)
            self._running.add(task_id)

    def _collect_finished_tasks(self) -> None:
        for task_id in list(self._running):
            task = self.tasks.get(task_id)
            if task is None or task.future is None:
                self._running.discard(task_id)
                continue
            if not task.future.done():
                continue

            self._running.discard(task_id)
            try:
                result = task.future.result()
                self._task_results[task_id] = result
                self._tasks_finished.append(task_id)
            except Exception as exc:
                self._tasks_failed.append((task_id, f'{type(exc).__name__}: {exc}'))
            finally:
                self.tasks.pop(task_id, None)

    def update(self) -> List[Hashable]:
        """Update scheduler state for one frame.

        Returns:
            List of task IDs that finished during this update.
        """
        with self._lock:
            self._tasks_finished.clear()
            self._tasks_failed.clear()
            self._submit_ready_tasks()
            self._collect_finished_tasks()
            return self._tasks_finished.copy()

    def get_finished_tasks(self) -> List[Hashable]:
        """Get list of tasks that finished in the most recent update."""
        with self._lock:
            return self._tasks_finished.copy()

    def clear_finished_tasks(self) -> None:
        """Clear the finished tasks list."""
        with self._lock:
            self._tasks_finished.clear()

    def get_failed_tasks(self) -> List[Tuple[Hashable, str]]:
        """Get list of failed tasks in the most recent update."""
        with self._lock:
            return self._tasks_failed.copy()

    def clear_failed_tasks(self) -> None:
        """Clear the failed tasks list."""
        with self._lock:
            self._tasks_failed.clear()

    def pop_result(self, id: Hashable, default: Optional[object] = None) -> Optional[object]:
        """Get and remove a completed task's result."""
        self._validate_task_id(id)
        with self._lock:
            return self._task_results.pop(id, default)

    def shutdown(self) -> None:
        """Release thread resources used by this scheduler."""
        with self._lock:
            self.remove_all()
            self._executor.shutdown(wait=False, cancel_futures=True)

    def __del__(self) -> None:
        try:
            self.shutdown()
        except Exception:
            pass
