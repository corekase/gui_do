from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from queue import Empty, Queue
from threading import Lock
from typing import Any, Callable, Dict, Hashable, List, Optional, Tuple


@dataclass
class TaskEvent:
    operation: str
    task_id: Hashable
    error: Optional[str] = None


@dataclass
class _Task:
    task_id: Hashable
    logic: Callable[..., Any]
    parameters: Any
    message_method: Optional[Callable[[Any], None]]
    future: Optional[Future] = None


class TaskScheduler:
    """Background task runner with frame-safe message and completion dispatch."""

    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max(1, int(max_workers)))
        self._lock = Lock()
        self._tasks: Dict[Hashable, _Task] = {}
        self._results: Dict[Hashable, Any] = {}
        self._incoming_messages: Queue[Tuple[Hashable, Any]] = Queue()
        self._incoming_failures: Queue[Tuple[Hashable, str]] = Queue()
        self._incoming_completions: Queue[Hashable] = Queue()
        self._failed_events: List[TaskEvent] = []
        self._finished_events: List[TaskEvent] = []

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        with self._lock:
            self._tasks.clear()

    def add_task(
        self,
        task_id: Hashable,
        logic: Callable[..., Any],
        parameters: Any = None,
        message_method: Optional[Callable[[Any], None]] = None,
    ) -> None:
        if not callable(logic):
            raise ValueError("logic must be callable")
        with self._lock:
            if task_id in self._tasks:
                raise ValueError(f"duplicate task id: {task_id}")
            task = _Task(task_id, logic, parameters, message_method)
            self._tasks[task_id] = task
            task.future = self._executor.submit(self._run_task, task)

    def remove_tasks(self, *task_ids: Hashable) -> None:
        with self._lock:
            for task_id in task_ids:
                task = self._tasks.pop(task_id, None)
                if task is not None and task.future is not None:
                    task.future.cancel()

    def send_message(self, task_id: Hashable, payload: Any) -> None:
        self._incoming_messages.put((task_id, payload))

    def pop_result(self, task_id: Hashable, default: Any = None) -> Any:
        return self._results.pop(task_id, default)

    def get_finished_events(self) -> List[TaskEvent]:
        return list(self._finished_events)

    def get_failed_events(self) -> List[TaskEvent]:
        return list(self._failed_events)

    def clear_events(self) -> None:
        self._finished_events.clear()
        self._failed_events.clear()

    def update(self) -> None:
        self._drain_messages()
        self._drain_failures()
        self._drain_completions()

    def _run_task(self, task: _Task) -> Any:
        try:
            if task.parameters is None:
                result = task.logic(task.task_id)
            else:
                result = task.logic(task.task_id, task.parameters)
            self._results[task.task_id] = result
            self._incoming_completions.put(task.task_id)
            return result
        except Exception as exc:  # noqa: BLE001
            self._incoming_failures.put((task.task_id, f"{type(exc).__name__}: {exc}"))
            raise

    def _drain_messages(self) -> None:
        while True:
            try:
                task_id, payload = self._incoming_messages.get_nowait()
            except Empty:
                break
            task = self._tasks.get(task_id)
            if task is None or task.message_method is None:
                continue
            try:
                task.message_method(payload)
            except Exception as exc:  # noqa: BLE001
                self._failed_events.append(TaskEvent("failed", task_id, f"Task message callback failed: {type(exc).__name__}: {exc}"))

    def _drain_failures(self) -> None:
        while True:
            try:
                task_id, error = self._incoming_failures.get_nowait()
            except Empty:
                break
            with self._lock:
                self._tasks.pop(task_id, None)
            self._failed_events.append(TaskEvent("failed", task_id, error))

    def _drain_completions(self) -> None:
        while True:
            try:
                task_id = self._incoming_completions.get_nowait()
            except Empty:
                break
            with self._lock:
                self._tasks.pop(task_id, None)
            self._finished_events.append(TaskEvent("finished", task_id, None))
