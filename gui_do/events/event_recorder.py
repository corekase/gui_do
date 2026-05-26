"""EventRecorder / EventPlayback — record and replay GuiEvent sequences.

:class:`EventRecorder` captures a time-stamped log of UI events.  Recordings
can be saved to a compact JSON file and reloaded for replay or analysis.
:class:`EventPlayback` re-injects recorded events through a user-supplied
handler at the original relative timing, driven by a frame-elapsed accumulator
(no OS timer APIs).

Typical use-cases:

- Integration tests: record a known-good interaction and replay in CI.
- Macros: save a workflow and trigger it on demand.
- Tutorials: prerecorded walkthroughs with pause-points.

Usage::

    from gui_do import EventRecorder, EventPlayback, RecordedEvent

    # Recording:
    recorder = EventRecorder()
    recorder.start()

    # In your event loop, after normalizing events:
    # recorder.record(gui_event)

    events = recorder.stop()

    # Persist:
    recorder.save("my_macro.json")

    # Playback:
    log = EventRecorder.load_file("my_macro.json")
    player = EventPlayback(log, handler=app.process_event_synthetic)
    player.start()

    # Per frame:
    player.update(dt_seconds)

    # Check status:
    if not player.is_playing:
        print("Playback complete")
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Dict, List


# ---------------------------------------------------------------------------
# RecordedEvent
# ---------------------------------------------------------------------------


@dataclass
class RecordedEvent:
    """A single captured event in a recording.

    Attributes
    ----------
    time_offset_ms:
        Milliseconds elapsed since :meth:`EventRecorder.start` was called.
    event_type:
        String name of the event type (e.g. ``"MOUSE_DOWN"``, ``"KEY_DOWN"``).
    pos:
        Screen position ``(x, y)`` for pointer events; ``(0, 0)`` otherwise.
    key:
        Pygame key constant for keyboard events; ``0`` otherwise.
    mod:
        Modifier bitmask for keyboard events; ``0`` otherwise.
    button:
        Mouse button index for mouse events; ``0`` otherwise.
    wheel_delta:
        Scroll wheel delta for wheel events; ``0`` otherwise.
    text:
        Text for ``TEXT_INPUT`` events; ``""`` otherwise.
    extra:
        Optional dict for application-specific payload.
    """

    time_offset_ms: float
    event_type: str
    pos: List[int] = field(default_factory=lambda: [0, 0])
    key: int = 0
    mod: int = 0
    button: int = 0
    wheel_delta: int = 0
    text: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# EventRecorder
# ---------------------------------------------------------------------------


class EventRecorder:
    """Records :class:`~gui_do.GuiEvent` sequences for later replay.

    Call :meth:`start` before the interaction, :meth:`record` for each event,
    then :meth:`stop` to finish and retrieve the :class:`RecordedEvent` list.
    """

    def __init__(self) -> None:
        self._recording: bool = False
        self._start_time: float = 0.0
        self._events: List[RecordedEvent] = []

    @property
    def is_recording(self) -> bool:
        """``True`` between :meth:`start` and :meth:`stop`."""
        return self._recording

    @property
    def recorded_count(self) -> int:
        """Number of events captured in the current or last recording."""
        return len(self._events)

    def start(self) -> None:
        """Begin a new recording session.  Discards any previous recording."""
        self._events.clear()
        self._start_time = time.perf_counter()
        self._recording = True

    def stop(self) -> List[RecordedEvent]:
        """End the recording and return the captured events."""
        self._recording = False
        return list(self._events)

    def record(self, event: Any) -> None:
        """Capture *event* if recording is active.

        *event* may be a :class:`~gui_do.GuiEvent` or any object with the
        common attributes (``kind``, ``pos``, ``key``, ``mod``, ``button``).
        Unrecognised attributes are silently defaulted.
        """
        if not self._recording:
            return
        offset_ms = (time.perf_counter() - self._start_time) * 1000.0
        kind = getattr(event, "kind", None)
        event_type = kind.value if hasattr(kind, "value") else str(kind) if kind else "UNKNOWN"
        pos = list(getattr(event, "pos", [0, 0]) or [0, 0])
        rec = RecordedEvent(
            time_offset_ms=round(offset_ms, 2),
            event_type=event_type,
            pos=pos[:2] if len(pos) >= 2 else [0, 0],
            key=int(getattr(event, "key", 0) or 0),
            mod=int(getattr(event, "mod", 0) or 0),
            button=int(getattr(event, "button", 0) or 0),
            wheel_delta=int(getattr(event, "wheel_delta", 0) or 0),
            text=str(getattr(event, "text", "") or ""),
        )
        self._events.append(rec)

    def save(self, path: "str | Path") -> None:
        """Persist the current recording to a JSON file."""
        data = [asdict(e) for e in self._events]
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    @staticmethod
    def load_file(path: "str | Path") -> List[RecordedEvent]:
        """Load a previously saved recording from *path*.

        Returns an empty list if the file does not exist.
        """
        p = Path(path)
        if not p.exists():
            return []
        raw = json.loads(p.read_text(encoding="utf-8"))
        return [RecordedEvent(**entry) for entry in raw]

    @staticmethod
    def from_events(events: List[RecordedEvent]) -> "EventRecorder":
        """Create a recorder pre-populated with *events* (useful for testing)."""
        rec = EventRecorder()
        rec._events = list(events)
        return rec


# ---------------------------------------------------------------------------
# EventPlayback
# ---------------------------------------------------------------------------


class EventPlayback:
    """Replays a :class:`RecordedEvent` sequence through a callback.

    Parameters
    ----------
    events:
        The recorded event sequence (from :meth:`EventRecorder.stop` or
        :meth:`EventRecorder.load_file`).
    handler:
        Callable invoked for each replayed event.  Receives a
        :class:`RecordedEvent` (not a live ``GuiEvent``) so the application
        can reconstruct whatever event object is appropriate.
    loop:
        When ``True`` the sequence restarts from the beginning after the last
        event.
    on_complete:
        Optional callback fired when a non-looping playback finishes.
    """

    def __init__(
        self,
        events: List[RecordedEvent],
        *,
        handler: Callable[[RecordedEvent], None],
        loop: bool = False,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        self._events = sorted(events, key=lambda e: e.time_offset_ms)
        self._handler = handler
        self._loop = bool(loop)
        self._on_complete = on_complete
        self._playing: bool = False
        self._elapsed_ms: float = 0.0
        self._next_index: int = 0

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def elapsed_ms(self) -> float:
        """Milliseconds elapsed since :meth:`start`."""
        return self._elapsed_ms

    @property
    def progress(self) -> float:
        """Fraction of the recording played (0.0 – 1.0).  ``0.0`` when empty."""
        if not self._events:
            return 0.0
        total = self._events[-1].time_offset_ms
        if total <= 0:
            return 1.0
        return min(1.0, self._elapsed_ms / total)

    def start(self) -> None:
        """Begin or restart playback from the first event."""
        self._elapsed_ms = 0.0
        self._next_index = 0
        self._playing = True

    def stop(self) -> None:
        """Halt playback without firing :attr:`on_complete`."""
        self._playing = False

    def update(self, dt_seconds: float) -> None:
        """Advance playback by *dt_seconds*.  Call once per frame."""
        if not self._playing or not self._events:
            return
        self._elapsed_ms += dt_seconds * 1000.0

        while (
            self._next_index < len(self._events)
            and self._events[self._next_index].time_offset_ms <= self._elapsed_ms
        ):
            self._handler(self._events[self._next_index])
            self._next_index += 1

        if self._next_index >= len(self._events):
            if self._loop:
                self._elapsed_ms = 0.0
                self._next_index = 0
            else:
                self._playing = False
                if self._on_complete is not None:
                    self._on_complete()
