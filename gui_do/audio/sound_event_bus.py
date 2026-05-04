"""SoundEventBus — portable pygame.mixer audio cue system.

Maps named semantic sound events (``"button.click"``, ``"dialog.open"``, …)
to audio cues loaded from file, and dispatches them on demand.  The bus
degrades gracefully to a silent no-op when ``pygame.mixer`` is not initialised
or audio hardware is unavailable — so application code never needs to guard
sound calls.

SoundBankRegistry
-----------------
A registry of named :class:`SoundCue` objects loaded from individual files or
bulk-registered from a dict.  Multiple banks can be merged; later
registrations override earlier ones for the same event name.

SoundEventBus
-------------
The runtime dispatcher.  Call :meth:`~SoundEventBus.emit` from any control,
overlay, or feature.  Callers never block — sounds are fired and forgotten.

Usage::

    from gui_do import SoundEventBus, SoundCue, SoundBankRegistry

    # Build a registry from individual files:
    bank = SoundBankRegistry()
    bank.register("button.click",  SoundCue("sounds/click.wav", volume=0.7))
    bank.register("dialog.open",   SoundCue("sounds/whoosh.wav"))
    bank.register("toast.warning", SoundCue("sounds/warning.wav", volume=0.5))

    # Wire into application startup:
    bus = SoundEventBus()
    bus.load_bank(bank)
    bus.set_master_volume(0.8)

    # Inside controls / overlays:
    bus.emit("button.click")
    bus.emit("toast.warning", volume=0.4)   # per-emit volume override

    # Silence specific cues at runtime:
    bus.mute("button.click")
    bus.unmute("button.click")

    # Stop all currently playing sounds:
    bus.stop_all()

    # Query:
    names = bus.registered_event_names()
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional


# ---------------------------------------------------------------------------
# SoundCue
# ---------------------------------------------------------------------------


@dataclass
class SoundCue:
    """Describes a single sound cue entry.

    Parameters
    ----------
    path:
        Filesystem path to the audio file (WAV or OGG recommended for
        cross-platform compatibility).
    volume:
        Default playback volume in ``[0.0, 1.0]``.
    loops:
        Number of additional times to loop after first play.  ``0`` = play
        once, ``-1`` = loop forever until stopped.
    max_time_ms:
        If positive, stop the sound after this many milliseconds.  ``0`` =
        no limit.
    """

    path: str
    volume: float = 1.0
    loops: int = 0
    max_time_ms: int = 0

    def __post_init__(self) -> None:
        self.volume = float(max(0.0, min(1.0, self.volume)))
        self.loops = int(self.loops)
        self.max_time_ms = int(max(0, self.max_time_ms))


# ---------------------------------------------------------------------------
# SoundBankRegistry
# ---------------------------------------------------------------------------


class SoundBankRegistry:
    """A named collection of :class:`SoundCue` objects.

    Registries can be merged with :meth:`merge`; later keys win.
    """

    def __init__(self) -> None:
        self._cues: Dict[str, SoundCue] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, event_name: str, cue: SoundCue) -> None:
        """Map *event_name* to *cue*, replacing any existing entry."""
        self._cues[str(event_name)] = cue

    def unregister(self, event_name: str) -> bool:
        """Remove the cue for *event_name*.  Returns ``True`` if it existed."""
        return self._cues.pop(str(event_name), None) is not None

    def merge(self, other: "SoundBankRegistry") -> None:
        """Merge *other* into this registry; *other*'s entries override."""
        self._cues.update(other._cues)

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------

    def get(self, event_name: str) -> Optional[SoundCue]:
        """Return the :class:`SoundCue` for *event_name*, or ``None``."""
        return self._cues.get(str(event_name))

    def event_names(self) -> List[str]:
        """Sorted list of all registered event names."""
        return sorted(self._cues.keys())

    def __len__(self) -> int:
        return len(self._cues)


# ---------------------------------------------------------------------------
# SoundEventBus
# ---------------------------------------------------------------------------


class SoundEventBus:
    """Runtime dispatcher that maps semantic event names to audio cues.

    The bus initialises ``pygame.mixer`` on first :meth:`emit` if it is not
    already initialised.  If the mixer cannot be initialised (e.g. no audio
    hardware, CI environment), all subsequent :meth:`emit` calls silently
    no-op — the bus enters a *degraded* state that is externally observable
    via :attr:`is_available`.

    Thread model: call from the main frame thread only.
    """

    def __init__(
        self,
        *,
        frequency: int = 44100,
        size: int = -16,
        channels: int = 2,
        buffer: int = 512,
    ) -> None:
        self._frequency = frequency
        self._size = size
        self._channels = channels
        self._buffer = buffer

        self._available: Optional[bool] = None  # None = not yet attempted
        self._registry: SoundBankRegistry = SoundBankRegistry()
        self._sound_cache: Dict[str, object] = {}  # event_name -> pygame.mixer.Sound
        self._muted: set = set()
        self._master_volume: float = 1.0

    # ------------------------------------------------------------------
    # Mixer lifecycle
    # ------------------------------------------------------------------

    def _ensure_mixer(self) -> bool:
        """Ensure pygame.mixer is ready.  Returns True if available."""
        if self._available is not None:
            return self._available
        try:
            import pygame  # type: ignore[import]
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=self._frequency,
                    size=self._size,
                    channels=self._channels,
                    buffer=self._buffer,
                )
            self._available = True
        except Exception:
            self._available = False
        return self._available  # type: ignore[return-value]

    @property
    def is_available(self) -> bool:
        """``True`` if the audio mixer is operational."""
        return self._ensure_mixer()

    # ------------------------------------------------------------------
    # Bank loading
    # ------------------------------------------------------------------

    def load_bank(self, bank: SoundBankRegistry) -> None:
        """Merge *bank* into the active registry.

        The sound cache is invalidated for any event names that changed so
        that the next :meth:`emit` re-loads the cue from the new path.
        """
        for name in bank.event_names():
            if self._registry.get(name) != bank.get(name):
                self._sound_cache.pop(name, None)
        self._registry.merge(bank)

    def register(self, event_name: str, cue: SoundCue) -> None:
        """Register a single cue, invalidating any cached sound for that name."""
        self._sound_cache.pop(event_name, None)
        self._registry.register(event_name, cue)

    # ------------------------------------------------------------------
    # Volume control
    # ------------------------------------------------------------------

    def set_master_volume(self, volume: float) -> None:
        """Set the master volume multiplier in ``[0.0, 1.0]``."""
        self._master_volume = float(max(0.0, min(1.0, volume)))

    @property
    def master_volume(self) -> float:
        return self._master_volume

    def mute(self, event_name: str) -> None:
        """Silence *event_name* without removing its registration."""
        self._muted.add(str(event_name))

    def unmute(self, event_name: str) -> None:
        """Re-enable *event_name* after a previous :meth:`mute`."""
        self._muted.discard(str(event_name))

    def is_muted(self, event_name: str) -> bool:
        return str(event_name) in self._muted

    # ------------------------------------------------------------------
    # Emission
    # ------------------------------------------------------------------

    def emit(
        self,
        event_name: str,
        *,
        volume: Optional[float] = None,
        pan: float = 0.0,
    ) -> bool:
        """Play the cue registered for *event_name*.

        Parameters
        ----------
        event_name:
            Semantic event key (e.g. ``"button.click"``).
        volume:
            Per-emit volume override in ``[0.0, 1.0]``.  When ``None``, the
            cue's default volume is used.
        pan:
            Stereo pan in ``[-1.0, 1.0]``.  ``-1`` = full left, ``0`` =
            centre, ``+1`` = full right.  Requires a stereo mixer channel.

        Returns
        -------
        bool
            ``True`` if the cue was played, ``False`` if the bus is
            unavailable, the event is not registered, or the cue is muted.
        """
        event_name = str(event_name)
        if event_name in self._muted:
            return False
        cue = self._registry.get(event_name)
        if cue is None:
            return False
        if not self._ensure_mixer():
            return False
        sound = self._load_sound(event_name, cue)
        if sound is None:
            return False

        try:
            import pygame  # type: ignore[import]
            effective_volume = (volume if volume is not None else cue.volume)
            effective_volume = float(max(0.0, min(1.0, effective_volume))) * self._master_volume

            if pan != 0.0:
                # Stereo panning via set_volume(left, right)
                left = min(1.0, 1.0 - pan) * effective_volume
                right = min(1.0, 1.0 + pan) * effective_volume
                channel = sound.play(loops=cue.loops, maxtime=cue.max_time_ms)
                if channel:
                    channel.set_volume(left, right)
            else:
                sound.set_volume(effective_volume)
                sound.play(loops=cue.loops, maxtime=cue.max_time_ms)
        except Exception:
            return False
        return True

    def _load_sound(self, event_name: str, cue: SoundCue) -> Optional[object]:
        """Load and cache the pygame.mixer.Sound for *cue*."""
        if event_name in self._sound_cache:
            return self._sound_cache[event_name]
        try:
            import pygame  # type: ignore[import]
            sound = pygame.mixer.Sound(cue.path)
            self._sound_cache[event_name] = sound
            return sound
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Playback control
    # ------------------------------------------------------------------

    def stop_all(self) -> None:
        """Stop all currently playing sounds immediately."""
        if not self._ensure_mixer():
            return
        try:
            import pygame  # type: ignore[import]
            pygame.mixer.stop()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def registered_event_names(self) -> List[str]:
        """Sorted list of all registered event names."""
        return self._registry.event_names()
