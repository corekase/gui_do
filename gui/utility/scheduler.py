import time
from collections import deque
from typing import Callable, Deque, Dict, Generator, Hashable, List, Optional, Set, Tuple, TYPE_CHECKING, cast
from enum import Enum
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
        if duration <= 0:
            from .guimanager import GuiError
            raise GuiError(f'timer duration must be > 0, got: {duration}')
        self.timers[id] = Interval(duration, callback)

    def remove_timer(self, id: Hashable) -> None:
        if id in self.timers:
            del self.timers[id]

    def timer_updates(self, now_time: int) -> None:
        # iterate over a list copy of the keys because timers may be removed
        # during the loop
        for id in list(self.timers.keys()):
            interval = self.timers.get(id)
            if interval is None:
                # timer was removed during the loop, so skip it
                continue
            if interval.previous_time is None:
                interval.previous_time = now_time
            else:
                elapsed_time = now_time - interval.previous_time
                interval.previous_time = now_time
                interval.timer += elapsed_time
                if interval.timer >= interval.duration:
                    interval.timer -= interval.duration
                    interval.callback()

class Task:
    def __init__(self, id: Hashable, interval: float) -> None:
        self.id: Hashable = id
        # times for yielding cooperative control
        self.time_start: float = 0.0
        self.time_duration: float = interval
        # pointer for a "receive information" method, takes one parameter (which can anything)
        # gives coroutine operations while only being a generator
        self.message_method: Optional[Callable[[object], None]] = None
        self.task_logic: Optional[Generator[object, None, None]] = None

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
    def __init__(self, gui: "GuiManager") -> None:
        self.tasks: Dict[Hashable, Task] = {}
        self.gui: "GuiManager" = gui
        self.stop_scheduler: bool = False
        # queued and finished lists
        self._tasks_ready: Deque[Hashable] = deque()
        self._tasks_processed: Deque[Hashable] = deque()
        self._tasks_suspended: List[Hashable] = []
        self._tasks_finished: List[Hashable] = []
        self._tasks_failed: List[Tuple[Hashable, str]] = []
        self._tasks_ready_set: Set[Hashable] = set()
        self._tasks_processed_set: Set[Hashable] = set()
        self._tasks_suspended_set: Set[Hashable] = set()

    def _validate_task_id(self, id: Hashable) -> None:
        try:
            hash(id)
        except TypeError as exc:
            from .guimanager import GuiError
            raise GuiError(f'task id must be hashable: {id!r}') from exc

    def _remove_from_ready(self, id: Hashable) -> None:
        if id in self._tasks_ready_set:
            if id in self._tasks_ready:
                self._tasks_ready.remove(id)
            self._tasks_ready_set.discard(id)

    def _remove_from_processed(self, id: Hashable) -> None:
        if id in self._tasks_processed_set:
            if id in self._tasks_processed:
                self._tasks_processed.remove(id)
            self._tasks_processed_set.discard(id)

    def event(self, operation: TaskKind, item1: Optional[Hashable] = None, item2: Optional[str] = None) -> TaskEvent:
        task_event = TaskEvent()
        task_event.operation = operation
        if operation == TaskKind.Finished:
            task_event.id = item1
        elif operation == TaskKind.Failed:
            task_event.id = item1
            task_event.error = item2
        # elif more operations
        return task_event

    def add_task(self, id: Hashable, logic: Callable[..., Generator[object, None, None]], parameters: Optional[object] = None, message_method: Optional[Callable[[object], None]] = None) -> None:
        self._validate_task_id(id)
        # Replace existing task with same id to avoid duplicate queue entries.
        self._tasks_failed = [item for item in self._tasks_failed if item[0] != id]
        self._tasks_finished = [task_id for task_id in self._tasks_finished if task_id != id]
        self._remove_from_ready(id)
        self._remove_from_processed(id)
        if id in self._tasks_suspended_set:
            self._tasks_suspended = [task_id for task_id in self._tasks_suspended if task_id != id]
            self._tasks_suspended_set.discard(id)
        if id in self.tasks:
            self.tasks.pop(id, None)
        task = Task(id, 0.01)
        try:
            if parameters is None:
                task.task_logic = logic(id)
            else:
                task.task_logic = logic(id, parameters)
        except Exception as exc:
            from .guimanager import GuiError
            raise GuiError(f'failed to create task logic for "{id}": {type(exc).__name__}: {exc}') from exc
        if task.task_logic is None or not hasattr(task.task_logic, '__next__'):
            from .guimanager import GuiError
            raise GuiError(f'task logic for "{id}" must be a generator')
        task.message_method = message_method
        self.tasks[id] = task
        self._tasks_ready.append(id)
        self._tasks_ready_set.add(id)

    def send_message(self, id: Hashable, parameters: object) -> None:
        self._validate_task_id(id)
        # send either a single value or a collection like a tuple or list to the method id
        task = self.tasks.get(id)
        if task is None:
            from .guimanager import GuiError
            raise GuiError(f'unknown task id: {id}')
        if task.message_method is None:
            from .guimanager import GuiError
            raise GuiError(f'task "{id}" has no message handler')
        task.message_method(parameters)

    def remove_all(self) -> None:
        self._tasks_ready.clear()
        self._tasks_processed.clear()
        self._tasks_suspended.clear()
        self._tasks_finished.clear()
        self._tasks_failed.clear()
        self._tasks_ready_set.clear()
        self._tasks_processed_set.clear()
        self._tasks_suspended_set.clear()
        self.tasks = {}

    def remove_tasks(self, *tasks: Hashable) -> None:
        for id in tasks:
            self._validate_task_id(id)
        remove_set = set(tasks)
        self._tasks_ready = deque(id for id in self._tasks_ready if id not in remove_set)
        self._tasks_processed = deque(id for id in self._tasks_processed if id not in remove_set)
        self._tasks_ready_set = set(self._tasks_ready)
        self._tasks_processed_set = set(self._tasks_processed)
        self._tasks_suspended = [id for id in self._tasks_suspended if id not in remove_set]
        self._tasks_suspended_set = set(self._tasks_suspended)
        self._tasks_finished = [id for id in self._tasks_finished if id not in remove_set]
        self._tasks_failed = [item for item in self._tasks_failed if item[0] not in remove_set]
        for id in tasks:
            self.tasks.pop(id, None)

    def suspend_all(self) -> None:
        ready = list(self._tasks_ready)
        processed = list(self._tasks_processed)
        for id in ready + processed:
            if id not in self._tasks_suspended_set:
                self._tasks_suspended.append(id)
                self._tasks_suspended_set.add(id)
        self._tasks_ready.clear()
        self._tasks_processed.clear()
        self._tasks_ready_set.clear()
        self._tasks_processed_set.clear()

    def resume_all(self) -> None:
        for id in self._tasks_suspended:
            if id not in self.tasks:
                continue
            if id not in self._tasks_ready_set:
                self._tasks_ready.append(id)
                self._tasks_ready_set.add(id)
        self._tasks_suspended.clear()
        self._tasks_suspended_set.clear()

    def suspend_tasks(self, *tasks: Hashable) -> None:
        for id in tasks:
            self._validate_task_id(id)
            # move id to suspended list from either the ready or processed lists
            if id in self._tasks_ready_set:
                self._remove_from_ready(id)
                if id not in self._tasks_suspended_set:
                    self._tasks_suspended.append(id)
                    self._tasks_suspended_set.add(id)
            elif id in self._tasks_processed_set:
                self._remove_from_processed(id)
                if id not in self._tasks_suspended_set:
                    self._tasks_suspended.append(id)
                    self._tasks_suspended_set.add(id)

    def resume_tasks(self, *tasks: Hashable) -> None:
        for id in tasks:
            self._validate_task_id(id)
            # move id from suspended list to end of queued list
            if id in self._tasks_suspended_set:
                if id in self._tasks_suspended:
                    self._tasks_suspended.remove(id)
                self._tasks_suspended_set.discard(id)
                if id in self.tasks:
                    if id not in self._tasks_ready_set:
                        self._tasks_ready.append(id)
                        self._tasks_ready_set.add(id)

    def read_suspended(self) -> List[Hashable]:
        # return a list of suspended task id's
        return self._tasks_suspended.copy()

    def read_suspended_len(self) -> int:
        # return the number of suspended tasks
        return len(self._tasks_suspended)

    def task_time(self, id: Hashable) -> bool:
        self._validate_task_id(id)
        task = self.tasks.get(id)
        if task is None:
            from .guimanager import GuiError
            raise GuiError(f'unknown task id: {id}')
        if (time.time() - task.time_start) >= task.time_duration:
            return True
        return False

    def tasks_active(self) -> bool:
        if self._tasks_ready_set or self._tasks_processed_set:
            return True
        return False

    def tasks_active_match_any(self, *tasks: Hashable) -> bool:
        # if a task is in either tasks_ready or tasks_processed then return True
        for task in tasks:
            if task in self._tasks_ready_set:
                return True
            elif task in self._tasks_processed_set:
                return True
        return False

    def tasks_active_match_all(self, *tasks: Hashable) -> bool:
        # return True only if all specified tasks are active
        for task in tasks:
            if task not in self._tasks_ready_set and task not in self._tasks_processed_set:
                return False
        return True

    def update(self) -> List[Hashable]:
        """
        Update scheduler state for one frame of execution.

        Processes a single task cycle and returns a list of task IDs that finished.

        Returns:
            List of task IDs that finished during this update
        """
        self._tasks_finished.clear()
        self._tasks_failed.clear()
        if len(self._tasks_ready) > 0:
            self._process_next_task()
        elif len(self._tasks_ready) == 0:
            self._tasks_ready = deque(self._tasks_processed)
            self._tasks_ready_set = set(self._tasks_processed_set)
            if len(self._tasks_processed) > 0:
                self._tasks_processed = deque()
                self._tasks_processed_set = set()
            if len(self._tasks_ready) > 0:
                # do process here again because ready list was empty
                self._process_next_task()
        # Return finished tasks so caller can dispatch events
        return self._tasks_finished.copy()

    def _process_next_task(self) -> None:
        # separate out duplicate code so that waiting processed list id's don't miss a cycle when the ready list is empty
        while self._tasks_ready:
            task_id = self._tasks_ready.popleft()
            self._tasks_ready_set.discard(task_id)
            # Task may have been removed after it was queued.
            task = self.tasks.get(task_id)
            if task is None:
                continue
            # Ignore and remove malformed tasks with no generator logic.
            if task.task_logic is None:
                self.tasks.pop(task_id, None)
                continue
            task.time_start = time.time()
            try:
                next(cast(Generator[object, None, None], task.task_logic))
            except StopIteration:
                # task exited, and exception from next() happened before appending the id to the processed list
                self._tasks_finished.append(task_id)
                self.tasks.pop(task_id, None)
                return
            except Exception as exc:
                self._tasks_failed.append((task_id, f'{type(exc).__name__}: {exc}'))
                self.tasks.pop(task_id, None)
                return
            self._tasks_processed.append(task_id)
            self._tasks_processed_set.add(task_id)
            return

    def get_finished_tasks(self) -> List[Hashable]:
        """
        Get list of tasks that finished in the most recent update.

        Returns:
            List of task IDs that finished
        """
        return self._tasks_finished.copy()

    def clear_finished_tasks(self) -> None:
        """Clear the finished tasks list."""
        self._tasks_finished.clear()

    def get_failed_tasks(self) -> List[Tuple[Hashable, str]]:
        """Get list of failed tasks in the most recent update.

        Returns:
            List of tuples: (task_id, error_message)
        """
        return self._tasks_failed.copy()

    def clear_failed_tasks(self) -> None:
        """Clear the failed tasks list."""
        self._tasks_failed.clear()
