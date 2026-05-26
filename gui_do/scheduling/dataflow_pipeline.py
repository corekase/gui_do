"""DataflowPipeline — cancelable multi-stage data processing pipeline.

Provides thread-safe cancellation, stale-generation rejection, and
simple sequential stage chaining.  Designed for UI-side async workflows
where multiple in-flight requests may be superseded by newer ones.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Generic, Iterable, Optional, TypeVar, List

__all__ = ["CancellationToken", "PipelineStage", "DataflowPipeline", "PipelineHandle"]

T = TypeVar("T")
U = TypeVar("U")


# ---------------------------------------------------------------------------
# CancellationToken
# ---------------------------------------------------------------------------


class CancellationToken:
    """Thread-safe cancellation flag.

    Callers pass the token to long-running work; the work polls
    :attr:`is_cancelled` and returns early when set.
    """

    __slots__ = ("_event",)

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        """Signal cancellation."""
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        """``True`` once :meth:`cancel` has been called."""
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        """Raise :exc:`CancelledError` if cancelled."""
        if self.is_cancelled:
            raise CancelledError()


class CancelledError(Exception):
    """Raised when a cancelled pipeline stage is entered."""


# ---------------------------------------------------------------------------
# PipelineStage
# ---------------------------------------------------------------------------


class PipelineStage(Generic[T, U]):
    """A single named transform in a :class:`DataflowPipeline`.

    Parameters
    ----------
    name:
        Human-readable label used in :meth:`DataflowPipeline.__repr__`.
    transform:
        Callable ``(value: T, token: CancellationToken) -> U``.
    """

    __slots__ = ("name", "transform")

    def __init__(
        self,
        name: str,
        transform: Callable[[T, CancellationToken], U],
    ) -> None:
        self.name = name
        self.transform = transform

    def __repr__(self) -> str:
        return f"PipelineStage({self.name!r})"


# ---------------------------------------------------------------------------
# PipelineHandle
# ---------------------------------------------------------------------------


class PipelineHandle:
    """Handle returned by :meth:`DataflowPipeline.run`.

    Allows callers to cancel in-flight execution and query status.
    """

    def __init__(self, token: CancellationToken, generation: int) -> None:
        self._token = token
        self._generation = generation
        self._result: Any = _MISSING
        self._error: Optional[BaseException] = None
        self._done_event = threading.Event()

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Request cancellation of the associated pipeline run."""
        self._token.cancel()

    @property
    def is_cancelled(self) -> bool:
        return self._token.is_cancelled

    @property
    def is_done(self) -> bool:
        return self._done_event.is_set()

    @property
    def result(self) -> Any:
        """The pipeline output, or raises the captured exception."""
        if self._error is not None:
            raise self._error
        if self._result is _MISSING:
            raise RuntimeError("Pipeline has not finished yet")
        return self._result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _set_result(self, value: Any) -> None:
        self._result = value
        self._done_event.set()

    def _set_error(self, exc: BaseException) -> None:
        self._error = exc
        self._done_event.set()


class _Missing:
    __slots__ = ()


_MISSING = _Missing()


# ---------------------------------------------------------------------------
# DataflowPipeline
# ---------------------------------------------------------------------------


class DataflowPipeline:
    """Sequential pipeline of :class:`PipelineStage` objects.

    Each call to :meth:`run` increments an internal *generation* counter.
    Superseded (stale) runs are cancelled via their :class:`CancellationToken`
    before the new run starts, providing automatic backpressure for callers
    that fire successive requests.

    Stages are executed **synchronously on the calling thread** of
    :meth:`run`.  For background execution wrap the call in a thread; the
    token/generation mechanism remains correct across threads.
    """

    def __init__(self, stages: Iterable[PipelineStage] = ()) -> None:
        self._stages: List[PipelineStage] = list(stages)
        self._lock = threading.Lock()
        self._generation = 0
        self._current_handle: Optional[PipelineHandle] = None

    # ------------------------------------------------------------------
    # Stage management
    # ------------------------------------------------------------------

    def add_stage(self, stage: PipelineStage) -> None:
        """Append *stage* to the end of the pipeline."""
        self._stages.append(stage)

    @property
    def stages(self) -> List[PipelineStage]:
        return list(self._stages)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, initial_value: Any) -> PipelineHandle:
        """Execute the pipeline starting with *initial_value*.

        Cancels any previously active handle before starting.
        Returns a :class:`PipelineHandle` for the new run.
        """
        with self._lock:
            if self._current_handle is not None and not self._current_handle.is_done:
                self._current_handle.cancel()
            self._generation += 1
            gen = self._generation
            token = CancellationToken()
            handle = PipelineHandle(token, gen)
            self._current_handle = handle

        try:
            value = initial_value
            for stage in self._stages:
                token.raise_if_cancelled()
                value = stage.transform(value, token)
            handle._set_result(value)
        except CancelledError as exc:
            handle._set_error(exc)
        except Exception as exc:
            handle._set_error(exc)

        return handle

    def __repr__(self) -> str:
        names = " -> ".join(s.name for s in self._stages)
        return f"DataflowPipeline([{names}])"
