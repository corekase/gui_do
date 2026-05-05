"""SpriteSheet + FrameAnimation — atlas-based frame animation.

:class:`SpriteSheet` slices a surface atlas into indexed frames.
:class:`FrameAnimation` drives frame-sequenced playback from a sheet.

All rendering uses :func:`pygame.Surface.subsurface` and
:func:`pygame.Surface.blit` — no OS extensions.

Usage::

    from gui_do import SpriteSheet, FrameAnimation

    sheet = SpriteSheet(surface, frame_w=64, frame_h=64)

    anim = FrameAnimation(
        sheet=sheet,
        frames=[0, 1, 2, 3, 4, 3, 2, 1],   # frame indices (may repeat)
        fps=12,
        loop=True,
    )

    # Per-frame in your update loop:
    anim.update(dt)

    # Draw current frame:
    anim.draw(surface, (100, 200))

    # Or get the current surface:
    img = anim.current_surface

    # Control playback:
    anim.pause()
    anim.play()
    anim.reset()
    anim.seek_frame(2)
"""
from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

from pygame import Rect, Surface


# ---------------------------------------------------------------------------
# SpriteSheet
# ---------------------------------------------------------------------------


class SpriteSheet:
    """Slices a surface atlas into indexed sub-surfaces.

    Parameters
    ----------
    surface:
        The atlas image (any :class:`pygame.Surface`).
    frame_w:
        Width of each frame in pixels.
    frame_h:
        Height of each frame in pixels.

    The sheet is sliced left-to-right, top-to-bottom.  Frame indices are
    0-based.
    """

    def __init__(self, surface: Surface, frame_w: int, frame_h: int) -> None:
        if frame_w <= 0 or frame_h <= 0:
            raise ValueError(f"frame_w and frame_h must be positive, got {frame_w}x{frame_h}")
        self._surface = surface
        self._frame_w = int(frame_w)
        self._frame_h = int(frame_h)
        sw, sh = surface.get_size()
        cols = max(1, sw // self._frame_w)
        rows = max(1, sh // self._frame_h)
        self._cols = cols
        self._frame_count = cols * rows
        self._cache: dict = {}

    @property
    def frame_count(self) -> int:
        """Total number of frames in the sheet."""
        return self._frame_count

    @property
    def frame_w(self) -> int:
        return self._frame_w

    @property
    def frame_h(self) -> int:
        return self._frame_h

    def frame(self, index: int) -> Surface:
        """Return the sub-surface for the given 0-based frame *index*.

        Sub-surfaces are cached after first access.
        """
        if index < 0 or index >= self._frame_count:
            raise IndexError(f"Frame index {index} out of range [0, {self._frame_count})")
        if index in self._cache:
            return self._cache[index]
        col = index % self._cols
        row = index // self._cols
        x = col * self._frame_w
        y = row * self._frame_h
        sub = self._surface.subsurface(Rect(x, y, self._frame_w, self._frame_h))
        self._cache[index] = sub
        return sub

    def frames(self, indices: Sequence[int]) -> List[Surface]:
        """Return a list of sub-surfaces for the given frame *indices*."""
        return [self.frame(i) for i in indices]


# ---------------------------------------------------------------------------
# FrameAnimation
# ---------------------------------------------------------------------------


class FrameAnimation:
    """Time-driven frame-by-frame animation from a :class:`SpriteSheet`.

    Parameters
    ----------
    sheet:
        The source sprite sheet.
    frames:
        Ordered list of frame indices to play back.
    fps:
        Playback rate in frames per second.  Must be > 0.
    loop:
        When ``True`` (default) the animation restarts after the last frame.
    on_complete:
        Optional callback invoked when the animation reaches the last frame
        (called once per loop cycle if *loop* is ``True``).
    """

    def __init__(
        self,
        sheet: SpriteSheet,
        frames: Sequence[int],
        fps: float,
        *,
        loop: bool = True,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        if not frames:
            raise ValueError("frames must be a non-empty sequence of frame indices")
        if fps <= 0:
            raise ValueError(f"fps must be positive, got {fps}")
        self._sheet = sheet
        self._frames: List[int] = list(frames)
        self._frame_duration: float = 1.0 / fps
        self.loop = loop
        self.on_complete = on_complete
        self._frame_index: int = 0
        self._elapsed: float = 0.0
        self._playing: bool = True
        self._completed: bool = False

    # ------------------------------------------------------------------
    # Playback control
    # ------------------------------------------------------------------

    def play(self) -> None:
        """Resume playback."""
        self._playing = True

    def pause(self) -> None:
        """Pause playback.  The current frame is held."""
        self._playing = False

    def reset(self) -> None:
        """Reset to the first frame and resume playback."""
        self._frame_index = 0
        self._elapsed = 0.0
        self._playing = True
        self._completed = False

    def seek_frame(self, index: int) -> None:
        """Jump to the given frame *index* within :attr:`frames`.

        *index* is relative to the :attr:`frames` list, not the sheet.
        """
        n = len(self._frames)
        if not (0 <= index < n):
            raise IndexError(f"Frame sequence index {index} out of range [0, {n})")
        self._frame_index = index
        self._elapsed = 0.0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def is_complete(self) -> bool:
        """``True`` if a non-looping animation has finished."""
        return self._completed

    @property
    def current_frame_index(self) -> int:
        """Current position within the :attr:`frames` list."""
        return self._frame_index

    @property
    def frames(self) -> List[int]:
        """The list of sheet frame indices in playback order."""
        return self._frames

    @property
    def current_surface(self) -> Surface:
        """The :class:`pygame.Surface` for the current frame."""
        return self._sheet.frame(self._frames[self._frame_index])

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance the animation by *dt* seconds.

        Call once per frame before :meth:`draw`.
        """
        if not self._playing or self._completed:
            return
        self._elapsed += dt
        n = len(self._frames)
        while self._elapsed >= self._frame_duration:
            self._elapsed -= self._frame_duration
            self._frame_index += 1
            if self._frame_index >= n:
                if self.loop:
                    self._frame_index = 0
                    if self.on_complete is not None:
                        self.on_complete()
                else:
                    self._frame_index = n - 1
                    self._playing = False
                    self._completed = True
                    if self.on_complete is not None:
                        self.on_complete()
                    break

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: Surface, pos: Tuple[int, int]) -> None:
        """Blit the current frame to *surface* at *pos*."""
        surface.blit(self.current_surface, pos)
