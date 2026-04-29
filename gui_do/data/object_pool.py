"""ObjectPool[T] — typed thread-safe object recycler.

Reduces garbage-collector pressure in hot allocation paths by recycling
previously used objects.  Call :meth:`acquire` to get a (possibly recycled)
instance and :meth:`release` to return it.

If a *reset* callable is supplied it is called on every released object before
the object is returned to the pool, clearing transient state.  If the pool is
full (``max_size`` reached) released objects are simply discarded.

The internal queue is guarded by a :class:`threading.Lock` so the pool can
safely be shared between background workers (e.g. :class:`~gui_do.AsyncDataProvider`
task threads) and the main frame thread.

Usage::

    from gui_do import ObjectPool

    def _make_event():
        return GuiEvent.__new__(GuiEvent)

    def _reset_event(e):
        e.kind = None
        e.pos = (0, 0)

    pool = ObjectPool(_make_event, reset=_reset_event, max_size=64)
    pool.preallocate(16)

    # Acquire an instance:
    evt = pool.acquire()
    # …fill evt fields…

    # Return it:
    pool.release(evt)

    # Diagnostics:
    stats = pool.stats()
    # → {"size": 15, "hits": 1, "misses": 0, "discards": 0}
"""
from __future__ import annotations

import threading
from typing import Callable, Generic, Optional, TypeVar


T = TypeVar("T")


class ObjectPool(Generic[T]):
    """Typed, thread-safe object recycler.

    Parameters
    ----------
    factory:
        Zero-argument callable that creates a new instance when the pool is
        empty.
    reset:
        Optional callable ``(obj) -> None`` invoked on release to clear
        transient state before the object re-enters the pool.
    max_size:
        Maximum number of objects held in the pool at once.  Surplus releases
        are discarded.  Default is 128.
    """

    def __init__(
        self,
        factory: Callable[[], T],
        *,
        reset: Optional[Callable[[T], None]] = None,
        max_size: int = 128,
    ) -> None:
        self._factory = factory
        self._reset = reset
        self._max_size = max(1, int(max_size))
        self._pool: list = []
        self._lock = threading.Lock()
        self._hits: int = 0
        self._misses: int = 0
        self._discards: int = 0

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def acquire(self) -> T:
        """Return a recycled instance or a freshly created one.

        Thread-safe.
        """
        with self._lock:
            if self._pool:
                self._hits += 1
                return self._pool.pop()
        self._misses += 1
        return self._factory()

    def release(self, obj: T) -> None:
        """Return *obj* to the pool for future reuse.

        Thread-safe.  If the pool is at capacity the object is discarded.
        """
        if self._reset is not None:
            self._reset(obj)
        with self._lock:
            if len(self._pool) < self._max_size:
                self._pool.append(obj)
            else:
                self._discards += 1

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def preallocate(self, count: int) -> None:
        """Warm the pool by pre-creating *count* objects.

        Up to ``max_size`` objects are created; extras are silently ignored.
        """
        with self._lock:
            needed = min(int(count), self._max_size - len(self._pool))
        for _ in range(needed):
            obj = self._factory()
            self.release(obj)

    def clear(self) -> None:
        """Discard all pooled objects."""
        with self._lock:
            self._pool.clear()

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return a snapshot of pool statistics.

        Returns
        -------
        dict with keys:
            ``size`` — current number of pooled objects,
            ``max_size`` — configured maximum pool size,
            ``hits`` — number of successful :meth:`acquire` recycles,
            ``misses`` — number of :meth:`acquire` calls that created new objects,
            ``discards`` — number of :meth:`release` calls that discarded objects
            because the pool was full.
        """
        with self._lock:
            size = len(self._pool)
        return {
            "size": size,
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "discards": self._discards,
        }

    @property
    def max_size(self) -> int:
        """Configured maximum pool size."""
        return self._max_size
