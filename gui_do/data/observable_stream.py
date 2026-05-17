"""ObservableStream — composable reactive stream operators.

Wraps any :class:`~gui_do.ObservableValue`, :class:`~gui_do.Signal` instance,
or callable subscription source and provides operator chaining so that
multi-step reactive pipelines can be expressed declaratively without building
intermediate callbacks and tracking unsub callables manually.

Usage::

    from gui_do import ObservableStream, ObservableValue

    speed = ObservableValue(0.0)

    # Build a pipeline:
    stream = (
        ObservableStream(speed)
        .distinct_until_changed()
        .filter(lambda v: v > 0)
        .map(lambda v: round(v, 1))
    )

    unsub = stream.subscribe(lambda v: label.__setattr__("text", f"{v} m/s"))
    # Later:
    unsub()

Sources
-------
Accepted source types:

- :class:`~gui_do.ObservableValue` — subscribes via ``.subscribe(cb)``
  returning an unsub callable.
- Any object with a ``.subscribe(cb) -> unsub`` method (same contract).
- A raw callable ``subscribe_fn(cb) -> unsub`` for ad-hoc integration.

Operators
---------
Every operator returns a new :class:`ObservableStream` that does not activate
until :meth:`subscribe` is called.  Operators are **lazy**: building a chain
allocates only descriptors; no callbacks are wired until subscription.

- :meth:`map` — transform emitted values.
- :meth:`filter` — suppress values that fail the predicate.
- :meth:`distinct_until_changed` — skip emissions equal to the previous value.
- :meth:`debounce` — emit only after *ms* milliseconds of silence (requires
  ``timers`` arg at subscription, see below).
- :meth:`throttle` — emit at most once per *ms* milliseconds.
- :meth:`merge` — combine with other streams; emit from whichever fires.
- :meth:`zip` — emit only when all merged streams have a pending new value.
- :meth:`take_until` — unsubscribe automatically on first emission from a
  stop-signal stream.
- :meth:`take` — unsubscribe after emitting *n* values.
- :meth:`pairwise` — emit ``(previous, current)`` tuples.

Thread safety
-------------
:class:`ObservableStream` is not thread-safe.  All source updates must be
delivered on the frame thread (the pygame main thread).
"""
from __future__ import annotations

import time
from collections import deque
from typing import Any, Callable, Generic, TypeVar


T = TypeVar("T")
U = TypeVar("U")

# A subscribe function has signature (callback) -> unsub_callable
SubscribeFn = Callable[[Callable[[Any], None]], Callable[[], None]]

_SENTINEL = object()


def _make_subscribe_fn(source: Any) -> SubscribeFn:
    """Return a canonical subscribe(cb) -> unsub function from *source*."""
    if callable(getattr(source, "subscribe", None)):
        return source.subscribe
    if callable(source):
        return source
    raise TypeError(
        f"ObservableStream source must have a .subscribe(cb)->unsub method "
        f"or be a callable subscribe function; got {type(source)!r}"
    )


class ObservableStream(Generic[T]):
    """Composable lazy reactive stream.

    Parameters
    ----------
    source:
        An :class:`~gui_do.ObservableValue`, :class:`~gui_do.Signal` instance,
        or any object whose ``.subscribe(cb)`` returns an unsub callable.
    """

    def __init__(self, source: Any) -> None:
        self._subscribe_fn: SubscribeFn = _make_subscribe_fn(source)

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, callback: Callable[[T], None]) -> Callable[[], None]:
        """Activate the pipeline and call *callback* for each emitted value.

        Returns an unsub callable that tears down the entire pipeline when
        called.
        """
        return self._subscribe_fn(callback)

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def map(self, fn: Callable[[T], U]) -> "ObservableStream[U]":
        """Transform each emitted value through *fn*."""
        parent = self

        def _subscribe(cb: Callable[[U], None]) -> Callable[[], None]:
            return parent.subscribe(lambda v: cb(fn(v)))

        return ObservableStream(_subscribe)

    def filter(self, predicate: Callable[[T], bool]) -> "ObservableStream[T]":
        """Suppress values for which *predicate* returns False."""
        parent = self

        def _subscribe(cb: Callable[[T], None]) -> Callable[[], None]:
            def _on_value(v: T) -> None:
                if predicate(v):
                    cb(v)

            return parent.subscribe(_on_value)

        return ObservableStream(_subscribe)

    def distinct_until_changed(self) -> "ObservableStream[T]":
        """Skip emissions equal to the immediately previous value."""
        parent = self

        def _subscribe(cb: Callable[[T], None]) -> Callable[[], None]:
            prev = [_SENTINEL]

            def _on_value(v: T) -> None:
                if prev[0] is _SENTINEL or v != prev[0]:
                    prev[0] = v
                    cb(v)

            return parent.subscribe(_on_value)

        return ObservableStream(_subscribe)

    def debounce(self, ms: float) -> "ObservableStream[T]":
        """Emit only after *ms* milliseconds of silence.

        Uses :func:`time.monotonic` for portable timing (no OS timer APIs).
        The debounced value is emitted the next time :meth:`subscribe`'s
        consumer calls its own update path — this operator stores a pending
        value and fires via a lightweight poll mechanism.  For frame-rate
        contexts, subscribers should call ``stream.tick(dt_ms)`` each frame.

        .. note::
            For precise frame-rate integration, use :meth:`debounce_ticked`
            with the scene timer.  This method is suitable for coarse
            time-based suppression.
        """
        parent = self
        delay_s = ms / 1000.0

        def _subscribe(cb: Callable[[T], None]) -> Callable[[], None]:
            pending: list = [_SENTINEL]
            deadline: list = [0.0]

            def _on_value(v: T) -> None:
                pending[0] = v
                deadline[0] = time.monotonic() + delay_s

            def _tick() -> None:
                if pending[0] is not _SENTINEL and time.monotonic() >= deadline[0]:
                    val = pending[0]
                    pending[0] = _SENTINEL
                    cb(val)

            # Attach tick helper to the returned unsub so callers can drive it
            unsub = parent.subscribe(_on_value)

            class _Unsub:
                def __call__(self) -> None:
                    unsub()

                def tick(self) -> None:
                    _tick()

            return _Unsub()

        return ObservableStream(_subscribe)

    def throttle(self, ms: float) -> "ObservableStream[T]":
        """Emit at most once per *ms* milliseconds; discard intervening values."""
        parent = self
        interval_s = ms / 1000.0

        def _subscribe(cb: Callable[[T], None]) -> Callable[[], None]:
            last_fire: list = [0.0]

            def _on_value(v: T) -> None:
                now = time.monotonic()
                if now - last_fire[0] >= interval_s:
                    last_fire[0] = now
                    cb(v)

            return parent.subscribe(_on_value)

        return ObservableStream(_subscribe)

    def merge(self, *others: "ObservableStream[Any]") -> "ObservableStream[Any]":
        """Emit from this stream or any of *others*; whichever fires first."""
        parent = self

        def _subscribe(cb: Callable[[Any], None]) -> Callable[[], None]:
            unsubs = [parent.subscribe(cb)]
            for other in others:
                unsubs.append(other.subscribe(cb))

            def _unsub() -> None:
                for u in unsubs:
                    u()

            return _unsub

        return ObservableStream(_subscribe)

    def zip(self, *others: "ObservableStream[Any]") -> "ObservableStream[Tuple]":
        """Emit a tuple only when all streams have each produced a new value."""
        parent = self
        all_streams = [parent] + list(others)
        n = len(all_streams)

        def _subscribe(cb: Callable[[Tuple], None]) -> Callable[[], None]:
            buffers: list = [deque() for _ in range(n)]
            unsubs: list = []

            def _make_handler(idx: int) -> Callable:
                def _on_value(v: Any) -> None:
                    buffers[idx].append(v)
                    if all(len(b) > 0 for b in buffers):
                        args = tuple(b.popleft() for b in buffers)
                        cb(args)

                return _on_value

            for i, stream in enumerate(all_streams):
                unsubs.append(stream.subscribe(_make_handler(i)))

            def _unsub() -> None:
                for u in unsubs:
                    u()

            return _unsub

        return ObservableStream(_subscribe)

    def take_until(self, stop_stream: "ObservableStream[Any]") -> "ObservableStream[T]":
        """Unsubscribe automatically on the first emission from *stop_stream*."""
        parent = self

        def _subscribe(cb: Callable[[T], None]) -> Callable[[], None]:
            unsub_main: list = [None]
            unsub_stop: list = [None]

            def _teardown() -> None:
                if unsub_main[0] is not None:
                    unsub_main[0]()
                    unsub_main[0] = None
                if unsub_stop[0] is not None:
                    unsub_stop[0]()
                    unsub_stop[0] = None

            unsub_main[0] = parent.subscribe(cb)
            unsub_stop[0] = stop_stream.subscribe(lambda _: _teardown())
            return _teardown

        return ObservableStream(_subscribe)

    def take(self, n: int) -> "ObservableStream[T]":
        """Unsubscribe after emitting *n* values."""
        parent = self

        def _subscribe(cb: Callable[[T], None]) -> Callable[[], None]:
            count = [0]
            unsub: list = [None]

            def _on_value(v: T) -> None:
                if count[0] < n:
                    count[0] += 1
                    cb(v)
                    if count[0] >= n and unsub[0] is not None:
                        unsub[0]()
                        unsub[0] = None

            unsub[0] = parent.subscribe(_on_value)
            return lambda: unsub[0]() if unsub[0] is not None else None

        return ObservableStream(_subscribe)

    def pairwise(self) -> "ObservableStream[Tuple[T, T]]":
        """Emit ``(previous, current)`` tuples; skips the very first emission."""
        parent = self

        def _subscribe(cb: Callable[[Tuple[T, T]], None]) -> Callable[[], None]:
            prev = [_SENTINEL]

            def _on_value(v: T) -> None:
                if prev[0] is not _SENTINEL:
                    cb((prev[0], v))
                prev[0] = v

            return parent.subscribe(_on_value)

        return ObservableStream(_subscribe)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_observable(cls, observable: Any) -> "ObservableStream":
        """Create a stream from any object with a ``.subscribe(cb)->unsub`` method."""
        return cls(observable)

    @classmethod
    def of(cls, *values: T) -> "ObservableStream[T]":
        """Create a stream that emits the given values synchronously on subscribe."""
        def _subscribe(cb: Callable[[T], None]) -> Callable[[], None]:
            for v in values:
                cb(v)
            return lambda: None

        return cls(_subscribe)
