"""TweenManager — frame-driven property interpolation with easing."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Optional, Union


EasingFn = Callable[[float], float]


class Easing(Enum):
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"


def _ease_linear(t: float) -> float:
    return t


def _ease_in(t: float) -> float:
    return t * t


def _ease_out(t: float) -> float:
    return t * (2.0 - t)


def _ease_in_out(t: float) -> float:
    return 3.0 * t * t - 2.0 * t * t * t


_EASING_MAP = {
    Easing.LINEAR: _ease_linear,
    Easing.EASE_IN: _ease_in,
    Easing.EASE_OUT: _ease_out,
    Easing.EASE_IN_OUT: _ease_in_out,
    "linear": _ease_linear,
    "ease_in": _ease_in,
    "ease_out": _ease_out,
    "ease_in_out": _ease_in_out,
}


def resolve_easing(easing: Union[str, Easing, EasingFn]) -> EasingFn:
    """Return the easing function for a name, Easing member, or callable."""
    if callable(easing):
        return easing
    fn = _EASING_MAP.get(easing)
    if fn is None:
        raise ValueError(f"Unknown easing: {easing!r}")
    return fn


def _lerp_float(start: float, end: float, t: float) -> float:
    return start + (end - start) * t


def _lerp_tuple(start: tuple, end: tuple, t: float) -> tuple:
    return tuple(s + (e - s) * t for s, e in zip(start, end))


class TweenHandle:
    """Handle for a running tween that allows cancellation and progress queries."""

    def __init__(self, tween_id: int, manager: "TweenManager") -> None:
        self._tween_id = tween_id
        self._manager = manager

    @property
    def tween_id(self) -> int:
        return self._tween_id

    @property
    def is_complete(self) -> bool:
        entry = self._manager._get_entry(self._tween_id)
        return entry is None or entry.complete

    @property
    def is_cancelled(self) -> bool:
        entry = self._manager._get_entry(self._tween_id)
        return entry is None or entry.cancelled

    def cancel(self) -> None:
        self._manager.cancel(self)

    def elapsed_fraction(self) -> float:
        """Return progress as normalized 0.0..1.0 value."""
        entry = self._manager._get_entry(self._tween_id)
        if entry is None:
            return 1.0
        if entry.duration <= 0.0:
            return 1.0
        return min(entry.elapsed / entry.duration, 1.0)


@dataclass
class _TweenEntry:
    tween_id: int
    duration: float
    fn: Callable[[float], None]
    easing_fn: EasingFn
    on_complete: Optional[Callable[[], None]]
    tag: Optional[str]
    elapsed: float = 0.0
    complete: bool = False
    cancelled: bool = False


class TweenManager:
    """Frame-driven property interpolation manager. One instance per scene."""

    def __init__(self) -> None:
        self._entries: List[_TweenEntry] = []
        self._next_id: int = 1

    def tween_fn(
        self,
        duration_seconds: float,
        fn: Callable[[float], None],
        *,
        easing: Union[str, Easing, EasingFn] = Easing.EASE_IN_OUT,
        on_complete: Optional[Callable[[], None]] = None,
        tag: Optional[str] = None,
    ) -> TweenHandle:
        """Core primitive: calls fn(eased_t) each frame until duration elapses."""
        tween_id = self._next_id
        self._next_id += 1
        duration = max(0.0, float(duration_seconds))
        easing_fn = resolve_easing(easing)
        entry = _TweenEntry(
            tween_id=tween_id,
            duration=duration,
            fn=fn,
            easing_fn=easing_fn,
            on_complete=on_complete,
            tag=tag,
        )
        # Zero-duration tweens complete immediately on first update
        if duration <= 0.0:
            try:
                fn(1.0)
            except Exception:
                pass
            entry.complete = True
            if on_complete is not None:
                try:
                    on_complete()
                except Exception:
                    pass
        self._entries.append(entry)
        return TweenHandle(tween_id, self)

    def tween(
        self,
        target: object,
        attr: str,
        end_value: Any,
        duration_seconds: float,
        *,
        easing: Union[str, Easing, EasingFn] = Easing.EASE_IN_OUT,
        on_complete: Optional[Callable[[], None]] = None,
        tag: Optional[str] = None,
    ) -> TweenHandle:
        """Animate target.attr from its current value to end_value."""
        start_value = getattr(target, attr)
        is_tuple = isinstance(start_value, tuple) or isinstance(end_value, tuple)

        def _apply(t: float) -> None:
            if is_tuple:
                sv = start_value if not isinstance(start_value, tuple) else start_value
                ev = end_value if isinstance(end_value, tuple) else end_value
                sv_t = sv if isinstance(sv, tuple) else (sv,) * len(ev)
                ev_t = ev if isinstance(ev, tuple) else (ev,) * len(sv_t)
                setattr(target, attr, _lerp_tuple(sv_t, ev_t, t))
            else:
                setattr(target, attr, _lerp_float(float(start_value), float(end_value), t))

        return self.tween_fn(
            duration_seconds,
            _apply,
            easing=easing,
            on_complete=on_complete,
            tag=tag,
        )

    def cancel(self, handle: TweenHandle) -> bool:
        """Cancel a specific tween. Returns True if it was active."""
        entry = self._get_entry(handle.tween_id)
        if entry is None or entry.complete or entry.cancelled:
            return False
        entry.cancelled = True
        return True

    def cancel_all_for_tag(self, tag: str) -> int:
        """Cancel all tweens with the given tag. Returns count cancelled."""
        count = 0
        for entry in self._entries:
            if entry.tag == tag and not entry.complete and not entry.cancelled:
                entry.cancelled = True
                count += 1
        return count

    def cancel_all(self) -> int:
        """Cancel all active tweens. Returns count cancelled."""
        count = 0
        for entry in self._entries:
            if not entry.complete and not entry.cancelled:
                entry.cancelled = True
                count += 1
        return count

    @property
    def active_count(self) -> int:
        """Return count of tweens currently running (not complete, not cancelled)."""
        return sum(1 for e in self._entries if not e.complete and not e.cancelled)

    def update(self, dt_seconds: float) -> None:
        """Advance all active tweens. Called from GuiApplication.update()."""
        dt = max(0.0, float(dt_seconds))
        completed_ids = []
        for entry in self._entries:
            if entry.complete or entry.cancelled:
                continue
            entry.elapsed += dt
            if entry.duration <= 0.0:
                t = 1.0
            else:
                t = min(entry.elapsed / entry.duration, 1.0)
            eased_t = entry.easing_fn(t)
            try:
                entry.fn(eased_t)
            except Exception:
                pass
            if t >= 1.0:
                entry.complete = True
                completed_ids.append(entry.tween_id)
                if entry.on_complete is not None:
                    try:
                        entry.on_complete()
                    except Exception:
                        pass
        # Remove finished entries to keep memory bounded
        if completed_ids or any(e.cancelled for e in self._entries):
            self._entries = [e for e in self._entries if not (e.complete or e.cancelled)]

    def _get_entry(self, tween_id: int) -> Optional[_TweenEntry]:
        for entry in self._entries:
            if entry.tween_id == tween_id:
                return entry
        return None
