"""AsyncDataProvider — standardised loading/error/data state for data controls.

Wraps a :class:`~gui_do.TaskScheduler` task with a ``IDLE → LOADING → LOADED
/ FAILED`` state machine and notifies subscribers on every transition.
Controls can render a loading indicator, an error message, or the loaded
content automatically by inspecting :attr:`AsyncDataProvider.state`.

Usage::

    from gui_do import AsyncDataProvider, LoadState, LoadStateKind

    provider = AsyncDataProvider(scheduler=app.scheduler)

    def _fetch_records():
        # Runs on a background thread — must NOT touch pygame.
        return load_json("records.json")

    provider.subscribe(lambda state: my_list.invalidate())
    provider.load(_fetch_records)

    # In the control's draw() method:
    state = provider.state
    if state.is_loading:
        draw_spinner(surface, rect)
    elif state.is_failed:
        draw_error(surface, rect, state.error)
    elif state.is_loaded:
        draw_items(surface, rect, state.data)

    # Per frame — advance the provider so state transitions are detected:
    provider.update()

    # Cancel an in-flight load:
    provider.cancel()

    # Reload:
    provider.load(_fetch_records)

``update()`` must be called once per frame (e.g. from the owning feature's
``on_post_frame`` hook or from ``GuiApplication.update()``).  It polls the
task scheduler for completion/failure of the tracked task.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Generic, List, Optional, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from ..scheduling.task_scheduler import TaskScheduler


T = TypeVar("T")

# Sentinel used to distinguish "no result stored" from a result of None.
_SENTINEL = object()


# ---------------------------------------------------------------------------
# LoadStateKind
# ---------------------------------------------------------------------------


class LoadStateKind(Enum):
    """Phase of an asynchronous data load operation."""

    IDLE = "idle"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# LoadState
# ---------------------------------------------------------------------------


@dataclass
class LoadState(Generic[T]):
    """Immutable snapshot of an asynchronous load operation.

    Attributes
    ----------
    kind:
        Current phase.
    data:
        Loaded value.  Only meaningful when *kind* is ``LOADED``.
    error:
        Error description.  Only meaningful when *kind* is ``FAILED``.
    progress:
        Optional fractional progress 0.0–1.0 for the ``LOADING`` phase.
    """

    kind: LoadStateKind = LoadStateKind.IDLE
    data: Optional[T] = None
    error: Optional[str] = None
    progress: float = 0.0

    @property
    def is_idle(self) -> bool:
        return self.kind is LoadStateKind.IDLE

    @property
    def is_loading(self) -> bool:
        return self.kind is LoadStateKind.LOADING

    @property
    def is_loaded(self) -> bool:
        return self.kind is LoadStateKind.LOADED

    @property
    def is_failed(self) -> bool:
        return self.kind is LoadStateKind.FAILED


StateChangeCallback = Callable[["LoadState"], None]


# ---------------------------------------------------------------------------
# AsyncDataProvider
# ---------------------------------------------------------------------------


class AsyncDataProvider(Generic[T]):
    """Observable lifecycle wrapper around a :class:`~gui_do.TaskScheduler` task.

    Parameters
    ----------
    scheduler:
        The application's :class:`~gui_do.TaskScheduler` instance.
    """

    def __init__(self, scheduler: "TaskScheduler") -> None:
        self._scheduler: "TaskScheduler" = scheduler
        self._state: LoadState[T] = LoadState(kind=LoadStateKind.IDLE)
        self._listeners: List[StateChangeCallback] = []
        self._task_id: Optional[Any] = None

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, callback: StateChangeCallback) -> Callable[[], None]:
        """Register *callback* for state changes.

        Returns a no-arg callable that unsubscribes.
        """
        self._listeners.append(callback)

        def _unsub() -> None:
            try:
                self._listeners.remove(callback)
            except ValueError:
                pass

        return _unsub

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def state(self) -> LoadState[T]:
        """Current :class:`LoadState` snapshot."""
        return self._state

    @property
    def is_loading(self) -> bool:
        """Convenience shortcut: ``True`` while a load is in progress."""
        return self._state.is_loading

    # ------------------------------------------------------------------
    # Load lifecycle
    # ------------------------------------------------------------------

    def load(
        self,
        fetch_fn: Callable[[], T],
        *,
        task_id: Optional[Any] = None,
    ) -> None:
        """Schedule *fetch_fn* on the task scheduler and transition to LOADING.

        *fetch_fn* is called with ``fetch_fn()`` on a background thread — it
        must not call any pygame API.

        Parameters
        ----------
        fetch_fn:
            Zero-argument callable that returns the loaded data.
        task_id:
            Optional explicit task-id key for the scheduler (default: auto).
        """
        self.cancel()
        self._task_id = task_id if task_id is not None else f"_adp_{id(self)}"

        # Wrap fetch_fn so the scheduler receives the correct signature:
        # scheduler calls logic(task_id) when parameters is None.
        _fn = fetch_fn

        def _logic(_tid: Any) -> T:  # noqa: ANN001
            return _fn()

        self._scheduler.add_task(self._task_id, _logic)
        self._set_state(LoadState(kind=LoadStateKind.LOADING))

    def cancel(self) -> None:
        """Cancel any in-flight load and return to IDLE."""
        if self._task_id is not None:
            try:
                self._scheduler.remove_tasks(self._task_id)
            except Exception:
                pass
            self._task_id = None
        if not self._state.is_idle:
            self._set_state(LoadState(kind=LoadStateKind.IDLE))

    def reset(self) -> None:
        """Cancel the load and reset to IDLE without firing listeners."""
        if self._task_id is not None:
            try:
                self._scheduler.remove_tasks(self._task_id)
            except Exception:
                pass
            self._task_id = None
        self._state = LoadState(kind=LoadStateKind.IDLE)

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------

    def update(self) -> None:
        """Poll the scheduler for task completion or failure.

        Call once per frame from your feature's ``on_post_frame`` hook or
        from the scene update loop.  Transitions state to ``LOADED`` or
        ``FAILED`` as appropriate.
        """
        if self._task_id is None or not self._state.is_loading:
            return

        # Still running — nothing to do yet.
        if self._scheduler.tasks_active_match_any(self._task_id):
            return

        # Task is no longer active — check for a stored result.
        result = self._scheduler.pop_result(self._task_id, _SENTINEL)
        if result is not _SENTINEL:
            self._task_id = None
            self._set_state(LoadState(kind=LoadStateKind.LOADED, data=result))
            return

        # No result — check for direct failed-event match.
        event = self._scheduler.pop_failed_event(self._task_id)
        if event is not None:
            error_msg = event.error or "Unknown error"
            self._task_id = None
            self._set_state(LoadState(kind=LoadStateKind.FAILED, error=error_msg))
            return

        # Task was removed without a result (external cancel) — go back to IDLE.
        self._task_id = None
        self._set_state(LoadState(kind=LoadStateKind.IDLE))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _set_state(self, state: LoadState[T]) -> None:
        self._state = state
        for cb in list(self._listeners):
            try:
                cb(state)
            except Exception:
                pass
