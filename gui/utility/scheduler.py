from __future__ import annotations

import asyncio
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
import inspect
import logging
import os
from queue import Empty, SimpleQueue
import threading
from typing import Callable, Deque, Dict, Hashable, List, Optional, Set, Tuple, TYPE_CHECKING
from .events import GuiError
from .scheduling import TaskKind, Timers, Task, TaskMessage, TaskCompletion, TaskFailure, TaskEvent

if TYPE_CHECKING:
    from .gui_manager import GuiManager

_logger = logging.getLogger(__name__)

class Scheduler:
    """Threaded task runner with per-frame completion and message dispatch."""

    def __init__(self, gui: "GuiManager") -> None:
        """Create Scheduler."""
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
        self._task_generation: Dict[Hashable, int] = {}
        self._task_message_counts: Dict[Hashable, int] = {}
        self._incoming_task_messages: SimpleQueue[TaskMessage] = SimpleQueue()
        self._incoming_task_completions: SimpleQueue[TaskCompletion] = SimpleQueue()
        self._incoming_task_failures: SimpleQueue[TaskFailure] = SimpleQueue()
        self._task_messages: Deque[TaskMessage] = deque()
        self._message_dispatch_limit: Optional[int] = None
        self._message_ingest_limit: Optional[int] = 256
        self._max_queued_messages_per_task: Optional[int] = 512
        self._lock = threading.RLock()
        self._message_slots_changed = threading.Condition(self._lock)
        self._max_workers: int = max(1, os.cpu_count() or 4)
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=self._max_workers)

    def shutdown(self) -> None:
        """Cancel pending work and stop worker threads."""
        with self._lock:
            self.remove_all()
            self._executor.shutdown(wait=False, cancel_futures=True)

    def update(self) -> List[Hashable]:
        """Advance one frame and return task ids that finished this update."""
        with self._lock:
            self._tasks_finished.clear()
            self._tasks_failed.clear()
            self._submit_ready_tasks()
            self._collect_finished_tasks()
            finished_tasks = self._tasks_finished.copy()
        self._drain_incoming_task_failures()
        self._drain_incoming_task_messages()
        self._dispatch_task_messages()
        self._drain_incoming_task_failures()
        return finished_tasks

    def get_failed_tasks(self) -> List[Tuple[Hashable, str]]:
        """Return failed tasks from the latest update as (id, error)."""
        with self._lock:
            return self._tasks_failed.copy()

    def get_finished_tasks(self) -> List[Hashable]:
        """Return finished task ids from the latest update."""
        with self._lock:
            return self._tasks_finished.copy()

    def get_max_queued_messages_per_task(self) -> Optional[int]:
        """Return per-task queue cap, or None when unlimited."""
        with self._lock:
            return self._max_queued_messages_per_task

    def get_message_dispatch_limit(self) -> Optional[int]:
        """Return dispatch limit per update, or None when unlimited."""
        with self._lock:
            return self._message_dispatch_limit

    def get_message_ingest_limit(self) -> Optional[int]:
        """Return ingest limit per update, or None when unlimited."""
        with self._lock:
            return self._message_ingest_limit

    def read_suspended(self) -> List[Hashable]:
        """Read suspended."""
        with self._lock:
            return self._suspended.copy()

    def read_suspended_len(self) -> int:
        """Read suspended len."""
        with self._lock:
            return len(self._suspended)

    def add_task(
        self,
        id: Hashable,
        logic: Callable[..., object],
        parameters: Optional[object] = None,
        message_method: Optional[Callable[[object], None]] = None,
    ) -> None:
        """Add task."""
        self._validate_task_id(id)
        if not callable(logic):
            raise GuiError('task logic must be callable')
        if message_method is not None and not callable(message_method):
            raise GuiError('task message_method must be callable when provided')
        with self._lock:
            self._tasks_failed = [item for item in self._tasks_failed if item[0] != id]
            self._tasks_finished = [task_id for task_id in self._tasks_finished if task_id != id]
            if id in self.tasks or id in self._running or id in self._pending_set or id in self._suspended_set:
                self._remove_task_internal(id)
            generation = self._task_generation.get(id, 0) + 1
            self._task_generation[id] = generation
            task_callable = self._build_task_callable(id, logic, parameters)
            self.tasks[id] = Task(id=id, run_callable=task_callable, message_method=message_method, generation=generation)
            self._pending.append(id)
            self._pending_set.add(id)

    def clear_failed_tasks(self) -> None:
        """Clear stored failed-task entries."""
        with self._lock:
            self._tasks_failed.clear()

    def clear_finished_tasks(self) -> None:
        """Clear stored finished-task ids."""
        with self._lock:
            self._tasks_finished.clear()

    def pop_result(self, id: Hashable, default: Optional[object] = None) -> Optional[object]:
        """Return and remove a completed task result."""
        self._validate_task_id(id)
        with self._lock:
            return self._task_results.pop(id, default)

    def remove_all(self) -> None:
        """Remove all."""
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
            self._task_messages.clear()
            self._task_message_counts.clear()

    def remove_tasks(self, *tasks: Hashable) -> None:
        """Remove tasks."""
        with self._lock:
            for id in tasks:
                self._validate_task_id(id)
                self._remove_task_internal(id)
            removed = set(tasks)
            self._tasks_finished = [id for id in self._tasks_finished if id not in removed]
            self._tasks_failed = [item for item in self._tasks_failed if item[0] not in removed]
            self._task_messages = deque(message for message in self._task_messages if message.id not in removed)

    def set_max_queued_messages_per_task(self, max_queued_messages: Optional[int]) -> None:
        """Set per-task queue cap before send_message blocks for backpressure."""
        if max_queued_messages is not None:
            if not isinstance(max_queued_messages, int):
                raise GuiError(f'max_queued_messages must be int or None, got: {type(max_queued_messages).__name__}')
            if max_queued_messages <= 0:
                raise GuiError(f'max_queued_messages must be > 0, got: {max_queued_messages}')
        with self._lock:
            self._max_queued_messages_per_task = max_queued_messages
            self._message_slots_changed.notify_all()

    def set_message_dispatch_limit(self, max_messages_per_update: Optional[int]) -> None:
        """Set max callback messages dispatched in each update call."""
        if max_messages_per_update is not None:
            if not isinstance(max_messages_per_update, int):
                raise GuiError(f'max_messages_per_update must be int or None, got: {type(max_messages_per_update).__name__}')
            if max_messages_per_update <= 0:
                raise GuiError(f'max_messages_per_update must be > 0, got: {max_messages_per_update}')
        with self._lock:
            self._message_dispatch_limit = max_messages_per_update

    def set_message_ingest_limit(self, max_messages_per_update: Optional[int]) -> None:
        """Set max incoming messages moved into dispatch buffer per update."""
        if max_messages_per_update is not None:
            if not isinstance(max_messages_per_update, int):
                raise GuiError(f'max_messages_per_update must be int or None, got: {type(max_messages_per_update).__name__}')
            if max_messages_per_update <= 0:
                raise GuiError(f'max_messages_per_update must be > 0, got: {max_messages_per_update}')
        with self._lock:
            self._message_ingest_limit = max_messages_per_update

    def event(self, operation: TaskKind, item1: Optional[Hashable] = None, item2: Optional[str] = None) -> TaskEvent:
        """Event."""
        if operation not in (TaskKind.Finished, TaskKind.Failed):
            raise GuiError(f'unknown task event operation: {operation}')
        if item1 is not None:
            self._validate_task_id(item1)
        if operation == TaskKind.Finished:
            return TaskEvent(TaskKind.Finished, item1)
        return TaskEvent(TaskKind.Failed, item1, '' if item2 is None else str(item2))

    def resume_all(self) -> None:
        """Resume all."""
        with self._lock:
            for id in list(self._suspended):
                if id in self.tasks and id not in self._pending_set:
                    self._pending.append(id)
                    self._pending_set.add(id)
            self._suspended.clear()
            self._suspended_set.clear()

    def resume_tasks(self, *tasks: Hashable) -> None:
        """Resume tasks."""
        with self._lock:
            for id in tasks:
                self._validate_task_id(id)
                if id in self._suspended_set:
                    self._remove_from_suspended(id)
                    if id in self.tasks and id not in self._pending_set:
                        self._pending.append(id)
                        self._pending_set.add(id)

    def send_message(self, id: Hashable, parameters: object) -> None:
        """Send message."""
        self._validate_task_id(id)
        with self._lock:
            while True:
                task = self.tasks.get(id)
                if task is None:
                    raise GuiError(f'unknown task id: {id}')
                if task.message_method is None:
                    raise GuiError(f'task "{id}" has no message handler')
                if not callable(task.message_method):
                    raise GuiError(f'task "{id}" message handler is not callable')
                queued_count = self._task_message_counts.get(id, 0)
                if self._max_queued_messages_per_task is None or queued_count < self._max_queued_messages_per_task:
                    break
                self._message_slots_changed.wait()
            self._task_message_counts[id] = self._task_message_counts.get(id, 0) + 1
            message = TaskMessage(id=id, callback=task.message_method, payload=parameters, generation=task.generation)
        self._incoming_task_messages.put(message)

    def suspend_all(self) -> None:
        """Suspend all."""
        with self._lock:
            for id in list(self._pending):
                if id not in self._suspended_set:
                    self._suspended.append(id)
                    self._suspended_set.add(id)
            self._pending.clear()
            self._pending_set.clear()

    def suspend_tasks(self, *tasks: Hashable) -> None:
        """Suspend tasks."""
        with self._lock:
            for id in tasks:
                self._validate_task_id(id)
                if id in self._pending_set:
                    self._remove_from_pending(id)
                    if id not in self._suspended_set:
                        self._suspended.append(id)
                        self._suspended_set.add(id)

    def tasks_active(self) -> bool:
        """Tasks active."""
        with self._lock:
            return bool(self._pending_set or self._running)

    def tasks_active_match_all(self, *tasks: Hashable) -> bool:
        """Tasks active match all."""
        with self._lock:
            for task in tasks:
                self._validate_task_id(task)
                if task not in self._pending_set and task not in self._running:
                    return False
            return True

    def tasks_active_match_any(self, *tasks: Hashable) -> bool:
        """Tasks active match any."""
        with self._lock:
            for task in tasks:
                self._validate_task_id(task)
                if task in self._pending_set or task in self._running:
                    return True
            return False

    def tasks_busy(self) -> bool:
        """Return True when tasks are running/pending or still have queued messages."""
        with self._lock:
            return bool(self._pending_set or self._running or self._task_message_counts)

    def tasks_busy_match_any(self, *tasks: Hashable) -> bool:
        """Return True when any listed id is active or has queued messages."""
        with self._lock:
            for task in tasks:
                self._validate_task_id(task)
                if task in self._pending_set or task in self._running:
                    return True
                if self._task_message_counts.get(task, 0) > 0:
                    return True
            return False

    def _dispatch_task_messages(self) -> None:
        """Dispatch task messages."""
        pending_messages: List[TaskMessage] = []
        with self._lock:
            if not self._task_messages:
                return
            if self._message_dispatch_limit is None:
                pending_messages = list(self._task_messages)
                self._task_messages.clear()
            else:
                for _ in range(self._message_dispatch_limit):
                    if not self._task_messages:
                        break
                    pending_messages.append(self._task_messages.popleft())
        for message in pending_messages:
            with self._lock:
                if self._task_generation.get(message.id) != message.generation:
                    self._decrement_message_count_locked(message.id)
                    continue
            try:
                message.callback(message.payload)
            except Exception as exc:
                self._enqueue_task_failure(
                    message.id,
                    message.generation,
                    f'Task message callback failed: {type(exc).__name__}: {exc}',
                )
            finally:
                with self._lock:
                    self._decrement_message_count_locked(message.id)

    def _build_task_callable(self, id: Hashable, logic: Callable[..., object], parameters: Optional[object]) -> Callable[[], object]:
        """Build task callable."""
        def run() -> object:
            """Run."""
            if parameters is None:
                outcome = logic(id)
            else:
                outcome = logic(id, parameters)

            if inspect.isawaitable(outcome):
                return asyncio.run(outcome)
            return outcome

        return run

    def _collect_finished_tasks(self) -> None:
        """Collect finished tasks."""
        completed: List[TaskCompletion] = []
        while True:
            try:
                completed.append(self._incoming_task_completions.get_nowait())
            except Empty:
                break
        for completion in completed:
            task_id = completion.id
            if self._task_generation.get(task_id) != completion.generation:
                continue
            task = self.tasks.get(task_id)
            if task is None or task.future is not completion.future:
                continue
            self._running.discard(task_id)
            try:
                result = completion.future.result()
                self._task_results[task_id] = result
                self._tasks_finished.append(task_id)
            except Exception as exc:
                self._enqueue_task_failure(task_id, completion.generation, f'{type(exc).__name__}: {exc}')
            finally:
                self.tasks.pop(task_id, None)

    def _enqueue_task_completion(self, task_id: Hashable, generation: int, future: Future[object]) -> None:
        """Enqueue task completion."""
        self._incoming_task_completions.put(TaskCompletion(id=task_id, generation=generation, future=future))

    def _enqueue_task_failure(self, task_id: Hashable, generation: int, error: str) -> None:
        """Enqueue task failure."""
        self._incoming_task_failures.put(TaskFailure(id=task_id, generation=generation, error=error))

    def _decrement_message_count_locked(self, id: Hashable) -> None:
        """Decrement message count locked."""
        count = self._task_message_counts.get(id)
        if count is None:
            return
        next_count = count - 1
        if next_count <= 0:
            self._task_message_counts.pop(id, None)
        else:
            self._task_message_counts[id] = next_count
        self._message_slots_changed.notify_all()

    def _drain_incoming_task_messages(self) -> None:
        """Drain incoming task messages."""
        drained: List[TaskMessage] = []
        with self._lock:
            ingest_limit = self._message_ingest_limit
        if ingest_limit is None:
            while True:
                try:
                    drained.append(self._incoming_task_messages.get_nowait())
                except Empty:
                    break
        else:
            for _ in range(ingest_limit):
                try:
                    drained.append(self._incoming_task_messages.get_nowait())
                except Empty:
                    break
        if not drained:
            return
        with self._lock:
            for message in drained:
                if self._task_generation.get(message.id) != message.generation:
                    self._decrement_message_count_locked(message.id)
                    continue
                self._task_messages.append(message)

    def _drain_incoming_task_failures(self) -> None:
        """Drain incoming task failures."""
        drained: List[TaskFailure] = []
        while True:
            try:
                drained.append(self._incoming_task_failures.get_nowait())
            except Empty:
                break
        if not drained:
            return
        with self._lock:
            for failure in drained:
                if self._task_generation.get(failure.id) != failure.generation:
                    continue
                self._tasks_failed.append((failure.id, failure.error))

    def _remove_from_pending(self, id: Hashable) -> None:
        """Remove from pending."""
        if id in self._pending_set:
            if id in self._pending:
                self._pending.remove(id)
            self._pending_set.discard(id)

    def _remove_from_suspended(self, id: Hashable) -> None:
        """Remove from suspended."""
        if id in self._suspended_set:
            if id in self._suspended:
                self._suspended.remove(id)
            self._suspended_set.discard(id)

    def _remove_task_internal(self, id: Hashable) -> None:
        """Remove task internal."""
        self._remove_from_pending(id)
        self._remove_from_suspended(id)
        self._task_generation[id] = self._task_generation.get(id, 0) + 1
        self._task_message_counts.pop(id, None)
        task = self.tasks.pop(id, None)
        self._task_results.pop(id, None)
        self._task_messages = deque(message for message in self._task_messages if message.id != id)
        if id in self._running:
            self._running.discard(id)
            if task is not None and task.future is not None:
                task.future.cancel()
        self._message_slots_changed.notify_all()

    def _submit_ready_tasks(self) -> None:
        """Submit ready tasks."""
        while self._pending and len(self._running) < self._max_workers:
            task_id = self._pending.popleft()
            self._pending_set.discard(task_id)
            task = self.tasks.get(task_id)
            if task is None:
                continue
            task.future = self._executor.submit(task.run_callable)
            task.future.add_done_callback(
                lambda done_future, task_id=task_id, generation=task.generation: self._enqueue_task_completion(task_id, generation, done_future)
            )
            self._running.add(task_id)

    def _validate_task_id(self, id: Hashable) -> None:
        """Validate task id."""
        try:
            hash(id)
        except TypeError as exc:
            raise GuiError(f'task id must be hashable: {id!r}') from exc

    def __del__(self) -> None:
        try:
            self.shutdown()
        except Exception as exc:
            _logger.warning('Scheduler cleanup failed: %s: %s', type(exc).__name__, exc)
