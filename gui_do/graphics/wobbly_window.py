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
        self._render_dir = (1.0, 0.0)
        self._push_pull = 1.0
        self._render_push_pull = 1.0
        self._motion_strength = 0.0
        self._render_motion_strength = 0.0
        self._settle_elapsed = 0.0
        self._settle_steps = 0
        self._drag_idle_elapsed = 0.0
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
        self.max_velocity = float(self.params.get("max_velocity", 220.0))
        self.anchor_free_radius = float(self.params.get("anchor_free_radius", 6.0))
        self.max_distort_px = float(self.params.get("max_distort_px", 184.0))
        self.max_total_distort_px = float(self.params.get("max_total_distort_px", 84.0))
        self.max_disp_mag = float(self.params.get("max_disp_mag", 108.0))
        self.arc_along_gain = float(self.params.get("arc_along_gain", self.params.get("bend_gain", 5.35)))
        self.arc_perp_gain = float(self.params.get("arc_perp_gain", self.params.get("sheet_cross_gain", 2.55)))
        self.arc_radius_scale = float(self.params.get("arc_radius_scale", 0.72))
        self.edge_weight = float(self.params.get("edge_weight", 0.84))
        self.anchor_gate_floor = float(self.params.get("anchor_gate_floor", 0.28))
        self.body_follow_gain = float(self.params.get("body_follow_gain", 0.30))
        self.arc_cross_exponent = float(self.params.get("arc_cross_exponent", 0.82))
        self.arc_along_taper = float(self.params.get("arc_along_taper", 0.16))
        self.overlap_px = int(self.params.get("overlap_px", 4))
        self.settle_timeout_seconds = float(self.params.get("settle_timeout_seconds", 0.30))
        self.settle_hard_limit_seconds = float(self.params.get("settle_hard_limit_seconds", 0.18))
        self._settle_blend_seconds = max(1e-6, min(self.settle_timeout_seconds, self.settle_hard_limit_seconds))
        self.settle_spring_boost = float(self.params.get("settle_spring_boost", 2.35))
        self.settle_damping_scale = float(self.params.get("settle_damping_scale", 0.74))
        self.drag_idle_speed_threshold = float(self.params.get("drag_idle_speed_threshold", 0.65))
        self.drag_idle_settle_delay_seconds = float(self.params.get("drag_idle_settle_delay_seconds", 0.02))
        self.drag_idle_spring_boost = float(self.params.get("drag_idle_spring_boost", 2.05))
        self.drag_idle_damping_scale = float(self.params.get("drag_idle_damping_scale", 0.78))
        self.direction_change_dot_threshold = float(self.params.get("direction_change_dot_threshold", 0.45))
        self.direction_change_perp_keep = float(self.params.get("direction_change_perp_keep", 0.22))
        self.horizontal_snap_dot_threshold = float(self.params.get("horizontal_snap_dot_threshold", -0.15))
        self.horizontal_snap_velocity_keep = float(self.params.get("horizontal_snap_velocity_keep", 0.18))
        self.visual_dir_interp_rate = float(self.params.get("visual_dir_interp_rate", 20.0))
        self.visual_scalar_interp_rate = float(self.params.get("visual_scalar_interp_rate", 26.0))
        self.settle_target_fps = float(self.params.get("settle_target_fps", 60.0))
        self.settle_epsilon = float(self.params.get("settle_epsilon", 0.18))
        self._settle_max_steps = max(
            1,
            int(round(max(self.settle_timeout_seconds, self.settle_hard_limit_seconds) * self.settle_target_fps * max(1, self.simulation_substeps))),
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
        self._render_dir = (1.0, 0.0)
        self._push_pull = 1.0
        self._render_push_pull = 1.0
        self._motion_strength = 0.0
        self._render_motion_strength = 0.0
        self._settle_elapsed = 0.0
        self._settle_steps = 0
        self._drag_idle_elapsed = 0.0
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
            if speed > self.drag_idle_speed_threshold:
                self._drag_idle_elapsed = 0.0
                nx = dx / speed
                ny = dy / speed
                previous_dir = self._dir
                self._dir = (nx, ny)
                direction_dot = (previous_dir[0] * nx) + (previous_dir[1] * ny)
                if direction_dot < self.direction_change_dot_threshold:
                    # Remove most residual velocity from the previous direction so
                    # old drag heading stops driving the current deformation.
                    vel_along = (self._vel[0] * nx) + (self._vel[1] * ny)
                    vel_perp_x = self._vel[0] - (vel_along * nx)
                    vel_perp_y = self._vel[1] - (vel_along * ny)
                    # Keep only a small fraction of along/perpendicular carry-over.
                    # This lets new heading influence the field immediately.
                    self._vel[0] = (vel_along * self.horizontal_snap_velocity_keep * nx) + (vel_perp_x * self.direction_change_perp_keep)
                    self._vel[1] = (vel_along * self.horizontal_snap_velocity_keep * ny) + (vel_perp_y * self.direction_change_perp_keep)
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
                    # Reverse only left/right push-pull mapping while preserving
                    # existing vertical motion behavior.
                    if abs(nx) >= abs(ny):
                        toward = -toward
                    # Hysteresis near neutral avoids sign chatter and directional flicker.
                    if toward >= 0.08:
                        self._push_pull = 1.0
                    elif toward <= -0.08:
                        self._push_pull = -1.0
                    # Strong horizontal reversals should visually switch direction now,
                    # not after a long interpolation tail.
                    if abs(nx) > abs(ny) and direction_dot <= self.horizontal_snap_dot_threshold:
                        self._render_dir = (nx, ny)
                        self._render_push_pull = self._push_pull
                        self._render_motion_strength = self._motion_strength
                    self._motion_strength = min(1.0, abs(toward))
                else:
                    self._push_pull = 1.0
                    self._motion_strength = 0.0

                impulse = min(self.max_impulse, speed * self.drag_coupling)
                self._vel[0] += self._dir[0] * impulse
                self._vel[1] += self._dir[1] * impulse
                vel_mag = math.hypot(self._vel[0], self._vel[1])
                if vel_mag > self.max_velocity > 1e-6:
                    vel_scale = self.max_velocity / vel_mag
                    self._vel[0] *= vel_scale
                    self._vel[1] *= vel_scale
                disp_mag = math.hypot(self._disp[0], self._disp[1])
                if disp_mag > self.max_disp_mag > 1e-6:
                    disp_scale = self.max_disp_mag / disp_mag
                    self._disp[0] *= disp_scale
                    self._disp[1] *= disp_scale
                    self._vel[0] *= disp_scale
                    self._vel[1] *= disp_scale
                self._phase += speed * self.phase_coupling
            else:
                self._drag_idle_elapsed += self.time_step
                self._motion_strength *= 0.82
        self._prev_mouse_pos = mouse_pos

    def _step_settle(self) -> None:
        """Advance damped spring state and auto-disable when fully settled."""
        dir_alpha = 1.0 - math.exp(-self.visual_dir_interp_rate * self.time_step)
        scalar_alpha = 1.0 - math.exp(-self.visual_scalar_interp_rate * self.time_step)
        blended_x = (self._render_dir[0] * (1.0 - dir_alpha)) + (self._dir[0] * dir_alpha)
        blended_y = (self._render_dir[1] * (1.0 - dir_alpha)) + (self._dir[1] * dir_alpha)
        blended_mag = math.hypot(blended_x, blended_y)
        if blended_mag > 1e-6:
            self._render_dir = (blended_x / blended_mag, blended_y / blended_mag)
        else:
            self._render_dir = self._dir
        self._render_push_pull = (self._render_push_pull * (1.0 - scalar_alpha)) + (self._push_pull * scalar_alpha)
        self._render_motion_strength = (
            (self._render_motion_strength * (1.0 - scalar_alpha))
            + (self._motion_strength * scalar_alpha)
        )

        spring_k = self.spring_k
        damping = self.damping
        if self.dragging:
            self._drag_idle_elapsed += self.time_step

        boost = 1.0
        damping_scale = 1.0
        if not self.dragging:
            boost = max(boost, self.settle_spring_boost)
            damping_scale = min(damping_scale, self.settle_damping_scale)
        elif self._drag_idle_elapsed >= self.drag_idle_settle_delay_seconds:
            boost = max(boost, self.drag_idle_spring_boost)
            damping_scale = min(damping_scale, self.drag_idle_damping_scale)

        spring_k *= boost
        damping = max(0.0, min(1.0, damping * damping_scale))

        self._vel[0] += (-spring_k * self._disp[0]) * self.time_step
        self._vel[1] += (-spring_k * self._disp[1]) * self.time_step
        self._vel[0] *= damping
        self._vel[1] *= damping
        self._disp[0] += self._vel[0] * self.time_step
        self._disp[1] += self._vel[1] * self.time_step

        disp_mag = math.hypot(self._disp[0], self._disp[1])
        if disp_mag > self.max_disp_mag > 1e-6:
            disp_scale = self.max_disp_mag / disp_mag
            self._disp[0] *= disp_scale
            self._disp[1] *= disp_scale
            self._vel[0] *= disp_scale
            self._vel[1] *= disp_scale

        if not self.dragging:
            self._settle_elapsed += self.time_step
            self._settle_steps += 1
            vel_mag = math.hypot(self._vel[0], self._vel[1])
            if disp_mag < self.settle_epsilon and vel_mag < self.settle_epsilon:
                self.active = False
                self.buffer = None
                self._scratch = None
                self._scratch_size = (0, 0)
                return
            if self._settle_elapsed >= self.settle_hard_limit_seconds:
                # Force a clean stop at the same position; geometry fade is already
                # guaranteed to be near-zero by the matched release blend horizon.
                self._disp[0] = 0.0
                self._disp[1] = 0.0
                self._vel[0] = 0.0
                self._vel[1] = 0.0
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
        self._drag_idle_elapsed = 0.0

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

        # Allow more dramatic bends while still bounding per-tile offsets for coverage safety.
        safe_component_offset = min(
            self.max_distort_px,
            max(18.0, (min(tile_w, tile_h) * 2.1) + 12.0, min(float(w), float(h)) * 0.22),
        )
        disp_mag = min(self.max_distort_px, safe_component_offset, math.hypot(self._disp[0], self._disp[1]))
        if disp_mag < 0.001:
            surface.blit(self.buffer, (base_x, base_y))
            return

        # Fade deformation to zero across settle interval so timeout deactivation
        # matches the resting geometry and avoids a visible position snap.
        release_blend = 1.0
        if not self.dragging and self._settle_blend_seconds > 1e-6:
            release_t = min(1.0, max(0.0, self._settle_elapsed / self._settle_blend_seconds))
            release_blend = 1.0 - release_t
        disp_mag *= release_blend
        if disp_mag < 0.001:
            surface.blit(self.buffer, (base_x, base_y))
            return

        dir_x, dir_y = self._render_dir
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
                    side_curve = math.copysign(abs(perp_win) ** self.arc_cross_exponent, perp_win)
                    longitudinal_taper = 1.0 - (self.arc_along_taper * abs(along_win))
                    arc_strength = max(0.0, longitudinal_taper) * edge_emphasis * anchor_gate

                    arc_along = (
                        disp_mag
                        * self.arc_along_gain
                        * self._render_push_pull
                        * side_curve
                        * arc_strength
                    )
                    arc_perp = (
                        disp_mag
                        * self.arc_perp_gain
                        * side_curve
                        * arc_strength
                        * (0.85 + (0.15 * self._render_motion_strength))
                    )

                    follow_x = self._disp[0] * self.body_follow_gain
                    follow_y = self._disp[1] * self.body_follow_gain

                    off_x = (arc_along * dir_x) + (arc_perp * perp_x) + follow_x
                    off_y = (arc_along * dir_y) + (arc_perp * perp_y) + follow_y

                    # Global geometry budget: clamp net tile displacement magnitude
                    # so rapid direction changes cannot produce runaway distortion.
                    off_mag = math.hypot(off_x, off_y)
                    max_off_mag = min(self.max_total_distort_px, safe_component_offset)
                    if off_mag > max_off_mag > 1e-6:
                        off_scale = max_off_mag / off_mag
                        off_x *= off_scale
                        off_y *= off_scale

                    off_x = int(max(-safe_component_offset, min(safe_component_offset, off_x)))
                    off_y = int(max(-safe_component_offset, min(safe_component_offset, off_y)))

                    sx = max(0, x - self.overlap_px)
                    sy = max(0, y - self.overlap_px)
                    ex = min(w, x + src_w + self.overlap_px)
                    ey = min(h, y + src_h + self.overlap_px)
                    src = pygame.Rect(sx, sy, ex - sx, ey - sy)
                    surface.blit(self.buffer, (base_x + sx + off_x, base_y + sy + off_y), src)

        _draw_tile_pass(0, 0)
