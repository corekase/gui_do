import time
import pygame
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from enum import Enum
from .constants import Event

if TYPE_CHECKING:
    from .guimanager import GuiManager

TaskKind = Enum('TaskKind', ['Finished'])

class Timers:
    def __init__(self) -> None:
        self.timers: Dict[Any, "Timers.Interval"] = {}

    class Interval:
        def __init__(self, duration: float, callback: Callable) -> None:
            self.timer: float = 0
            self.previous_time: Optional[float] = None
            self.duration: float = duration
            self.callback: Callable = callback

    def add_timer(self, id: Any, duration: float, callback: Callable) -> None:
        self.timers[id] = self.Interval(duration, callback)

    def remove_timer(self, id: Any) -> None:
        if id in self.timers.keys():
            del self.timers[id]

    def timer_updates(self, now_time: int) -> None:
        # iterate over a list copy of the keys because timers may be removed
        # during the loop
        for id in list(self.timers.keys()):
            if id not in self.timers:
                # timer was removed during the loop, so skip it
                continue
            if self.timers[id].previous_time is None:
                self.timers[id].previous_time = now_time
            else:
                elapsed_time = now_time - self.timers[id].previous_time
                self.timers[id].previous_time = now_time
                self.timers[id].timer += elapsed_time
                if self.timers[id].timer >= self.timers[id].duration:
                    self.timers[id].timer -= self.timers[id].duration
                    self.timers[id].callback()

class TaskEvent:
    # an event object to be returned which includes pygame event information and gui_do information
    def __init__(self) -> None:
        # the event is a Task type
        self.type: Any = Event.Task
        # what the event represents
        self.operation: Any = None
        # task id
        self.id: Optional[Any] = None

class Scheduler:
    def __init__(self, gui: "GuiManager") -> None:
        self.tasks: Dict[Any, "Scheduler.Task"] = {}
        self.gui: "GuiManager" = gui
        self.stop_scheduler: bool = False
        # queued and finished lists
        self._tasks_ready: List[Any] = []
        self._tasks_processed: List[Any] = []
        self._tasks_suspended: List[Any] = []
        self._tasks_finished: List[Any] = []

    class Task:
        def __init__(self, id: Any, interval: float) -> None:
            self.id: Any = id
            # times for yielding cooperative control
            self.time_start: float = 0.0
            self.time_duration: float = interval
            # pointer for a "receive information" method, takes one parameter (which can anything)
            # gives coroutine operations while only being a generator
            self.message_method: Optional[Callable] = None
            self.task_logic: Any = None

    def event(self, operation: Any, item1: Optional[Any] = None) -> "Scheduler.TaskEvent":
        task_event = TaskEvent()
        task_event.operation = operation
        if operation == TaskKind.Finished:
            task_event.id = item1
        # elif more operations
        return task_event

    def add_task(self, id: Any, logic: Callable, parameters: Optional[Any] = None, message_method: Optional[Callable] = None) -> None:
        # Replace existing task with same id to avoid duplicate queue entries.
        if id in self.tasks:
            if id in self._tasks_ready:
                self._tasks_ready = [task_id for task_id in self._tasks_ready if task_id != id]
            if id in self._tasks_processed:
                self._tasks_processed = [task_id for task_id in self._tasks_processed if task_id != id]
            if id in self._tasks_suspended:
                self._tasks_suspended = [task_id for task_id in self._tasks_suspended if task_id != id]
            self.tasks.pop(id, None)

        task = self.Task(id, 0.01)
        if parameters is None:
            task.task_logic = logic(id)
        else:
            task.task_logic = logic(id, parameters)
        task.message_method = message_method
        self.tasks[id] = task
        self._tasks_ready.append(id)

    def send_message(self, id: Any, parameters: Any) -> None:
        # send either a single value or a collection like a tuple or list to the method id
        self.tasks[id].message_method(parameters)

    def remove_all(self) -> None:
        self._tasks_ready.clear()
        self._tasks_processed.clear()
        self._tasks_suspended.clear()
        self.tasks = {}

    def remove_tasks(self, *tasks: Any) -> None:
        for id in tasks:
            if id in self._tasks_ready:
                self._tasks_ready.remove(id)
            if id in self._tasks_processed:
                self._tasks_processed.remove(id)
            if id in self._tasks_suspended:
                self._tasks_suspended.remove(id)
            self.tasks.pop(id, None)

    def suspend_all(self) -> None:
        self._tasks_suspended += self._tasks_ready[:] + self._tasks_processed[:]
        self._tasks_ready.clear()
        self._tasks_processed.clear()

    def resume_all(self) -> None:
        self._tasks_ready += self._tasks_suspended
        self._tasks_suspended.clear()

    def suspend_tasks(self, *tasks: Any) -> None:
        for id in tasks:
            # move id to suspended list from either the queued or finished lists
            if id in self._tasks_ready:
                self._tasks_ready.remove(id)
                self._tasks_suspended.append(id)
            elif id in self._tasks_processed:
                self._tasks_processed.remove(id)
                self._tasks_suspended.append(id)

    def resume_tasks(self, *tasks: Any) -> None:
        for id in tasks:
            # move id from suspended list to end of queued list
            if id in self._tasks_suspended:
                self._tasks_suspended.remove(id)
                self._tasks_ready.append(id)

    def read_suspended(self) -> List[Any]:
        # return a list of suspended task id's
        return self._tasks_suspended

    def read_suspended_len(self) -> int:
        # return the number of suspended tasks
        return len(self._tasks_suspended)

    def task_time(self, id: Any) -> bool:
        if (time.time() - self.tasks[id].time_start) >= self.tasks[id].time_duration:
            return True
        return False

    def tasks_active(self) -> bool:
        if (len(self._tasks_ready) > 0) or (len(self._tasks_processed) > 0):
            return True
        return False

    def tasks_active_match_any(self, *tasks: Any) -> bool:
        # if a task is in either tasks_ready or tasks_processed then return True
        for task in tasks:
            if task in self._tasks_ready:
                return True
            elif task in self._tasks_processed:
                return True
        return False

    def tasks_active_match_all(self, *tasks: Any) -> bool:
        # return True only if all specified tasks are active
        for task in tasks:
            if task not in self._tasks_ready and task not in self._tasks_processed:
                return False
        return True

    def update(self) -> List[Any]:
        """
        Update scheduler state for one frame of execution.

        Processes a single task cycle and returns a list of task IDs that finished.

        Returns:
            List of task IDs that finished during this update
        """
        self._tasks_finished.clear()

        if len(self._tasks_ready) > 0:
            self._process_next_task()
        elif len(self._tasks_ready) == 0:
            self._tasks_ready = self._tasks_processed
            if len(self._tasks_processed) > 0:
                self._tasks_processed.clear()
            if len(self._tasks_ready) > 0:
                # do process here again because ready list was empty
                self._process_next_task()

        # Return finished tasks so caller can dispatch events
        return self._tasks_finished.copy()

    def _process_next_task(self) -> None:
        # separate out duplicate code so that waiting processed list id's don't miss a cycle when the ready list is empty
        try:
            task_id = self._tasks_ready.pop(0)
            self.tasks[task_id].time_start = time.time()
            next(self.tasks[task_id].task_logic)
            self._tasks_processed.append(task_id)
        except StopIteration:
            # task exited, and exception from next() happened before appending the id to the processed list
            self._tasks_finished.append(task_id)
            del self.tasks[task_id]

    def get_finished_tasks(self) -> List[Any]:
        """
        Get list of tasks that finished in the most recent update.

        Returns:
            List of task IDs that finished
        """
        return self._tasks_finished.copy()

    def clear_finished_tasks(self) -> None:
        """Clear the finished tasks list."""
        self._tasks_finished.clear()
