"""reactive_batch — deferred notification batching for ObservableValue.

Wraps multiple :class:`~gui_do.ObservableValue` mutations inside a single
:func:`reactive_batch` context manager so observers are notified **once** at
the context exit rather than once per individual assignment.

Nested batch contexts are supported.  Observers are fired only when the
outermost ``reactive_batch`` block exits.  Re-entrant notifications triggered
during the flush phase are handled safely: they are queued and flushed in the
same pass.

Usage::

    from gui_do import reactive_batch

    a = ObservableValue(0)
    b = ObservableValue(0)

    def on_change(_): ...

    a.subscribe(on_change)
    b.subscribe(on_change)

    # Without batch: on_change fires twice.
    # With batch: on_change fires once per observable, at block exit.
    with reactive_batch():
        a.value = 1
        b.value = 2
    # on_change("a") and on_change("b") each called once here

ObservableList bulk replacement::

    from gui_do import reactive_batch
    obs_list.batch_replace(new_items)   # single RESET change notification

Async-compatible usage::

    # Works fine in frame-thread-only code; not thread-safe by design.
    with reactive_batch():
        for field in form.fields:
            field.value.value = loaded_data[field.name]
"""
from __future__ import annotations

import contextlib
from typing import Generator


# ---------------------------------------------------------------------------
# Module-level batch state (main-thread only, non-reentrant across threads)
# ---------------------------------------------------------------------------

_batch_depth: int = 0
# Maps id(observable) -> observable to deduplicate pending notifications.
# Ordered insertion preserves the mutation order for predictable flush sequence.
_pending: dict = {}


def is_batching() -> bool:
    """Return ``True`` if a :func:`reactive_batch` context is currently active."""
    return _batch_depth > 0


def _enqueue(observable: object) -> None:
    """Internal: record *observable* as needing notification at flush time."""
    _pending[id(observable)] = observable


def _flush() -> None:
    """Internal: drain and fire all deferred observer notifications."""
    # Loop to handle re-entrant mutations triggered by observers.
    while _pending:
        # Snapshot and clear before notifying so re-entrant assignments are
        # captured in the next iteration rather than growing the snapshot.
        batch = list(_pending.values())
        _pending.clear()
        for obs in batch:
            obs._notify_observers()  # type: ignore[attr-defined]


@contextlib.contextmanager
def reactive_batch() -> Generator[None, None, None]:
    """Context manager that defers :class:`~gui_do.ObservableValue` notifications.

    All assignments to :attr:`~gui_do.ObservableValue.value` inside this block
    update the stored value immediately but fire observers only at the exit of
    the outermost ``reactive_batch`` scope.  If the value is reassigned
    multiple times in one batch the observers receive one notification with the
    final value.

    Raises
    ------
    Exception
        Any exception raised inside the block propagates normally.  Pending
        notifications are discarded if the block exits via exception to avoid
        notifying observers about values that may be inconsistent.
    """
    global _batch_depth
    _batch_depth += 1
    try:
        yield
        _batch_depth -= 1
        if _batch_depth == 0:
            _flush()
    except Exception:
        _batch_depth -= 1
        if _batch_depth == 0:
            # Discard pending notifications on exception — state may be
            # partially updated and notifying could cause inconsistent renders.
            _pending.clear()
        raise
