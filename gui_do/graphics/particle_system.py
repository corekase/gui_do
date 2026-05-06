"""ParticleSystem — frame-driven 2D particle emitter.

Integrates with :class:`~gui_do.ObjectPool` for zero-GC particle recycling,
:class:`~gui_do.SurfaceCompositor` for Z-ordered rendering, and
:class:`~gui_do.SceneTimeline` for choreographed bursts.

All rendering uses plain ``pygame.draw`` — no OS extensions.

Usage::

    from gui_do import ParticleSystem, Emitter

    ps = ParticleSystem()

    # Confetti burst at (200, 200):
    burst = Emitter(
        x=200, y=200,
        rate=0,             # 0 = burst mode
        burst_count=60,
        lifetime=(0.5, 1.5),
        speed=(80, 200),
        angle_range=(0, 360),
        size=(3, 7),
        colors=[(255,80,80),(80,255,80),(80,80,255),(255,220,50)],
        gravity=300,
    )
    ps.add_emitter(burst)

    # Continuous sparkle:
    sparkle = Emitter(
        x=100, y=100,
        rate=30,            # 30 particles/second
        lifetime=(0.3, 0.8),
        speed=(20, 60),
        angle_range=(250, 290),
        size=(2, 4),
        colors=[(255, 255, 200)],
    )
    ps.add_emitter(sparkle)

    # Per-frame in your update loop:
    ps.update(dt)           # advance simulation
    ps.draw(surface)        # render to surface

    # Remove an emitter (stops emission but existing particles finish):
    ps.remove_emitter(sparkle)
    ps.clear()              # remove all emitters and particles
"""
from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..controls.base.ui_node import UiNode

if TYPE_CHECKING:
    from ..theme.color_theme import ColorTheme


Color = Tuple[int, int, int]


# ---------------------------------------------------------------------------
# _Particle — internal particle state (pooled)
# ---------------------------------------------------------------------------


class _Particle:
    """Mutable particle state.  Managed internally by :class:`ParticleSystem`."""

    __slots__ = (
        "x", "y", "vx", "vy",
        "lifetime", "age",
        "size", "start_size", "end_size",
        "color", "alpha", "alive",
        "gravity", "fade_out",
    )

    def __init__(self) -> None:
        self.x: float = 0.0
        self.y: float = 0.0
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.lifetime: float = 1.0
        self.age: float = 0.0
        self.size: float = 4.0
        self.start_size: float = 4.0
        self.end_size: float = 2.0
        self.color: Color = (255, 255, 255)
        self.alpha: int = 255
        self.alive: bool = False
        self.gravity: float = 0.0
        self.fade_out: bool = True

    def reset(self) -> None:
        self.alive = False
        self.age = 0.0


# ---------------------------------------------------------------------------
# Emitter
# ---------------------------------------------------------------------------


@dataclass
class Emitter:
    """Configuration for a single particle emission source.

    Parameters
    ----------
    x, y:
        World-space spawn position.
    rate:
        Particles emitted per second during continuous emission.
        Set to ``0`` for burst-only mode (uses *burst_count*).
    burst_count:
        Number of particles emitted immediately on the next :meth:`ParticleSystem.update`
        call after the emitter is added, or when :meth:`ParticleSystem.burst` is called.
        ``0`` means no burst.
    lifetime:
        ``(min, max)`` lifetime in seconds for each particle.
    speed:
        ``(min, max)`` initial speed in pixels/second.
    angle_range:
        ``(start_deg, end_deg)`` emission cone in degrees (0 = right, 90 = down).
    size:
        ``(start_size, end_size)`` particle radius in pixels.
        Each particle interpolates from start to end over its lifetime.
        Pass a single int/float (as a 1-tuple or both equal) for constant size.
    colors:
        List of colors to choose from per particle spawn.  Defaults to white.
    gravity:
        Downward acceleration in pixels/second².  Defaults to ``0``.
    fade_out:
        When ``True`` (default) particles fade to transparent over their lifetime.
    active:
        When ``False`` the emitter emits no new particles (existing ones continue).
    """

    x: float = 0.0
    y: float = 0.0
    rate: float = 30.0
    burst_count: int = 0
    lifetime: Tuple[float, float] = (0.5, 1.5)
    speed: Tuple[float, float] = (50.0, 150.0)
    angle_range: Tuple[float, float] = (0.0, 360.0)
    size: Tuple[float, float] = (4.0, 2.0)
    colors: List[Color] = field(default_factory=lambda: [(255, 255, 255)])
    gravity: float = 0.0
    fade_out: bool = True
    active: bool = True

    # Internal: fractional particle accumulator for rate-based emission.
    _accumulator: float = field(default=0.0, init=False, repr=False, compare=False)
    # Internal: pending burst particles to emit on next update.
    _pending_burst: int = field(default=0, init=False, repr=False, compare=False)
    # Internal: cached end size resolved once from the size tuple.
    _end_size: float = field(default=0.0, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._pending_burst = self.burst_count
        # Cache end_size to avoid per-spawn len() check.
        self._end_size = self.size[1] if len(self.size) > 1 else self.size[0]


# ---------------------------------------------------------------------------
# ParticleSystem
# ---------------------------------------------------------------------------


class ParticleSystem:
    """Manager for multiple :class:`Emitter` instances and their live particles.

    Usage::

        ps = ParticleSystem(max_particles=1000)
        ps.add_emitter(emitter)
        # Per frame:
        ps.update(dt)
        ps.draw(surface)
    """

    def __init__(self, max_particles: int = 2000) -> None:
        self._max_particles = max_particles
        self._emitters: List[Emitter] = []
        self._particles: List[_Particle] = [_Particle() for _ in range(max_particles)]
        self._active_count: int = 0
        # Free-list of available particle indices — O(1) spawn instead of O(n) scan.
        self._free_indices: deque = deque(range(max_particles))
        # Per-radius surface cache for semi-transparent particles — avoids per-draw Surface allocation.
        self._alpha_surf_cache: Dict[int, pygame.Surface] = {}

    # ------------------------------------------------------------------
    # Emitter management
    # ------------------------------------------------------------------

    def add_emitter(self, emitter: Emitter) -> None:
        """Register an emitter with this system."""
        if emitter not in self._emitters:
            self._emitters.append(emitter)

    def remove_emitter(self, emitter: Emitter) -> None:
        """Remove an emitter.  Live particles from it continue to completion."""
        try:
            self._emitters.remove(emitter)
        except ValueError:
            pass

    def burst(self, emitter: Emitter, count: Optional[int] = None) -> None:
        """Trigger an immediate burst from *emitter*.

        Parameters
        ----------
        count:
            Number of particles to emit.  Defaults to ``emitter.burst_count``.
        """
        n = count if count is not None else emitter.burst_count
        emitter._pending_burst += n

    def clear(self) -> None:
        """Remove all emitters and kill all live particles."""
        self._emitters.clear()
        for i, p in enumerate(self._particles):
            p.alive = False
        self._active_count = 0
        self._free_indices = deque(range(self._max_particles))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def active_particle_count(self) -> int:
        """Number of currently alive particles."""
        return self._active_count

    @property
    def emitter_count(self) -> int:
        return len(self._emitters)

    # ------------------------------------------------------------------
    # Internal: spawn one particle from an emitter
    # ------------------------------------------------------------------

    def _spawn(self, emitter: Emitter) -> None:
        """Spawn one particle from *emitter* using the free-list (O(1))."""
        if not self._free_indices:
            return
        idx = self._free_indices.popleft()
        p = self._particles[idx]
        p.alive = True
        p.x = emitter.x
        p.y = emitter.y
        p.age = 0.0
        p.lifetime = random.uniform(*emitter.lifetime)
        speed = random.uniform(*emitter.speed)
        a0, a1 = emitter.angle_range
        angle_deg = random.uniform(a0, a1)
        angle_rad = math.radians(angle_deg)
        p.vx = math.cos(angle_rad) * speed
        p.vy = math.sin(angle_rad) * speed
        p.start_size = emitter.size[0]
        p.end_size = emitter._end_size
        p.size = p.start_size
        p.color = random.choice(emitter.colors)
        p.alpha = 255
        p.gravity = emitter.gravity
        p.fade_out = emitter.fade_out

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance the simulation by *dt* seconds.

        Call once per frame before :meth:`draw`.
        """
        # Emit new particles from each emitter
        for emitter in self._emitters:
            # Burst
            if emitter._pending_burst > 0:
                n = emitter._pending_burst
                emitter._pending_burst = 0
                for _ in range(n):
                    if self._active_count < self._max_particles:
                        self._spawn(emitter)

            # Rate-based emission
            if emitter.active and emitter.rate > 0:
                emitter._accumulator += emitter.rate * dt
                while emitter._accumulator >= 1.0:
                    if self._active_count < self._max_particles:
                        self._spawn(emitter)
                    emitter._accumulator -= 1.0

        # Advance live particles; collect newly-dead indices for the free-list.
        alive_count = 0
        newly_dead: Optional[list] = None
        for i, p in enumerate(self._particles):
            if not p.alive:
                continue
            p.age += dt
            if p.age >= p.lifetime:
                p.alive = False
                if newly_dead is None:
                    newly_dead = []
                newly_dead.append(i)
                continue
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            t = p.age / p.lifetime
            p.size = p.start_size + (p.end_size - p.start_size) * t
            p.alpha = int(255 * (1.0 - t)) if p.fade_out else 255
            alive_count += 1
        if newly_dead:
            self._free_indices.extend(newly_dead)
        self._active_count = alive_count

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Render all live particles onto *surface*."""
        cache = self._alpha_surf_cache
        for p in self._particles:
            if not p.alive:
                continue
            radius = max(1, int(p.size))
            cx = int(p.x)
            cy = int(p.y)
            if p.alpha < 255:
                # Reuse a cached surface per radius to avoid per-frame allocation.
                tmp = cache.get(radius)
                if tmp is None:
                    tmp = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
                    cache[radius] = tmp
                else:
                    tmp.fill((0, 0, 0, 0))
                r, g, b = p.color
                pygame.draw.circle(tmp, (r, g, b, p.alpha), (radius + 1, radius + 1), radius)
                surface.blit(tmp, (cx - radius - 1, cy - radius - 1))
            else:
                pygame.draw.circle(surface, p.color, (cx, cy), radius)


# ---------------------------------------------------------------------------
# ParticleLayer — UiNode wrapper
# ---------------------------------------------------------------------------


class ParticleLayer(UiNode):
    """A :class:`~gui_do.UiNode` that hosts a :class:`ParticleSystem`.

    Renders the particle system in its ``draw`` pass.  The system's world
    coordinates are relative to the screen (not the node's rect).

    Usage::

        layer = ParticleLayer("fx", Rect(0, 0, 800, 600))
        layer.particle_system.add_emitter(emitter)
        scene.add(layer)
        # Call layer.update_particles(dt) each frame before draw.
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        *,
        max_particles: int = 2000,
    ) -> None:
        super().__init__(control_id, rect)
        self.particle_system: ParticleSystem = ParticleSystem(max_particles=max_particles)

    def accepts_mouse_focus(self) -> bool:
        return False

    def update_particles(self, dt: float) -> None:
        """Advance the particle simulation.  Call once per frame before draw."""
        self.particle_system.update(dt)

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        if not self.visible:
            return
        self.particle_system.draw(surface)
