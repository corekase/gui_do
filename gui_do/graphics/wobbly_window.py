"""Wobbly window drag renderer for pygame-backed windows.

This implementation uses an off-screen snapshot and renders it as horizontal
bands with per-band offsets to emulate a jelly-like wobble while dragging.
"""

from __future__ import annotations

import math
from typing import Any, Optional

import pygame

class WobblyWindowController:
    def __init__(self, window: Any, params: Optional[dict] = None):
        """
        Initialize the mesh, buffer, and parameters for the wobbly window effect.
        :param window: The window object to which the effect is applied.
        :param params: Optional dictionary of wobble parameters (spring, damping, mesh size, etc).
        """
        self.window = window
        self.params = params or {}
        self.active = False
        self.buffer: Optional[pygame.Surface] = None
        self.anchor = None  # local (x, y) in window space
        self._prev_mouse_pos = None
        self._phase = 0.0
        self._wobble_x = 0.0
        self._wobble_vx = 0.0

        # Tunables
        self.band_height = int(self.params.get("band_height", 8))
        self.amplitude = float(self.params.get("amplitude", 10.0))
        self.frequency = float(self.params.get("frequency", 0.10))
        self.drag_coupling = float(self.params.get("drag_coupling", 0.45))
        self.spring_k = float(self.params.get("spring_k", 18.0))
        self.damping = float(self.params.get("damping", 0.82))
        self.time_step = float(self.params.get("time_step", 1.0 / 60.0))

    def start_drag(self, mouse_pos, surface: Optional[pygame.Surface] = None):
        """
        Called when dragging starts. Captures buffer, sets reference point, anchors mesh.
        :param mouse_pos: (x, y) tuple of mouse position relative to window.
        """
        self.active = True
        self._prev_mouse_pos = mouse_pos
        wx, wy = self.window.rect.topleft
        self.anchor = (int(mouse_pos[0] - wx), int(mouse_pos[1] - wy))
        self._phase = 0.0
        self._wobble_x = 0.0
        self._wobble_vx = 0.0

        self.buffer = None
        if surface is not None:
            rect = self.window.rect.clip(surface.get_rect())
            if rect.width > 0 and rect.height > 0 and rect.size == self.window.rect.size:
                self.buffer = surface.subsurface(self.window.rect).copy()

    def update_drag(self, mouse_pos):
        """
        Called on each drag update. Updates mesh simulation with new anchor position.
        :param mouse_pos: (x, y) tuple of current mouse position.
        """
        if not self.active or self.buffer is None:
            return
        if self._prev_mouse_pos is not None:
            dx = float(mouse_pos[0] - self._prev_mouse_pos[0])
            self._wobble_vx += dx * self.drag_coupling
            self._phase += abs(dx) * 0.12
        self._prev_mouse_pos = mouse_pos

        # Spring-damper integration for horizontal jiggle.
        self._wobble_vx += (-self.spring_k * self._wobble_x) * self.time_step
        self._wobble_vx *= self.damping
        self._wobble_x += self._wobble_vx * self.time_step

    def end_drag(self):
        """
        Called when dragging ends. Releases anchor, animates mesh to rest.
        """
        self.active = False
        self._prev_mouse_pos = None
        self._wobble_x = 0.0
        self._wobble_vx = 0.0
        self._phase = 0.0
        self.buffer = None

    def _refresh_buffer(self, surface: pygame.Surface, theme, draw_window_standard) -> None:
        """Refresh the off-screen drag bitmap from the window's latest frame output."""
        scratch = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        draw_window_standard(scratch, theme)
        rect = self.window.rect.clip(scratch.get_rect())
        if rect.width > 0 and rect.height > 0 and rect.size == self.window.rect.size:
            self.buffer = scratch.subsurface(self.window.rect).copy()

    def render(self, surface, theme=None, draw_window_standard=None):
        """
        Draw the warped buffer using the mesh onto the given surface.
        :param surface: The rendering surface/context.
        """
        if not self.active:
            return
        if draw_window_standard is not None and theme is not None:
            # Pull a fresh snapshot every frame so animated window content remains live while dragging.
            self._refresh_buffer(surface, theme, draw_window_standard)
        if self.buffer is None:
            return
        w, h = self.window.rect.size
        base_x, base_y = self.window.rect.topleft
        band_h = max(2, self.band_height)

        # Add passive settle motion while active drag is held.
        self._phase += 0.25

        for y in range(0, h, band_h):
            slice_h = min(band_h, h - y)
            src = pygame.Rect(0, y, w, slice_h)
            # Anchor-aware attenuation keeps the grab point steadier than edges.
            if self.anchor is not None and h > 0:
                anchor_y = float(self.anchor[1])
                distance = abs(float(y + (slice_h * 0.5)) - anchor_y) / max(1.0, h * 0.5)
                attenuation = min(1.0, max(0.15, distance))
            else:
                attenuation = 1.0
            wave = math.sin((y * self.frequency) + self._phase) * self.amplitude
            offset_x = int((wave + self._wobble_x) * attenuation)
            surface.blit(self.buffer, (base_x + offset_x, base_y + y), src)
