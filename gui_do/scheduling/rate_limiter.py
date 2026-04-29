"""Debouncer and Throttler — rate-limiting utilities for callback-heavy input paths.

Both utilities are portable pure-Python classes that use the frame-driven
:class:`~gui_do.Timers` service internally.  No OS-level timer APIs are used.

:class:`Debouncer`
    Delays a callback until the input is idle for a configurable period.
    Subsequent calls within the delay window restart the timer.  Ideal for
    search-as-you-type, auto-save triggers, and window-resize completions.

:class:`Throttler`
    Ensures a callback is invoked at most once per interval, discarding
    intermediate calls.  Ideal for scroll handlers, telemetry sampling, and
    progress updates.

Usage::

    from gui_do import Debouncer, Throttler, Timers

    timers = app.timers          # or any Timers instance

    # Debounce: wait 300 ms of inactivity before firing
    debounce = Debouncer(delay_ms=300, callback=update_search, timers=timers)
    text_input.on_change = lambda text: debounce.call(text)

    # Throttle: fire at most once every 100 ms
    throttle = Throttler(interval_ms=100, callback=update_preview)
    scrollbar.on_change = lambda offset: throttle.call(offset)

    # Cancel pending debounce (e.g. on dialog close):
    debounce.cancel()

    # Flush a pending debounced call immediately:
    debounce.flush()

Both classes are safe to reuse across frames and safe to cancel at any time.
"""
from __future__ import annotations

from typing import Any, Callable, Hashable, Optional, Tuple


# ---------------------------------------------------------------------------
# Debouncer
# ---------------------------------------------------------------------------


class Debouncer:
    """Delays *callback* until input is idle for *delay_ms* milliseconds.

    Each call to :meth:`call` resets the delay window.  The callback fires
    with the arguments from the **most recent** :meth:`call` invocation.

    Parameters
    ----------
    delay_ms:
        Idle time in milliseconds before the callback is invoked.
    callback:
        The function to call after the idle period.
    timers:
        The :class:`~gui_do.Timers` instance used to schedule the delayed call.
    timer_id:
        Optional explicit key for the internal timer entry.  Defaults to a
        unique object key so multiple Debouncers share the same Timers safely.
    """

    def __init__(
        self,
        delay_ms: int,
        callback: Callable,
        timers,
        *,
        timer_id: Optional[Hashable] = None,
    ) -> None:
        if delay_ms <= 0:
            raise ValueError("delay_ms must be > 0")
        if not callable(callback):
            raise ValueError("callback must be callable")
        self._delay_s: float = int(delay_ms) / 1000.0
        self._callback: Callable = callback
        self._timers = timers
        self._timer_id: Hashable = timer_id if timer_id is not None else object()
        self._pending_args: Tuple = ()
        self._pending_kwargs: dict = {}
        self._pending: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def call(self, *args: Any, **kwargs: Any) -> None:
        """Trigger the debounce with *args* and *kwargs*.

        Resets the idle window; the callback will fire *delay_ms* after the
        last call to this method.
        """
        self._pending_args = args
        self._pending_kwargs = kwargs
        self._pending = True
        # Cancel any existing pending timer and re-arm
        self._timers.remove_timer(self._timer_id)
        self._timers.add_once(self._timer_id, self._delay_s, self._fire)

    def cancel(self) -> None:
        """Cancel the pending debounced call (if any) without firing it."""
        self._timers.remove_timer(self._timer_id)
        self._pending = False
        self._pending_args = ()
        self._pending_kwargs = {}

    def flush(self) -> None:
        """Fire the pending callback immediately (if pending) and cancel the timer."""
        if not self._pending:
            return
        self._timers.remove_timer(self._timer_id)
        self._fire()

    @property
    def is_pending(self) -> bool:
        """Return True while a debounced call is waiting to fire."""
        return self._pending

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fire(self) -> None:
        args = self._pending_args
        kwargs = self._pending_kwargs
        self._pending = False
        self._pending_args = ()
        self._pending_kwargs = {}
        self._callback(*args, **kwargs)


# ---------------------------------------------------------------------------
# Throttler
# ---------------------------------------------------------------------------


class Throttler:
    """Limits *callback* to at most one invocation per *interval_ms* milliseconds.

    The first call always fires immediately.  Subsequent calls within the
    interval are buffered; the most-recent buffered call fires at the end of
    the interval (trailing-edge behaviour).

    Parameters
    ----------
    interval_ms:
        Minimum milliseconds between successive callback invocations.
    callback:
        The function to invoke (with the same args as :meth:`call`).
    timers:
        The :class:`~gui_do.Timers` instance used for trailing-edge dispatch.
    timer_id:
        Optional explicit key for the internal timer entry.
    leading:
        If ``True`` (default) the first call within an idle window fires
        immediately.  Set to ``False`` for trailing-edge-only behaviour.
    """

    def __init__(
        self,
        interval_ms: int,
        callback: Callable,
        timers,
        *,
        timer_id: Optional[Hashable] = None,
        leading: bool = True,
    ) -> None:
        if interval_ms <= 0:
            raise ValueError("interval_ms must be > 0")
        if not callable(callback):
            raise ValueError("callback must be callable")
        self._interval_s: float = int(interval_ms) / 1000.0
        self._callback: Callable = callback
        self._timers = timers
        self._timer_id: Hashable = timer_id if timer_id is not None else object()
        self._leading: bool = bool(leading)
        self._locked: bool = False        # True while within the throttle interval
        self._queued_args: Optional[Tuple] = None
        self._queued_kwargs: Optional[dict] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def call(self, *args: Any, **kwargs: Any) -> None:
        """Trigger the throttle with *args* and *kwargs*.

        If not currently within a throttle window (or ``leading=True`` on first
        call), the callback fires immediately and a trailing window opens.
        Otherwise the call is buffered as the trailing-edge call.
        """
        if not self._locked:
            self._locked = True
            if self._leading:
                self._callback(*args, **kwargs)
            else:
                self._queued_args = args
                self._queued_kwargs = kwargs
            # Schedule trailing-edge dispatch
            self._timers.add_once(self._timer_id, self._interval_s, self._on_interval_end)
        else:
            # Buffer as most-recent queued call
            self._queued_args = args
            self._queued_kwargs = kwargs

    def cancel(self) -> None:
        """Cancel any pending trailing-edge call and reset the throttle window."""
        self._timers.remove_timer(self._timer_id)
        self._locked = False
        self._queued_args = None
        self._queued_kwargs = None

    @property
    def is_locked(self) -> bool:
        """Return True while within the throttle interval (i.e. calls are buffered)."""
        return self._locked

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_interval_end(self) -> None:
        self._locked = False
        if self._queued_args is not None:
            args = self._queued_args
            kwargs = self._queued_kwargs or {}
            self._queued_args = None
            self._queued_kwargs = None
            # Fire trailing-edge call (re-enters throttle window)
            self.call(*args, **kwargs)
