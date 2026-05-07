"""CooperativeScheduler — frame-driven generator coroutine runner.

Allows complex multi-step behaviors (tutorials, cutscenes, AI sequences,
integration-test scripts) to be written as linear ``yield``-based generator
functions.  All execution happens on the frame thread — no threads or OS
timers are used.

Yield tokens
------------
- :class:`Pause` — suspend for exactly one frame.
- :class:`Sleep` — suspend for *seconds* seconds.
- :class:`WaitForEvent` — suspend until an ``EventBus`` emits a matching event.
- :class:`WaitForSignal` — suspend until a ``Signal`` fires.
- :class:`WaitUntil` — suspend until a predicate returns ``True``.
- :class:`WaitForAll` — suspend until all listed ``CoroutineHandle`` objects complete.

Usage::

    from gui_do import (
        CooperativeScheduler, CoroutineHandle,
        Pause, Sleep, WaitForSignal, WaitUntil, WaitForAll,
    )

    scheduler = CooperativeScheduler()

    def intro_sequence():
        show_title()
        yield Sleep(1.5)
        fade_in_logo()
        yield Sleep(2.0)
        yield WaitUntil(lambda: user_pressed_any_key())
        start_game()

    handle = scheduler.start(intro_sequence())

    # In your frame loop:
    def update(dt):
        scheduler.update(dt)

    # Cancel if needed:
    handle.cancel()
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generator, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Yield tokens
# ---------------------------------------------------------------------------


@dataclass
class Pause:
    """Yield this to suspend the coroutine for exactly one frame."""


@dataclass
class Sleep:
    """Yield this to suspend the coroutine for *seconds* seconds.

    Parameters
    ----------
    seconds:
        How long to wait in seconds.  Must be >= 0.
    """
    seconds: float

    def __post_init__(self) -> None:
        if self.seconds < 0:
            raise ValueError(f"Sleep.seconds must be >= 0, got {self.seconds}")


@dataclass
class WaitForEvent:
    """Yield this to suspend until an ``EventBus`` emits a matching event.

    Parameters
    ----------
    event_type:
        The event type string to listen for.
    bus:
        The :class:`~gui_do.EventBus` to subscribe to.
    predicate:
        Optional additional filter applied to the emitted payload.
        Defaults to accepting any payload.
    """
    event_type: str
    bus: Any  # EventBus — typed as Any to avoid circular import
    predicate: Optional[Callable[[Any], bool]] = None


@dataclass
class WaitForSignal:
    """Yield this to suspend until a :class:`~gui_do.Signal` fires.

    Parameters
    ----------
    signal:
        The :class:`~gui_do.Signal` to subscribe to.
    predicate:
        Optional filter applied to the emitted value.
    """
    signal: Any  # Signal — typed as Any to avoid circular import
    predicate: Optional[Callable[[Any], bool]] = None


@dataclass
class WaitUntil:
    """Yield this to suspend until *predicate()* returns ``True``.

    The predicate is polled once per frame.
    """
    predicate: Callable[[], bool]


@dataclass
class WaitForAll:
    """Yield this to suspend until all listed coroutine handles complete.

    Parameters
    ----------
    handles:
        :class:`CoroutineHandle` objects to wait for.
    """
    handles: List["CoroutineHandle"]


# ---------------------------------------------------------------------------
# CoroutineHandle
# ---------------------------------------------------------------------------


class CoroutineHandle:
    """Opaque handle to a running coroutine managed by :class:`CooperativeScheduler`.

    Attributes
    ----------
    is_running:
        ``True`` while the coroutine has not finished or been cancelled.
    is_complete:
        ``True`` after the coroutine generator has been exhausted.
    is_cancelled:
        ``True`` after :meth:`cancel` has been called.
    """

    def __init__(self, gen: Generator) -> None:
        self._gen = gen
        self._is_complete = False
        self._is_cancelled = False
        self._wait_state: Optional[Any] = None  # current yield token being awaited
        self._wait_elapsed: float = 0.0
        self._wait_unsub: Optional[Callable[[], None]] = None
        self._wait_triggered: bool = False

    @property
    def is_running(self) -> bool:
        return not self._is_complete and not self._is_cancelled

    @property
    def is_complete(self) -> bool:
        return self._is_complete

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def cancel(self) -> None:
        """Cancel the coroutine.  Any pending subscriptions are cleaned up."""
        if not self.is_running:
            return
        self._is_cancelled = True
        self._cleanup_wait()
        try:
            self._gen.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cleanup_wait(self) -> None:
        if self._wait_unsub is not None:
            try:
                self._wait_unsub()
            except Exception:
                pass
            self._wait_unsub = None
        self._wait_state = None
        self._wait_triggered = False
        self._wait_elapsed = 0.0


# ---------------------------------------------------------------------------
# CooperativeScheduler
# ---------------------------------------------------------------------------


class CooperativeScheduler:
    """Frame-driven cooperative coroutine scheduler.

    All coroutines run on the calling thread (the pygame frame thread).
    No OS threads or async I/O are used.

    Usage::

        scheduler = CooperativeScheduler()
        handle = scheduler.start(my_generator())

        # Each frame:
        scheduler.update(dt)
    """

    def __init__(self) -> None:
        self._handles: List[CoroutineHandle] = []
        self._pending_starts: List[CoroutineHandle] = []
        self._updating: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, generator: Generator) -> CoroutineHandle:
        """Start a coroutine from *generator* and return its handle.

        The generator must be a Python generator object (the result of
        calling a ``def ... yield ...`` function).
        """
        handle = CoroutineHandle(generator)
        # Run until the first yield
        self._step(handle)
        if handle.is_running:
            if self._updating:
                self._pending_starts.append(handle)
            else:
                self._handles.append(handle)
        return handle

    def cancel_all(self) -> None:
        """Cancel all running coroutines."""
        for h in list(self._handles):
            h.cancel()
        self._handles.clear()

    @property
    def coroutine_count(self) -> int:
        """Number of currently running coroutines."""
        return sum(1 for h in self._handles if h.is_running)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance all coroutines by *dt* seconds.

        Call once per frame.
        """
        if not self._handles:
            if self._pending_starts:
                self._handles.extend(self._pending_starts)
                self._pending_starts.clear()
            return
        self._updating = True
        try:
            write = 0
            for handle in self._handles:
                if not handle.is_running:
                    continue
                if self._try_resume(handle, dt):
                    self._step(handle)
                if handle.is_running:
                    self._handles[write] = handle
                    write += 1
            del self._handles[write:]
        finally:
            self._updating = False
            if self._pending_starts:
                self._handles.extend(self._pending_starts)
                self._pending_starts.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _try_resume(self, handle: CoroutineHandle, dt: float) -> bool:
        """Return True if *handle* is ready to be stepped again."""
        ws = handle._wait_state
        if ws is None:
            return True

        if type(ws) is Pause:
            handle._cleanup_wait()
            return True

        if type(ws) is Sleep:
            handle._wait_elapsed += dt
            if handle._wait_elapsed >= ws.seconds:
                handle._cleanup_wait()
                return True
            return False

        if type(ws) is WaitForEvent or type(ws) is WaitForSignal:
            if handle._wait_triggered:
                handle._cleanup_wait()
                return True
            return False

        if type(ws) is WaitUntil:
            if ws.predicate():
                handle._cleanup_wait()
                return True
            return False

        if type(ws) is WaitForAll:
            all_done = all(
                h.is_complete or h.is_cancelled
                for h in ws.handles
            )
            if all_done:
                handle._cleanup_wait()
                return True
            return False

        # Unknown yield token — treat as Pause
        handle._cleanup_wait()
        return True

    def _step(self, handle: CoroutineHandle) -> None:
        """Run the coroutine until it yields or returns."""
        try:
            token = next(handle._gen)
        except StopIteration:
            handle._is_complete = True
            return
        except Exception:
            handle._is_complete = True
            return

        # Process yield token
        handle._wait_state = token
        handle._wait_elapsed = 0.0
        handle._wait_triggered = False
        handle._wait_unsub = None

        if isinstance(token, (Pause, Sleep, WaitUntil, WaitForAll)):
            return  # timer/poll — handled in _try_resume

        if type(token) is WaitForEvent:
            def _on_event(payload: Any) -> None:
                if token.predicate is None or token.predicate(payload):
                    handle._wait_triggered = True
            try:
                handle._wait_unsub = token.bus.subscribe(token.event_type, _on_event)
            except Exception:
                handle._wait_triggered = True  # fail-safe: resume immediately
            return

        if type(token) is WaitForSignal:
            triggered = [False]

            def _on_signal(value: Any) -> None:
                if not triggered[0]:
                    if token.predicate is None or token.predicate(value):
                        triggered[0] = True
                        handle._wait_triggered = True

            try:
                unsub = token.signal.subscribe(_on_signal)
                handle._wait_unsub = unsub
            except Exception:
                handle._wait_triggered = True
            return

        # Unknown token: resume next frame
        handle._wait_state = Pause()
