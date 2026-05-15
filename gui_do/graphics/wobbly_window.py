"""Wobbly window drag renderer for pygame-backed windows.

Implements a simple directional push/pull arc deformation:
- dragging injects spring velocity in the drag direction,
- window geometry bends as one coherent sheet around the title-bar grab anchor,
- when movement pauses or drag ends, spring damping settles back to identity.
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
        self._scratch: Optional[pygame.Surface] = None
        self._scratch_size: tuple[int, int] = (0, 0)
        self.anchor = None  # local (x, y) in window space
        self._prev_mouse_pos = None
        self._phase = 0.0
        self._dir = (1.0, 0.0)
        self._push_pull = 1.0
        self._motion_strength = 0.0
        self._settle_elapsed = 0.0
        self._settle_steps = 0
        self._disp = [0.0, 0.0]
        self._vel = [0.0, 0.0]

        # Tunables
        self.band_height = int(self.params.get("band_height", 10))
        self.tile_width = int(self.params.get("tile_width", 14))
        self.phase_coupling = float(self.params.get("phase_coupling", 0.22))
        self.drag_coupling = float(self.params.get("drag_coupling", 0.55))
        self.spring_k = float(self.params.get("spring_k", 62.0))
        self.damping = float(self.params.get("damping", 0.60))
        self.time_step = float(self.params.get("time_step", 1.0 / 120.0))
        self.simulation_substeps = int(self.params.get("simulation_substeps", 2))
        self.max_impulse = float(self.params.get("max_impulse", 92.0))
        self.anchor_free_radius = float(self.params.get("anchor_free_radius", 6.0))
        self.max_distort_px = float(self.params.get("max_distort_px", 96.0))
        self.arc_along_gain = float(self.params.get("arc_along_gain", self.params.get("bend_gain", 2.45)))
        self.arc_perp_gain = float(self.params.get("arc_perp_gain", self.params.get("sheet_cross_gain", 1.10)))
        self.arc_radius_scale = float(self.params.get("arc_radius_scale", 0.95))
        self.edge_weight = float(self.params.get("edge_weight", 0.72))
        self.anchor_gate_floor = float(self.params.get("anchor_gate_floor", 0.28))
        self.body_follow_gain = float(self.params.get("body_follow_gain", 0.22))
        self.overlap_px = int(self.params.get("overlap_px", 4))
        self.settle_timeout_seconds = float(self.params.get("settle_timeout_seconds", 0.45))
        self.settle_target_fps = float(self.params.get("settle_target_fps", 60.0))
        self.settle_epsilon = float(self.params.get("settle_epsilon", 0.18))
        self._settle_max_steps = max(
            1,
            int(round(self.settle_timeout_seconds * self.settle_target_fps * max(1, self.simulation_substeps))),
        )

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
        self._push_pull = 1.0
        self._motion_strength = 0.0
        self._settle_elapsed = 0.0
        self._settle_steps = 0
        self._disp[0] = 0.0
        self._disp[1] = 0.0
        self._vel[0] = 0.0
        self._vel[1] = 0.0

        self.buffer = None
        self._scratch = None
        self._scratch_size = (0, 0)
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
                content_rect = None
                content_rect_fn = getattr(self.window, "content_rect", None)
                if callable(content_rect_fn):
                    try:
                        content_rect = content_rect_fn()
                    except Exception:
                        content_rect = None
                if content_rect is None:
                    content_rect = self.window.rect
                cx = float(content_rect.centerx - mouse_pos[0])
                cy = float(content_rect.centery - mouse_pos[1])
                to_content_mag = math.hypot(cx, cy)
                if to_content_mag > 0.001:
                    tx = cx / to_content_mag
                    ty = cy / to_content_mag
                    toward = (nx * tx) + (ny * ty)
                    # Hysteresis near neutral avoids sign chatter and directional flicker.
                    if toward >= 0.08:
                        self._push_pull = 1.0
                    elif toward <= -0.08:
                        self._push_pull = -1.0
                    self._motion_strength = min(1.0, abs(toward))
                else:
                    self._push_pull = 1.0
                    self._motion_strength = 0.0
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
            else:
                self._motion_strength *= 0.82
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
            self._settle_elapsed += self.time_step
            self._settle_steps += 1
            disp_mag = math.hypot(self._disp[0], self._disp[1])
            vel_mag = math.hypot(self._vel[0], self._vel[1])
            if disp_mag < self.settle_epsilon and vel_mag < self.settle_epsilon:
                self.active = False
                self.buffer = None
                self._scratch = None
                self._scratch_size = (0, 0)
                return
            if (
                self._settle_steps > self._settle_max_steps
                or
                self._settle_elapsed > self.settle_timeout_seconds
            ):
                self.active = False
                self.buffer = None
                self._scratch = None
                self._scratch_size = (0, 0)

    def end_drag(self):
        """
        Called when dragging ends. Releases anchor, animates mesh to rest.
        """
        self.dragging = False
        self._prev_mouse_pos = None
        self._motion_strength = 0.0
        self._settle_elapsed = 0.0
        self._settle_steps = 0

    def is_active(self) -> bool:
        return bool(self.active)

    def _refresh_buffer(self, surface: pygame.Surface, theme, draw_window_standard) -> None:
        """Refresh the off-screen drag bitmap from the window's latest frame output."""
        size = surface.get_size()
        if self._scratch is None or self._scratch_size != size:
            self._scratch = pygame.Surface(size, pygame.SRCALPHA)
            self._scratch_size = size

        scratch = self._scratch
        window_rect = pygame.Rect(self.window.rect)
        # Clear just the current window area, not the whole scratch surface.
        scratch.fill((0, 0, 0, 0), window_rect)
        draw_window_standard(scratch, theme)

        clip = window_rect.clip(scratch.get_rect())

        # Reuse window-sized buffer to avoid per-frame allocations.
        if self.buffer is None or self.buffer.get_size() != window_rect.size:
            self.buffer = pygame.Surface(window_rect.size, pygame.SRCALPHA)
        else:
            self.buffer.fill((0, 0, 0, 0))

        if clip.width > 0 and clip.height > 0:
            dst_x = clip.left - window_rect.left
            dst_y = clip.top - window_rect.top
            self.buffer.blit(scratch, (dst_x, dst_y), clip)

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

        substeps = max(1, self.simulation_substeps)
        for _ in range(substeps):
            self._step_settle()
            if not self.active:
                break
        if not self.active or self.buffer is None:
            # Transition frame: if settle just completed, draw the normal window now
            # so we don't emit a blank frame flash before WindowControl exits wobble mode.
            if draw_window_standard is not None and theme is not None:
                draw_window_standard(surface, theme)
            return

        w, h = self.window.rect.size
        base_x, base_y = self.window.rect.topleft
        tile_h = max(2, self.band_height)
        tile_w = max(2, self.tile_width)

        # Passive oscillation: advances even when pointer is stationary.
        self._phase += 0.18

        safe_component_offset = min(
            self.max_distort_px,
            max(10.0, (min(tile_w, tile_h) * 1.45) + 8.0),
        )
        disp_mag = min(self.max_distort_px, safe_component_offset, math.hypot(self._disp[0], self._disp[1]))
        if disp_mag < 0.001:
            surface.blit(self.buffer, (base_x, base_y))
            return

        # Fade deformation to zero across settle interval so timeout deactivation
        # matches the resting geometry and avoids a visible position snap.
        release_blend = 1.0
        if not self.dragging and self.settle_timeout_seconds > 1e-6:
            release_t = min(1.0, max(0.0, self._settle_elapsed / self.settle_timeout_seconds))
            release_blend = 1.0 - release_t
        disp_mag *= release_blend
        if disp_mag < 0.001:
            surface.blit(self.buffer, (base_x, base_y))
            return

        dir_x, dir_y = self._dir
        perp_x, perp_y = -dir_y, dir_x
        anchor_x, anchor_y = self.anchor if self.anchor is not None else (w * 0.5, h * 0.5)
        max_dist_x = max(anchor_x, float(w) - anchor_x)
        max_dist_y = max(anchor_y, float(h) - anchor_y)
        max_anchor_dist = max(1.0, math.hypot(max_dist_x, max_dist_y))
        arc_radius = max(24.0, max_anchor_dist * self.arc_radius_scale)

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

                    anchor_dist = math.hypot(rel_x, rel_y)
                    if anchor_dist <= self.anchor_free_radius:
                        anchor_gate = 1.0
                    else:
                        gate_span = max(1.0, arc_radius - self.anchor_free_radius)
                        anchor_gate = min(1.0, (anchor_dist - self.anchor_free_radius) / gate_span)
                        anchor_gate = self.anchor_gate_floor + ((1.0 - self.anchor_gate_floor) * anchor_gate)

                    distance_field = min(1.0, anchor_dist / max(1.0, arc_radius))
                    edge_emphasis = self.edge_weight + ((1.0 - self.edge_weight) * distance_field)

                    nx_win = (center_x / max(1.0, float(w))) * 2.0 - 1.0
                    ny_win = (center_y / max(1.0, float(h))) * 2.0 - 1.0
                    along_win = (nx_win * dir_x) + (ny_win * dir_y)
                    perp_win = (nx_win * perp_x) + (ny_win * perp_y)
                    side_curve = math.copysign(abs(perp_win) ** 1.25, perp_win)
                    longitudinal_taper = 1.0 - (0.35 * abs(along_win))
                    arc_strength = max(0.0, longitudinal_taper) * edge_emphasis * anchor_gate

                    arc_along = (
                        disp_mag
                        * self.arc_along_gain
                        * self._push_pull
                        * side_curve
                        * arc_strength
                    )
                    arc_perp = (
                        disp_mag
                        * self.arc_perp_gain
                        * side_curve
                        * arc_strength
                        * (0.85 + (0.15 * self._motion_strength))
                    )

                    follow_x = self._disp[0] * self.body_follow_gain
                    follow_y = self._disp[1] * self.body_follow_gain

                    off_x = (arc_along * dir_x) + (arc_perp * perp_x) + follow_x
                    off_y = (arc_along * dir_y) + (arc_perp * perp_y) + follow_y
                    off_x = int(max(-safe_component_offset, min(safe_component_offset, off_x)))
                    off_y = int(max(-safe_component_offset, min(safe_component_offset, off_y)))

                    sx = max(0, x - self.overlap_px)
                    sy = max(0, y - self.overlap_px)
                    ex = min(w, x + src_w + self.overlap_px)
                    ey = min(h, y + src_h + self.overlap_px)
                    src = pygame.Rect(sx, sy, ex - sx, ey - sy)
                    surface.blit(self.buffer, (base_x + sx + off_x, base_y + sy + off_y), src)

        _draw_tile_pass(0, 0)
