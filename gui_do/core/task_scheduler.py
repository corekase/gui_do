from __future__ import annotations

import asyncio
import os
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
import inspect
from queue import Empty, Queue
from threading import Condition, RLock
from time import perf_counter
from typing import Any, Callable, Deque, Dict, Hashable, List, Optional, Set

from .telemetry import telemetry_collector


@dataclass
class TaskEvent:
    operation: str
    task_id: Hashable
    error: Optional[str] = None


@dataclass
class _Task:
    task_id: Hashable
    run_callable: Callable[[], Any]
    message_method: Optional[Callable[[Any], None]]
    generation: int
    future: Optional[Future] = None


@dataclass
class _TaskMessage:
    task_id: Hashable
    callback: Callable[[Any], None]
    payload: Any
    generation: int


@dataclass
class _TaskCompletion:
    task_id: Hashable
    generation: int
    future: Future


@dataclass
class _TaskFailure:
    task_id: Hashable
    generation: int
    error: str


class TaskScheduler:
    """Threaded task runner with queue limits, suspend/resume, and frame-safe dispatch."""

    def __init__(self, max_workers: int = 4) -> None:
        self._max_workers = max(1, int(max_workers))
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._lock = RLock()
        self._message_slots_changed = Condition(self._lock)
        self._execution_state_changed = Condition(self._lock)
        self._execution_paused = False

        self._tasks: Dict[Hashable, _Task] = {}
        self._pending: Deque[Hashable] = deque()
        self._pending_set: Set[Hashable] = set()
        self._suspended: List[Hashable] = []
        self._suspended_set: Set[Hashable] = set()
        self._running: Set[Hashable] = set()

        self._results: Dict[Hashable, Any] = {}
        self._task_generation: Dict[Hashable, int] = {}
        self._task_message_counts: Dict[Hashable, int] = {}

        self._task_messages: Deque[_TaskMessage] = deque()
        self._message_dispatch_limit: Optional[int] = None
        self._message_dispatch_time_budget_ms: Optional[float] = None
        self._message_ingest_limit: Optional[int] = 512
        self._max_queued_messages_per_task: Optional[int] = 1024

        self._incoming_messages: Queue[_TaskMessage] = Queue()
        self._incoming_failures: Queue[_TaskFailure] = Queue()
        self._incoming_completions: Queue[_TaskCompletion] = Queue()

        self._failed_events: List[TaskEvent] = []
        self._finished_events: List[TaskEvent] = []

    @staticmethod
    def recommended_worker_count(logical_cpus: Optional[int] = None, reserve_for_ui: int = 1, cap: int = 4) -> int:
        """Return a conservative worker count that keeps capacity for the UI loop."""
        cpu_count = os.cpu_count() if logical_cpus is None else logical_cpus
        try:
            normalized = int(cpu_count) if cpu_count is not None else cap
        except (TypeError, ValueError):
            normalized = cap
        normalized = max(1, normalized)
        reserved = max(0, int(reserve_for_ui))
        max_cap = max(1, int(cap))
        return max(1, min(max_cap, normalized - reserved))

    def shutdown(self) -> None:
        with self._lock:
            self._execution_paused = False
            self._execution_state_changed.notify_all()
            self.remove_all()
            self._executor.shutdown(wait=False, cancel_futures=True)

    def set_execution_paused(self, paused: bool) -> None:
        with self._lock:
            self._execution_paused = bool(paused)
            self._execution_state_changed.notify_all()

    def is_execution_paused(self) -> bool:
        with self._lock:
            return self._execution_paused

    def add_task(
        self,
        task_id: Hashable,
        logic: Callable[..., Any],
        parameters: Any = None,
        message_method: Optional[Callable[[Any], None]] = None,
    ) -> None:
        self._validate_task_id(task_id)
        if not callable(logic):
            raise ValueError("logic must be callable")
        if message_method is not None and not callable(message_method):
            raise ValueError("message_method must be callable")

        with self._lock:
            self._failed_events = [event for event in self._failed_events if event.task_id != task_id]
            self._finished_events = [event for event in self._finished_events if event.task_id != task_id]
            if task_id in self._tasks or task_id in self._running or task_id in self._pending_set or task_id in self._suspended_set:
                self._remove_task_internal(task_id)

            generation = self._task_generation.get(task_id, 0) + 1
            self._task_generation[task_id] = generation
            run_callable = self._build_task_callable(task_id, logic, parameters)
            task = _Task(task_id=task_id, run_callable=run_callable, message_method=message_method, generation=generation)
            self._tasks[task_id] = task
            self._pending.append(task_id)
            self._pending_set.add(task_id)

    def remove_tasks(self, *task_ids: Hashable) -> None:
        with self._lock:
            for task_id in task_ids:
                self._validate_task_id(task_id)
                self._remove_task_internal(task_id)
            removed = set(task_ids)
            self._finished_events = [event for event in self._finished_events if event.task_id not in removed]
            self._failed_events = [event for event in self._failed_events if event.task_id not in removed]
            self._task_messages = deque(message for message in self._task_messages if message.task_id not in removed)

    def remove_all(self) -> None:
        with self._lock:
            ids = list(self._tasks.keys())
            for task_id in ids:
                self._remove_task_internal(task_id)
            self._pending.clear()
            self._pending_set.clear()
            self._suspended.clear()
            self._suspended_set.clear()
            self._running.clear()
            self._results.clear()
            self._task_messages.clear()
            self._task_message_counts.clear()
            self._message_slots_changed.notify_all()

    def suspend_all(self) -> None:
        with self._lock:
            for task_id in list(self._pending):
                if task_id not in self._suspended_set:
                    self._suspended.append(task_id)
                    self._suspended_set.add(task_id)
            self._pending.clear()
            self._pending_set.clear()

    def suspend_tasks(self, *task_ids: Hashable) -> None:
        with self._lock:
            for task_id in task_ids:
                self._validate_task_id(task_id)
                if task_id in self._pending_set:
                    self._remove_from_pending(task_id)
                    if task_id not in self._suspended_set:
                        self._suspended.append(task_id)
                        self._suspended_set.add(task_id)

    def resume_all(self) -> None:
        with self._lock:
            for task_id in list(self._suspended):
                if task_id in self._tasks and task_id not in self._pending_set:
                    self._pending.append(task_id)
                    self._pending_set.add(task_id)
            self._suspended.clear()
            self._suspended_set.clear()

    def resume_tasks(self, *task_ids: Hashable) -> None:
        with self._lock:
            for task_id in task_ids:
                self._validate_task_id(task_id)
                if task_id in self._suspended_set:
                    self._remove_from_suspended(task_id)
                    if task_id in self._tasks and task_id not in self._pending_set:
                        self._pending.append(task_id)
                        self._pending_set.add(task_id)

    def read_suspended(self) -> List[Hashable]:
        with self._lock:
            return self._suspended.copy()

    def read_suspended_len(self) -> int:
        with self._lock:
            return len(self._suspended)

    def tasks_active(self) -> bool:
        with self._lock:
            return bool(self._pending_set or self._running)

    def tasks_active_match_all(self, *task_ids: Hashable) -> bool:
        with self._lock:
            for task_id in task_ids:
                self._validate_task_id(task_id)
                if task_id not in self._pending_set and task_id not in self._running:
                    return False
            return True

    def tasks_active_match_any(self, *task_ids: Hashable) -> bool:
        with self._lock:
            for task_id in task_ids:
                self._validate_task_id(task_id)
                if task_id in self._pending_set or task_id in self._running:
                    return True
            return False

    def tasks_busy(self) -> bool:
        with self._lock:
            return bool(self._pending_set or self._running or self._task_message_counts)

    def tasks_busy_match_any(self, *task_ids: Hashable) -> bool:
        with self._lock:
            for task_id in task_ids:
                self._validate_task_id(task_id)
                if task_id in self._pending_set or task_id in self._running:
                    return True
                if self._task_message_counts.get(task_id, 0) > 0:
                    return True
            return False

    # --- Count queries ---

    def pending_count(self) -> int:
        """Return the number of tasks currently queued and waiting to be submitted."""
        with self._lock:
            return len(self._pending_set)

    def running_count(self) -> int:
        """Return the number of tasks currently executing in the thread pool."""
        with self._lock:
            return len(self._running)

    def suspended_count(self) -> int:
        """Return the number of tasks currently suspended."""
        with self._lock:
            return len(self._suspended_set)

    def task_count(self) -> int:
        """Return the total number of known tasks (pending + running + suspended)."""
        with self._lock:
            return len(self._pending_set) + len(self._running) + len(self._suspended_set)

    def set_max_queued_messages_per_task(self, max_queued_messages: Optional[int]) -> None:
        if max_queued_messages is not None:
            if not isinstance(max_queued_messages, int):
                raise ValueError(f"max_queued_messages must be int or None, got: {type(max_queued_messages).__name__}")
            if max_queued_messages <= 0:
                raise ValueError(f"max_queued_messages must be > 0, got: {max_queued_messages}")
        with self._lock:
            self._max_queued_messages_per_task = max_queued_messages
            self._message_slots_changed.notify_all()

    def get_max_queued_messages_per_task(self) -> Optional[int]:
        with self._lock:
            return self._max_queued_messages_per_task

    def set_message_dispatch_limit(self, max_messages_per_update: Optional[int]) -> None:
        if max_messages_per_update is not None:
            if not isinstance(max_messages_per_update, int):
                raise ValueError(f"max_messages_per_update must be int or None, got: {type(max_messages_per_update).__name__}")
            if max_messages_per_update <= 0:
                raise ValueError(f"max_messages_per_update must be > 0, got: {max_messages_per_update}")
        with self._lock:
            self._message_dispatch_limit = max_messages_per_update

    def get_message_dispatch_limit(self) -> Optional[int]:
        with self._lock:
            return self._message_dispatch_limit

    def set_message_dispatch_time_budget_ms(self, budget_ms: Optional[float]) -> None:
        if budget_ms is not None:
            if not isinstance(budget_ms, (int, float)):
                raise ValueError(f"budget_ms must be number or None, got: {type(budget_ms).__name__}")
            if budget_ms <= 0:
                raise ValueError(f"budget_ms must be > 0, got: {budget_ms}")
        with self._lock:
            self._message_dispatch_time_budget_ms = None if budget_ms is None else float(budget_ms)

    def get_message_dispatch_time_budget_ms(self) -> Optional[float]:
        with self._lock:
            return self._message_dispatch_time_budget_ms

    def set_message_ingest_limit(self, max_messages_per_update: Optional[int]) -> None:
        if max_messages_per_update is not None:
            if not isinstance(max_messages_per_update, int):
                raise ValueError(f"max_messages_per_update must be int or None, got: {type(max_messages_per_update).__name__}")
            if max_messages_per_update <= 0:
                raise ValueError(f"max_messages_per_update must be > 0, got: {max_messages_per_update}")
        with self._lock:
            self._message_ingest_limit = max_messages_per_update

    def get_message_ingest_limit(self) -> Optional[int]:
        with self._lock:
            return self._message_ingest_limit

    def send_message(self, task_id: Hashable, payload: Any) -> None:
        self._validate_task_id(task_id)
        send_start = perf_counter()
        collector = telemetry_collector()
        queued_count = 0
        with self._lock:
            while True:
                task = self._tasks.get(task_id)
                if task is None:
                    raise ValueError(f"unknown task id: {task_id}")
                if task.message_method is None:
                    raise ValueError(f"task '{task_id}' has no message handler")
                if not callable(task.message_method):
                    raise ValueError(f"task '{task_id}' message handler is not callable")
                if self._execution_paused:
                    self._execution_state_changed.wait()
                    continue
                queued_count = self._task_message_counts.get(task_id, 0)
                if self._max_queued_messages_per_task is None or queued_count < self._max_queued_messages_per_task:
                    break
                self._message_slots_changed.wait()

            self._task_message_counts[task_id] = self._task_message_counts.get(task_id, 0) + 1
            message = _TaskMessage(task_id=task_id, callback=task.message_method, payload=payload, generation=task.generation)
        self._incoming_messages.put(message)
        collector.record_duration(
            "task_scheduler",
            "message_send_wait",
            (perf_counter() - send_start) * 1000.0,
            metadata={"task_id": str(task_id), "queued_before_send": queued_count},
        )

    def pop_result(self, task_id: Hashable, default: Any = None) -> Any:
        return self._results.pop(task_id, default)

    def get_finished_events(self) -> List[TaskEvent]:
        return list(self._finished_events)

    def get_finished_tasks(self) -> List[Hashable]:
        return [event.task_id for event in self._finished_events if event.operation == "finished"]

    def get_failed_events(self) -> List[TaskEvent]:
        return list(self._failed_events)

    def get_failed_tasks(self) -> List[tuple[Hashable, str]]:
        return [(event.task_id, event.error or "") for event in self._failed_events if event.operation == "failed"]

    def clear_events(self) -> None:
        self._finished_events.clear()
        self._failed_events.clear()

    def clear_finished_tasks(self) -> None:
        self._finished_events.clear()

    def clear_failed_tasks(self) -> None:
        self._failed_events.clear()

    def update(self) -> List[Hashable]:
        collector = telemetry_collector()
        with collector.span("task_scheduler", "update"):
            with self._lock:
                with collector.span("task_scheduler", "submit_ready_tasks"):
                    self._submit_ready_tasks()
                with collector.span("task_scheduler", "collect_finished_tasks"):
                    finished = self._collect_finished_tasks()
            with collector.span("task_scheduler", "drain_messages"):
                self._drain_messages()
            with collector.span("task_scheduler", "drain_failures"):
                self._drain_failures()
            with collector.span("task_scheduler", "dispatch_messages"):
                self._dispatch_messages()
            with collector.span("task_scheduler", "drain_failures"):
                self._drain_failures()
            collector.record_duration(
                "task_scheduler",
                "finished_count",
                0.0,
                metadata={"count": len(finished)},
            )
            return finished

    def _build_task_callable(self, task_id: Hashable, logic: Callable[..., Any], parameters: Any) -> Callable[[], Any]:
        def run() -> Any:
            self._wait_if_execution_paused()
            if parameters is None:
                outcome = logic(task_id)
            else:
                outcome = logic(task_id, parameters)
            if inspect.isawaitable(outcome):
                return asyncio.run(outcome)
            return outcome

        return run

    def _wait_if_execution_paused(self) -> None:
        with self._lock:
            while self._execution_paused:
                self._execution_state_changed.wait()

    def _enqueue_completion(self, task_id: Hashable, generation: int, future: Future) -> None:
        self._incoming_completions.put(_TaskCompletion(task_id=task_id, generation=generation, future=future))

    def _enqueue_failure(self, task_id: Hashable, generation: int, error: str) -> None:
        self._incoming_failures.put(_TaskFailure(task_id=task_id, generation=generation, error=error))

    def _submit_ready_tasks(self) -> None:
        collector = telemetry_collector()
        submitted = 0
        while self._pending and len(self._running) < self._max_workers:
            task_id = self._pending.popleft()
            self._pending_set.discard(task_id)
            task = self._tasks.get(task_id)
            if task is None:
                continue
            task.future = self._executor.submit(task.run_callable)
            task.future.add_done_callback(
                lambda done_future, _task_id=task_id, _generation=task.generation: self._enqueue_completion(_task_id, _generation, done_future)
            )
            self._running.add(task_id)
            submitted += 1
        if submitted:
            collector.record_duration("task_scheduler", "submitted_count", 0.0, metadata={"count": submitted})

    def _collect_finished_tasks(self) -> List[Hashable]:
        collector = telemetry_collector()
        finished_task_ids: List[Hashable] = []
        completions: List[_TaskCompletion] = []
        while True:
            try:
                completions.append(self._incoming_completions.get_nowait())
            except Empty:
                break
        for completion in completions:
            task_id = completion.task_id
            if self._task_generation.get(task_id) != completion.generation:
                continue
            task = self._tasks.get(task_id)
            if task is None or task.future is not completion.future:
                continue
            self._running.discard(task_id)
            try:
                result = completion.future.result()
                self._results[task_id] = result
                self._finished_events.append(TaskEvent("finished", task_id))
                finished_task_ids.append(task_id)
            except Exception as exc:  # noqa: BLE001
                self._enqueue_failure(task_id, completion.generation, f"{type(exc).__name__}: {exc}")
            finally:
                self._tasks.pop(task_id, None)
        if completions:
            collector.record_duration(
                "task_scheduler",
                "completion_count",
                0.0,
                metadata={"count": len(completions), "finished": len(finished_task_ids)},
            )
        return finished_task_ids

    def _drain_messages(self) -> None:
        collector = telemetry_collector()
        drained: List[_TaskMessage] = []
        with self._lock:
            ingest_limit = self._message_ingest_limit
        if ingest_limit is None:
            while True:
                try:
                    drained.append(self._incoming_messages.get_nowait())
                except Empty:
                    break
        else:
            for _ in range(ingest_limit):
                try:
                    drained.append(self._incoming_messages.get_nowait())
                except Empty:
                    break
        if not drained:
            return
        with self._lock:
            for message in drained:
                if self._task_generation.get(message.task_id) != message.generation:
                    self._decrement_message_count_locked(message.task_id)
                    continue
                self._task_messages.append(message)
        collector.record_duration(
            "task_scheduler",
            "drained_message_count",
            0.0,
            metadata={"count": len(drained)},
        )

    def _dispatch_messages(self) -> None:
        collector = telemetry_collector()
        dispatch_start = perf_counter()
        dispatched_count = 0
        while True:
            message = None
            with self._lock:
                if not self._task_messages:
                    break
                if self._message_dispatch_limit is not None and dispatched_count >= self._message_dispatch_limit:
                    break
                if (
                    self._message_dispatch_time_budget_ms is not None
                    and dispatched_count > 0
                    and ((perf_counter() - dispatch_start) * 1000.0) >= self._message_dispatch_time_budget_ms
                ):
                    break
                message = self._task_messages.popleft()
                if self._task_generation.get(message.task_id) != message.generation:
                    self._decrement_message_count_locked(message.task_id)
                    continue

            try:
                with collector.span(
                    "task_scheduler",
                    "message_callback",
                    metadata={"task_id": str(message.task_id)},
                ):
                    message.callback(message.payload)
            except Exception as exc:  # noqa: BLE001
                self._enqueue_failure(
                    message.task_id,
                    message.generation,
                    f"Task message callback failed: {type(exc).__name__}: {exc}",
                )
            finally:
                with self._lock:
                    self._decrement_message_count_locked(message.task_id)
            dispatched_count += 1
        if dispatched_count:
            collector.record_duration(
                "task_scheduler",
                "dispatched_message_count",
                0.0,
                metadata={"count": dispatched_count},
            )

    def _drain_failures(self) -> None:
        while True:
            try:
                failure = self._incoming_failures.get_nowait()
            except Empty:
                break
            with self._lock:
                if self._task_generation.get(failure.task_id) != failure.generation:
                    continue
                self._failed_events.append(TaskEvent("failed", failure.task_id, failure.error))
                self._tasks.pop(failure.task_id, None)
                self._running.discard(failure.task_id)

    def _decrement_message_count_locked(self, task_id: Hashable) -> None:
        count = self._task_message_counts.get(task_id)
        if count is None:
            return
        next_count = count - 1
        if next_count <= 0:
            self._task_message_counts.pop(task_id, None)
        else:
            self._task_message_counts[task_id] = next_count
        self._message_slots_changed.notify_all()

    def _remove_from_pending(self, task_id: Hashable) -> None:
        if task_id in self._pending_set:
            if task_id in self._pending:
                self._pending.remove(task_id)
            self._pending_set.discard(task_id)

    def _remove_from_suspended(self, task_id: Hashable) -> None:
        if task_id in self._suspended_set:
            if task_id in self._suspended:
                self._suspended.remove(task_id)
            self._suspended_set.discard(task_id)

    def _remove_task_internal(self, task_id: Hashable) -> None:
        self._remove_from_pending(task_id)
        self._remove_from_suspended(task_id)
        self._task_generation[task_id] = self._task_generation.get(task_id, 0) + 1
        self._task_message_counts.pop(task_id, None)
        task = self._tasks.pop(task_id, None)
        self._results.pop(task_id, None)
        self._task_messages = deque(message for message in self._task_messages if message.task_id != task_id)
        if task_id in self._running:
            self._running.discard(task_id)
            if task is not None and task.future is not None:
                task.future.cancel()
        self._message_slots_changed.notify_all()

    def _validate_task_id(self, task_id: Hashable) -> None:
        try:
            hash(task_id)
        except TypeError as exc:
            raise ValueError(f"task id must be hashable: {task_id!r}") from exc
