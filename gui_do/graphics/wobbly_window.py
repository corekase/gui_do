"""Wobbly window drag renderer for pygame-backed windows.

Implements a directional "jello" deformation driven by pointer velocity:
- motion injects impulses along drag direction,
- distortion decays quickly when pointer stops,
- release keeps a brief settle tail, then auto-disables.
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
        self.dragging = False
        self.buffer: Optional[pygame.Surface] = None
        self.anchor = None  # local (x, y) in window space
        self._prev_mouse_pos = None
        self._phase = 0.0
        self._dir = (1.0, 0.0)
        self._disp = [0.0, 0.0]
        self._vel = [0.0, 0.0]

        # Tunables
        self.band_height = int(self.params.get("band_height", 8))
        self.tile_width = int(self.params.get("tile_width", 12))
        self.base_amplitude = float(self.params.get("amplitude", 10.0))
        self.frequency = float(self.params.get("frequency", 0.055))
        self.phase_coupling = float(self.params.get("phase_coupling", 0.22))
        self.drag_coupling = float(self.params.get("drag_coupling", 0.55))
        self.spring_k = float(self.params.get("spring_k", 42.0))
        self.damping = float(self.params.get("damping", 0.68))
        self.time_step = float(self.params.get("time_step", 1.0 / 60.0))
        self.max_impulse = float(self.params.get("max_impulse", 74.0))
        self.anchor_free_radius = float(self.params.get("anchor_free_radius", 10.0))
        self.max_distort_px = float(self.params.get("max_distort_px", 40.0))
        self.perp_strength = float(self.params.get("perp_strength", 0.9))
        self.settle_epsilon = float(self.params.get("settle_epsilon", 0.18))

    def start_drag(self, mouse_pos, surface: Optional[pygame.Surface] = None):
        """
        Called when dragging starts. Captures buffer, sets reference point, anchors mesh.
        :param mouse_pos: (x, y) tuple of mouse position relative to window.
        """
        self.active = True
        self.dragging = True
        self._prev_mouse_pos = mouse_pos
        wx, wy = self.window.rect.topleft
        self.anchor = (int(mouse_pos[0] - wx), int(mouse_pos[1] - wy))
        self._phase = 0.0
        self._dir = (1.0, 0.0)
        self._disp[0] = 0.0
        self._disp[1] = 0.0
        self._vel[0] = 0.0
        self._vel[1] = 0.0

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
        if not self.active:
            return
        self.dragging = True
        wx, wy = self.window.rect.topleft
        self.anchor = (int(mouse_pos[0] - wx), int(mouse_pos[1] - wy))
        if self._prev_mouse_pos is not None:
            dx = float(mouse_pos[0] - self._prev_mouse_pos[0])
            dy = float(mouse_pos[1] - self._prev_mouse_pos[1])
            speed = math.hypot(dx, dy)
            if speed > 0.001:
                nx = dx / speed
                ny = dy / speed
                # Smooth heading toward latest movement direction.
                self._dir = (
                    (self._dir[0] * 0.75) + (nx * 0.25),
                    (self._dir[1] * 0.75) + (ny * 0.25),
                )
                dir_mag = max(0.001, math.hypot(self._dir[0], self._dir[1]))
                self._dir = (self._dir[0] / dir_mag, self._dir[1] / dir_mag)

                impulse = min(self.max_impulse, speed * self.drag_coupling)
                self._vel[0] += self._dir[0] * impulse
                self._vel[1] += self._dir[1] * impulse
                self._phase += speed * self.phase_coupling
        self._prev_mouse_pos = mouse_pos

    def _step_settle(self) -> None:
        """Advance damped spring state and auto-disable when fully settled."""
        self._vel[0] += (-self.spring_k * self._disp[0]) * self.time_step
        self._vel[1] += (-self.spring_k * self._disp[1]) * self.time_step
        self._vel[0] *= self.damping
        self._vel[1] *= self.damping
        self._disp[0] += self._vel[0] * self.time_step
        self._disp[1] += self._vel[1] * self.time_step

        if not self.dragging:
            disp_mag = math.hypot(self._disp[0], self._disp[1])
            vel_mag = math.hypot(self._vel[0], self._vel[1])
            if disp_mag < self.settle_epsilon and vel_mag < self.settle_epsilon:
                self.active = False
                self.buffer = None

    def end_drag(self):
        """
        Called when dragging ends. Releases anchor, animates mesh to rest.
        """
        self.dragging = False
        self._prev_mouse_pos = None

    def is_active(self) -> bool:
        return bool(self.active)

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

        self._step_settle()
        if not self.active or self.buffer is None:
            return

        w, h = self.window.rect.size
        base_x, base_y = self.window.rect.topleft
        tile_h = max(2, self.band_height)
        tile_w = max(2, self.tile_width)

        # Passive oscillation: advances even when pointer is stationary.
        self._phase += 0.18

        disp_mag = min(self.max_distort_px, math.hypot(self._disp[0], self._disp[1]))
        if disp_mag < 0.001:
            surface.blit(self.buffer, (base_x, base_y))
            return

        dir_x, dir_y = self._dir
        perp_x, perp_y = -dir_y, dir_x
        anchor_x, anchor_y = self.anchor if self.anchor is not None else (w * 0.5, h * 0.5)
        sigma_perp = max(8.0, h * 0.32)
        sigma_along = max(8.0, h * 0.40)

        def _draw_tile_pass(x_start: int, y_start: int) -> None:
            for y in range(y_start, h, tile_h):
                for x in range(x_start, w, tile_w):
                    src_w = min(tile_w, w - x)
                    src_h = min(tile_h, h - y)
                    if src_w <= 0 or src_h <= 0:
                        continue
                    center_x = float(x + (src_w * 0.5))
                    center_y = float(y + (src_h * 0.5))
                    rel_x = center_x - float(anchor_x)
                    rel_y = center_y - float(anchor_y)

                    along = (rel_x * dir_x) + (rel_y * dir_y)
                    perp = (rel_x * perp_x) + (rel_y * perp_y)

                    # Keep the exact grab region visually stable.
                    anchor_dist = math.hypot(rel_x, rel_y)
                    if anchor_dist <= self.anchor_free_radius:
                        anchor_gate = 0.0
                    else:
                        anchor_gate = min(1.0, (anchor_dist - self.anchor_free_radius) / max(1.0, h * 0.25))

                    # Strongest near movement axis; quickly decays away from it.
                    axis_falloff = math.exp(-(abs(perp) / sigma_perp))

                    # Trailing bias: deformation should mostly live opposite to motion.
                    trailing_bias = 1.0 if along <= 0.0 else math.exp(-(along / sigma_along)) * 0.55

                    wave_along = math.sin((along * self.frequency) + self._phase)
                    wave_perp = math.cos((perp * self.frequency * 0.95) - (self._phase * 1.3))
                    amount = disp_mag * axis_falloff * trailing_bias * anchor_gate
                    amount_along = max(-self.max_distort_px, min(self.max_distort_px, amount * wave_along))
                    amount_perp = max(
                        -self.max_distort_px,
                        min(self.max_distort_px, amount * self.perp_strength * wave_perp),
                    )

                    off_x = int((amount_along * dir_x) + (amount_perp * perp_x))
                    off_y = int((amount_along * dir_y) + (amount_perp * perp_y))

                    # 2px overlap around each tile hides inter-tile seam artifacts.
                    sx = max(0, x - 2)
                    sy = max(0, y - 2)
                    ex = min(w, x + src_w + 2)
                    ey = min(h, y + src_h + 2)
                    src = pygame.Rect(sx, sy, ex - sx, ey - sy)
                    surface.blit(self.buffer, (base_x + sx + off_x, base_y + sy + off_y), src)

        # Two staggered passes improve coverage and eliminate visible black seams.
        _draw_tile_pass(0, 0)
        _draw_tile_pass(tile_w // 2, tile_h // 2)
