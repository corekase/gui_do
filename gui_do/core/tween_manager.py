"""TweenManager — frame-driven property interpolation with easing."""
from __future__ import annotations

from dataclasses import dataclass
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
        self._entry_by_id: dict[int, _TweenEntry] = {}
        self._next_id: int = 1
        self._has_cancelled: bool = False

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
        self._entry_by_id[tween_id] = entry
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
        start_is_tuple = isinstance(start_value, tuple)
        end_is_tuple = isinstance(end_value, tuple)

        if start_is_tuple or end_is_tuple:
            # Pre-compute canonical tuple operands once; avoids per-frame isinstance.
            if start_is_tuple and end_is_tuple:
                sv_t: tuple = start_value
                ev_t: tuple = end_value
            elif end_is_tuple:
                sv_t = (start_value,) * len(end_value)
                ev_t = end_value
            else:
                sv_t = start_value
                ev_t = (end_value,) * len(start_value)

            def _apply_tuple(t: float) -> None:
                setattr(target, attr, _lerp_tuple(sv_t, ev_t, t))

            _apply = _apply_tuple
        else:
            start_f = float(start_value)
            end_f = float(end_value)

            def _apply_float(t: float) -> None:
                setattr(target, attr, _lerp_float(start_f, end_f, t))

            _apply = _apply_float

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
        self._has_cancelled = True
        return True

    def cancel_all_for_tag(self, tag: str) -> int:
        """Cancel all tweens with the given tag. Returns count cancelled."""
        count = 0
        for entry in self._entries:
            if entry.tag == tag and not entry.complete and not entry.cancelled:
                entry.cancelled = True
                count += 1
        if count:
            self._has_cancelled = True
        return count

    def cancel_all(self) -> int:
        """Cancel all active tweens. Returns count cancelled."""
        count = 0
        for entry in self._entries:
            if not entry.complete and not entry.cancelled:
                entry.cancelled = True
                count += 1
        if count:
            self._has_cancelled = True
        return count

    @property
    def active_count(self) -> int:
        """Return count of tweens currently running (not complete, not cancelled)."""
        return sum(1 for e in self._entries if not e.complete and not e.cancelled)

    def update(self, dt_seconds: float) -> None:
        """Advance all active tweens. Called from GuiApplication.update()."""
        if not self._entries:
            return
        dt = max(0.0, float(dt_seconds))
        had_completions = False
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
                had_completions = True
                if entry.on_complete is not None:
                    try:
                        entry.on_complete()
                    except Exception:
                        pass
        # Remove finished entries to keep memory bounded
        if had_completions or self._has_cancelled:
            self._has_cancelled = False
            self._entries = [e for e in self._entries if not (e.complete or e.cancelled)]
            self._entry_by_id = {e.tween_id: e for e in self._entries}

    def _get_entry(self, tween_id: int) -> Optional[_TweenEntry]:
        return self._entry_by_id.get(tween_id)
