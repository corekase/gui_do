"""SceneTimeline — frame-driven scene choreography timeline.

Schedules callbacks at precise time offsets, fires looping events at regular
intervals, and supports labeled seek points and duration-spanning region
callbacks (enter/exit).  All time tracking is frame-driven: call
:meth:`update` once per frame with the elapsed delta and the timeline advances
deterministically.  No OS timer APIs are used.

Usage::

    from gui_do import SceneTimeline

    timeline = SceneTimeline()

    # Point-in-time events:
    timeline.at(0.0,  lambda: spawn_title())
    timeline.at(1.5,  lambda: fade_in_logo())
    timeline.at(4.0,  lambda: start_music())
    timeline.after(5.0, lambda: show_menu())  # relative to play() start

    # Duration-spanning region:
    timeline.between(1.5, 4.0, on_enter=show_logo, on_exit=hide_logo)

    # Looping:
    timeline.loop_every(0.5, lambda: blink_cursor())

    # Seek labels:
    timeline.label("intro_end", t=4.0)
    timeline.seek_to_label("intro_end")

    # Play / pause:
    timeline.play()

    def update(dt):
        timeline.update(dt)

    # Explicit seek:
    timeline.seek(2.0)

    # Completion:
    timeline.on_complete(lambda: show_end_screen())
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple


_Callback = Callable[[], None]


class SceneTimeline:
    """Frame-driven scene choreography timeline.

    Parameters
    ----------
    duration:
        Explicit total duration in seconds.  When ``None`` (default) the
        duration is auto-computed as the furthest :meth:`at` time plus any
        pending offsets.
    """

    def __init__(self, *, duration: Optional[float] = None) -> None:
        # --- point events: (time, callback) ---
        self._events: List[Tuple[float, _Callback]] = []
        # --- loops: (interval, callback, next_trigger) ---
        self._loops: List[Dict] = []
        # --- regions: (t_start, t_end, on_enter, on_exit, active) ---
        self._regions: List[Dict] = []
        # --- labels: name → time ---
        self._labels: Dict[str, float] = {}
        # --- completion ---
        self._complete_cbs: List[_Callback] = []
        # --- state ---
        self._t: float = 0.0
        self._playing: bool = False
        self._explicit_duration: Optional[float] = duration
        # Track which events have fired in the current play-through
        self._fired: set = set()   # indices into _events
        # --- after() support: relative offset resolved on play() ---
        self._after_events: List[Tuple[float, _Callback]] = []
        self._play_start_extra_events_added: bool = False

    # ------------------------------------------------------------------
    # Event registration
    # ------------------------------------------------------------------

    def at(self, t_seconds: float, callback: _Callback) -> "SceneTimeline":
        """Fire *callback* when :attr:`current_time` reaches *t_seconds*."""
        self._events.append((max(0.0, float(t_seconds)), callback))
        self._events.sort(key=lambda e: e[0])
        return self

    def after(self, delay: float, callback: _Callback) -> "SceneTimeline":
        """Fire *callback delay* seconds after :meth:`play` is called.

        Unlike :meth:`at`, :meth:`after` offsets are resolved to absolute
        time when :meth:`play` is first called.  Calling :meth:`after` before
        :meth:`play` always fires at ``play_start_time + delay``.
        """
        self._after_events.append((max(0.0, float(delay)), callback))
        return self

    def between(
        self,
        t_start: float,
        t_end: float,
        *,
        on_enter: _Callback,
        on_exit: Optional[_Callback] = None,
    ) -> "SceneTimeline":
        """Fire *on_enter* when time enters [t_start, t_end) and *on_exit* when leaving."""
        self._regions.append({
            "t_start": max(0.0, float(t_start)),
            "t_end": max(0.0, float(t_end)),
            "on_enter": on_enter,
            "on_exit": on_exit,
            "active": False,
        })
        return self

    def loop_every(self, interval: float, callback: _Callback) -> "SceneTimeline":
        """Fire *callback* repeatedly every *interval* seconds while playing."""
        self._loops.append({
            "interval": max(1e-6, float(interval)),
            "callback": callback,
            "next": float(interval),
        })
        return self

    def label(self, name: str, *, t: Optional[float] = None) -> "SceneTimeline":
        """Register a named seek label at *t* seconds (or current time if ``None``)."""
        self._labels[name] = float(t) if t is not None else self._t
        return self

    def on_complete(self, callback: _Callback) -> "SceneTimeline":
        """Register *callback* to be fired when the timeline completes."""
        self._complete_cbs.append(callback)
        return self

    # ------------------------------------------------------------------
    # Playback control
    # ------------------------------------------------------------------

    def play(self) -> None:
        """Start or resume playback."""
        if not self._playing:
            if not self._play_start_extra_events_added and self._after_events:
                for delay, cb in self._after_events:
                    self._events.append((self._t + delay, cb))
                self._events.sort(key=lambda e: e[0])
                self._play_start_extra_events_added = True
            self._playing = True

    def pause(self) -> None:
        """Pause playback without resetting time."""
        self._playing = False

    def reset(self) -> None:
        """Reset to time 0 and clear fired-event state."""
        self._t = 0.0
        self._playing = False
        self._fired.clear()
        self._play_start_extra_events_added = False
        # Reset loops
        for loop in self._loops:
            loop["next"] = loop["interval"]
        # Deactivate all regions
        for region in self._regions:
            region["active"] = False

    def seek(self, t_seconds: float) -> None:
        """Jump to *t_seconds*.  Events between old and new time are fired.
        Events before old time (backward seek) have their fired-state reset."""
        new_t = max(0.0, float(t_seconds))
        if new_t > self._t:
            self._advance(new_t - self._t)
        else:
            # Backward seek — reset fired state for events after new_t
            self._t = new_t
            self._fired = {i for i, (t, _) in enumerate(self._events) if t <= new_t}
            self._fire_regions(new_t)

    def seek_to_label(self, name: str) -> None:
        """Seek to the time registered under *name*."""
        self.seek(self._labels[name])

    # ------------------------------------------------------------------
    # Frame update
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float) -> None:
        """Advance the timeline by *dt_seconds*.  Call once per frame."""
        if not self._playing:
            return
        self._advance(dt_seconds)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def current_time(self) -> float:
        return self._t

    @property
    def duration(self) -> float:
        """Total timeline duration in seconds."""
        if self._explicit_duration is not None:
            return self._explicit_duration
        if not self._events:
            return 0.0
        return max(t for t, _ in self._events)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _advance(self, dt: float) -> None:
        prev_t = self._t
        new_t = self._t + dt

        # Check duration limit
        dur = self.duration
        if dur > 0 and new_t >= dur:
            new_t = dur
            self._t = new_t
            self._fire_events_in_range(prev_t, new_t)
            self._fire_loops(prev_t, new_t)
            self._fire_regions(new_t)
            self._playing = False
            for cb in self._complete_cbs:
                try:
                    cb()
                except Exception:
                    pass
            return

        self._t = new_t
        self._fire_events_in_range(prev_t, new_t)
        self._fire_loops(prev_t, new_t)
        self._fire_regions(new_t)

    def _fire_events_in_range(self, prev_t: float, new_t: float) -> None:
        for i, (t, cb) in enumerate(self._events):
            if i in self._fired:
                continue
            if prev_t < t <= new_t:
                self._fired.add(i)
                try:
                    cb()
                except Exception:
                    pass

    def _fire_loops(self, prev_t: float, new_t: float) -> None:
        for loop in self._loops:
            while loop["next"] <= new_t:
                try:
                    loop["callback"]()
                except Exception:
                    pass
                loop["next"] += loop["interval"]

    def _fire_regions(self, current_t: float) -> None:
        for region in self._regions:
            inside = region["t_start"] <= current_t < region["t_end"]
            if inside and not region["active"]:
                region["active"] = True
                try:
                    region["on_enter"]()
                except Exception:
                    pass
            elif not inside and region["active"]:
                region["active"] = False
                if region["on_exit"] is not None:
                    try:
                        region["on_exit"]()
                    except Exception:
                        pass
