"""Shear-only window drag renderer for pygame-backed windows."""

from __future__ import annotations

import math
from typing import Any, Optional

import pygame


class ShearWindowController:
    """Applies a horizontal shear deformation while dragging a window titlebar."""

    def __init__(self, window: Any, params: Optional[dict] = None):
        self.window = window
        self.params = params or {}

        self.active = False
        self.dragging = False
        self.anchor: Optional[tuple[int, int]] = None
        self._prev_mouse_pos: Optional[tuple[int, int]] = None

        self.buffer: Optional[pygame.Surface] = None
        self._scratch: Optional[pygame.Surface] = None
        self._scratch_size: tuple[int, int] = (0, 0)

        self._disp = [0.0, 0.0]
        self._vel = [0.0, 0.0]
        self._drag_dir = (1.0, 0.0)
        self._shear_dir_x = 1.0
        self._drag_handover_active = False
        self._drag_handover_elapsed = 0.0
        self._drag_handover_start_x = 1.0
        self._drag_handover_end_x = 1.0
        self._drag_motion_started = False
        self._drag_start_handover_active = False
        self._drag_start_handover_elapsed = 0.0
        self._drag_start_blend = 0.0
        self._motion_strength = 0.0
        self._settle_elapsed = 0.0
        self._settle_steps = 0
        self._drag_idle_elapsed = 0.0
        self._release_frame_pending = False
        self._release_drag_shear_blend = 1.0
        self._release_idle_influence = 1.0
        self._last_drag_frame_valid = False
        self._last_drag_shear_dir_x = 1.0
        self._last_drag_shear_blend = 1.0
        self._drag_speed_smoothed = 0.0
        self._drag_idle_influence = 1.0
        self._drag_is_idle = True

        # Shear + settle tunables
        self.band_height = int(self.params.get("band_height", 10))
        self.tile_width = int(self.params.get("tile_width", 16))
        self.overlap_px = int(self.params.get("overlap_px", 4))

        self.time_step = float(self.params.get("time_step", 1.0 / 120.0))
        self.simulation_substeps = int(self.params.get("simulation_substeps", 3))
        self.spring_k = float(self.params.get("spring_k", 62.0))
        self.damping = float(self.params.get("damping", 0.60))
        self.drag_coupling = float(self.params.get("drag_coupling", 0.78))
        self.max_impulse = float(self.params.get("max_impulse", 128.0))
        self.max_velocity = float(self.params.get("max_velocity", 300.0))
        self.max_disp_mag = float(self.params.get("max_disp_mag", 108.0))
        self.max_distort_px = float(self.params.get("max_distort_px", 96.0))

        self.shear_gain = float(self.params.get("shear_gain", 3.5))
        self.shear_horizontal_emphasis = float(self.params.get("shear_horizontal_emphasis", 1.7))
        self.shear_distance_boost_px = float(self.params.get("shear_distance_boost_px", 40.0))

        self.drag_idle_speed_threshold = float(self.params.get("drag_idle_speed_threshold", 1.10))
        self.drag_idle_speed_enter = float(
            self.params.get("drag_idle_speed_enter", self.drag_idle_speed_threshold)
        )
        self.drag_idle_speed_exit = float(
            self.params.get("drag_idle_speed_exit", self.drag_idle_speed_enter * 1.35)
        )
        self.drag_speed_smoothing_seconds = float(self.params.get("drag_speed_smoothing_seconds", 0.050))
        self.drag_idle_influence_smoothing_seconds = float(
            self.params.get("drag_idle_influence_smoothing_seconds", 0.080)
        )
        self.drag_direction_handover_seconds = float(self.params.get("drag_direction_handover_seconds", 0.06))
        self.drag_start_handover_seconds = float(self.params.get("drag_start_handover_seconds", 0.07))
        self.drag_idle_settle_delay_seconds = float(
            self.params.get(
                "drag_idle_settle_trigger_seconds",
                self.params.get("drag_idle_settle_delay_seconds", 0.07),
            )
        )

        self.settle_timeout_seconds = float(self.params.get("settle_timeout_seconds", 0.22))
        self.settle_hard_limit_seconds = float(self.params.get("settle_hard_limit_seconds", 0.12))
        self.release_blend_seconds = float(self.params.get("release_blend_seconds", 0.16))
        self.release_hard_limit_seconds = float(self.params.get("release_hard_limit_seconds", 0.24))
        self._settle_blend_seconds = max(1e-6, min(self.release_blend_seconds, self.release_hard_limit_seconds))
        self.settle_spring_boost = float(self.params.get("settle_spring_boost", 2.35))
        self.settle_damping_scale = float(self.params.get("settle_damping_scale", 0.74))
        self.settle_target_fps = float(self.params.get("settle_target_fps", 120.0))
        self.settle_epsilon = float(self.params.get("settle_epsilon", 0.12))
        self._settle_max_steps = max(
            1,
            int(
                round(
                    max(self.settle_timeout_seconds, self.release_hard_limit_seconds)
                    * self.settle_target_fps
                    * max(1, self.simulation_substeps)
                )
            ),
        )

    def start_drag(self, mouse_pos, surface: Optional[pygame.Surface] = None):
        self.active = True
        self.dragging = True
        self._prev_mouse_pos = mouse_pos
        wx, wy = self.window.rect.topleft
        self.anchor = (int(mouse_pos[0] - wx), int(mouse_pos[1] - wy))

        self._disp[0] = 0.0
        self._disp[1] = 0.0
        self._vel[0] = 0.0
        self._vel[1] = 0.0
        self._drag_dir = (1.0, 0.0)
        self._shear_dir_x = 1.0
        self._drag_handover_active = False
        self._drag_handover_elapsed = 0.0
        self._drag_handover_start_x = self._shear_dir_x
        self._drag_handover_end_x = self._shear_dir_x
        self._drag_motion_started = False
        self._drag_start_handover_active = False
        self._drag_start_handover_elapsed = 0.0
        self._drag_start_blend = 0.0
        self._motion_strength = 0.0
        self._settle_elapsed = 0.0
        self._settle_steps = 0
        self._drag_idle_elapsed = 0.0
        self._release_frame_pending = False
        self._release_drag_shear_blend = 1.0
        self._release_idle_influence = 1.0
        self._last_drag_frame_valid = False
        self._last_drag_shear_dir_x = self._shear_dir_x
        self._last_drag_shear_blend = 1.0
        self._drag_speed_smoothed = 0.0
        self._drag_idle_influence = 1.0
        self._drag_is_idle = True

        self.buffer = None
        self._scratch = None
        self._scratch_size = (0, 0)
        if surface is not None:
            rect = self.window.rect.clip(surface.get_rect())
            if rect.width > 0 and rect.height > 0 and rect.size == self.window.rect.size:
                self.buffer = surface.subsurface(self.window.rect).copy()

    def update_drag(self, mouse_pos):
        if not self.active or not self.dragging:
            return
        wx, wy = self.window.rect.topleft
        self.anchor = (int(mouse_pos[0] - wx), int(mouse_pos[1] - wy))

        if self._prev_mouse_pos is not None:
            dx = float(mouse_pos[0] - self._prev_mouse_pos[0])
            dy = float(mouse_pos[1] - self._prev_mouse_pos[1])
            speed = math.hypot(dx, dy)

            speed_tau = max(1e-6, self.drag_speed_smoothing_seconds)
            speed_alpha = 1.0 - math.exp(-(self.time_step / speed_tau))
            self._drag_speed_smoothed += (speed - self._drag_speed_smoothed) * speed_alpha
            if speed > 0.0:
                self._drag_idle_elapsed = 0.0

            if speed > 1e-6:
                inv = 1.0 / speed
                new_drag_dir = (dx * inv, dy * inv)
                prev_shear_dir_x = self._shear_dir_x
                self._drag_dir = new_drag_dir

                new_dir_x = new_drag_dir[0]
                if not self._drag_motion_started:
                    self._drag_motion_started = True
                    self._drag_start_handover_active = True
                    self._drag_start_handover_elapsed = 0.0
                    self._drag_start_blend = 0.0
                    self._drag_handover_active = False
                    if abs(new_dir_x) > 1e-6:
                        self._shear_dir_x = new_dir_x
                elif (
                    abs(new_dir_x) > 1e-6
                    and abs(prev_shear_dir_x) > 1e-6
                    and (new_dir_x * prev_shear_dir_x) < 0.0
                ):
                    self._drag_handover_active = True
                    self._drag_handover_elapsed = 0.0
                    self._drag_handover_start_x = prev_shear_dir_x
                    self._drag_handover_end_x = new_dir_x
                elif not self._drag_handover_active and abs(new_dir_x) > 1e-6:
                    self._shear_dir_x = new_dir_x
                self._motion_strength = max(self._motion_strength * 0.86, min(1.0, speed / 48.0))

                impulse = min(self.max_impulse, speed * self.drag_coupling)
                self._vel[0] += self._drag_dir[0] * impulse
                self._vel[1] += self._drag_dir[1] * impulse

                vel_mag = math.hypot(self._vel[0], self._vel[1])
                if vel_mag > self.max_velocity > 1e-6:
                    scale = self.max_velocity / vel_mag
                    self._vel[0] *= scale
                    self._vel[1] *= scale
            else:
                self._motion_strength *= 0.86

        self._prev_mouse_pos = mouse_pos

    def _update_drag_direction_handover(self) -> None:
        if not self._drag_handover_active:
            return

        duration = max(1e-6, self.drag_direction_handover_seconds)
        self._drag_handover_elapsed += self.time_step
        t = min(1.0, self._drag_handover_elapsed / duration)
        smooth_t = (t * t) * (3.0 - (2.0 * t))
        self._shear_dir_x = self._drag_handover_start_x + (
            (self._drag_handover_end_x - self._drag_handover_start_x) * smooth_t
        )
        if t >= 1.0:
            self._drag_handover_active = False
            self._shear_dir_x = self._drag_handover_end_x

    def _update_drag_start_handover(self) -> None:
        if not self._drag_start_handover_active:
            return

        duration = max(1e-6, self.drag_start_handover_seconds)
        self._drag_start_handover_elapsed += self.time_step
        t = min(1.0, self._drag_start_handover_elapsed / duration)
        self._drag_start_blend = (t * t) * (3.0 - (2.0 * t))
        if t >= 1.0:
            self._drag_start_handover_active = False
            self._drag_start_blend = 1.0

    def end_drag(self, mouse_pos: Optional[tuple[int, int]] = None):
        if mouse_pos is not None and self.active and self.dragging:
            # Fold the release-point mouse sample into drag state so settle starts
            # from the exact final direction/velocity envelope.
            self.update_drag(mouse_pos)
        elif mouse_pos is not None:
            wx, wy = self.window.rect.topleft
            self.anchor = (int(mouse_pos[0] - wx), int(mouse_pos[1] - wy))

        surface = getattr(self.window, "surface", None)
        theme = getattr(self.window, "theme", None)
        draw_window_standard = getattr(self.window, "_draw_standard", None)
        if surface is not None and draw_window_standard is not None:
            try:
                self._refresh_buffer(surface, theme, draw_window_standard)
            except Exception:
                pass

        self.dragging = False
        self._prev_mouse_pos = None
        self._settle_elapsed = 0.0
        self._settle_steps = 0
        self._release_idle_influence = self._drag_idle_influence

        if self._last_drag_frame_valid:
            # Use the exact last rendered drag envelope to avoid release pops
            # caused by event timing differences between mouse move/up.
            self._release_drag_shear_blend = self._last_drag_shear_blend
            self._shear_dir_x = self._last_drag_shear_dir_x
        else:
            idle_blend = max(0.0, min(1.0, 1.0 - self._drag_idle_influence))
            start_blend = self._drag_start_blend if self._drag_motion_started else 1.0
            self._release_drag_shear_blend = max(0.0, min(1.0, idle_blend * start_blend))

        self._drag_motion_started = False
        self._drag_start_handover_active = False
        self._drag_start_handover_elapsed = 0.0
        self._drag_start_blend = 0.0
        self._drag_idle_elapsed = 0.0
        self._release_frame_pending = True
        self._last_drag_frame_valid = False
        self._drag_speed_smoothed = 0.0
        self._drag_is_idle = True
        # Preserve exact shear state at mouse-up; release settle should begin
        # from the current deformation, then quickly relax to neutral.

    def is_active(self) -> bool:
        return bool(self.active)

    def _iter_control_subtree(self, root: Any):
        stack = [root]
        seen = set()
        while stack:
            node = stack.pop()
            node_id = id(node)
            if node_id in seen:
                continue
            seen.add(node_id)
            yield node
            children = getattr(node, "children", None)
            if children:
                stack.extend(children)

    def _draw_window_local_buffer(self, theme, draw_window_standard, window_rect: pygame.Rect) -> None:
        assert self.buffer is not None
        self.buffer.fill((0, 0, 0, 0))

        offset_x = -window_rect.left
        offset_y = -window_rect.top
        shifted: list[tuple[Any, pygame.Rect]] = []
        try:
            for control in self._iter_control_subtree(self.window):
                rect = getattr(control, "rect", None)
                if isinstance(rect, pygame.Rect):
                    original = rect.copy()
                    control.rect = rect.move(offset_x, offset_y)
                    shifted.append((control, original))
            draw_window_standard(self.buffer, theme)
        finally:
            for control, original in reversed(shifted):
                control.rect = original

    def _refresh_buffer(self, surface: pygame.Surface, theme, draw_window_standard) -> None:
        window_rect = pygame.Rect(self.window.rect)
        if self.buffer is None or self.buffer.get_size() != window_rect.size:
            self.buffer = pygame.Surface(window_rect.size, pygame.SRCALPHA)

        surface_rect = surface.get_rect()
        clip = window_rect.clip(surface_rect)

        # If any part of the window is offscreen, render to a local buffer so
        # uncovered pixels do not become transparent/black in the shear pass.
        if clip.size != window_rect.size:
            self._draw_window_local_buffer(theme, draw_window_standard, window_rect)
            return

        size = surface.get_size()
        if self._scratch is None or self._scratch_size != size:
            self._scratch = pygame.Surface(size, pygame.SRCALPHA)
            self._scratch_size = size

        scratch = self._scratch
        scratch.fill((0, 0, 0, 0), window_rect)
        draw_window_standard(scratch, theme)
        self.buffer.fill((0, 0, 0, 0))

        if clip.width > 0 and clip.height > 0:
            dst_x = clip.left - window_rect.left
            dst_y = clip.top - window_rect.top
            self.buffer.blit(scratch, (dst_x, dst_y), clip)

    def _step_settle(self) -> None:
        self._update_drag_start_handover()
        self._update_drag_direction_handover()

        spring_k = self.spring_k
        damping = self.damping
        drag_idle_influence = 0.0

        def _smoothstep(edge0: float, edge1: float, value: float) -> float:
            if edge1 <= edge0:
                return 1.0 if value >= edge1 else 0.0
            t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
            return t * t * (3.0 - (2.0 * t))

        if self.dragging:
            self._drag_idle_elapsed += self.time_step

            # Continuously decay speed estimate when no fresh motion is sampled.
            speed_tau = max(1e-6, self.drag_speed_smoothing_seconds)
            speed_decay = math.exp(-(self.time_step / speed_tau))
            self._drag_speed_smoothed *= speed_decay

            enter = self.drag_idle_speed_enter
            exit_speed = max(enter + 1e-6, self.drag_idle_speed_exit)
            if self._drag_is_idle:
                if self._drag_speed_smoothed > exit_speed:
                    self._drag_is_idle = False
            elif self._drag_speed_smoothed < enter:
                self._drag_is_idle = True

            moving_factor = _smoothstep(enter, exit_speed, self._drag_speed_smoothed)
            target_idle = 1.0 - moving_factor
            if self._drag_is_idle:
                target_idle = max(target_idle, 0.60)

            idle_tau = max(1e-6, self.drag_idle_influence_smoothing_seconds)
            idle_alpha = 1.0 - math.exp(-(self.time_step / idle_tau))
            self._drag_idle_influence += (target_idle - self._drag_idle_influence) * idle_alpha
            self._drag_idle_influence = max(0.0, min(1.0, self._drag_idle_influence))
            drag_idle_influence = self._drag_idle_influence

            if self._drag_idle_influence > 0.92:
                self._drag_motion_started = False
                self._drag_start_handover_active = False
                self._drag_start_handover_elapsed = 0.0
                self._drag_start_blend = 0.0

            self._motion_strength *= (0.96 - (0.10 * self._drag_idle_influence))

        boost = 1.0
        damping_scale = 1.0
        if not self.dragging:
            boost = max(boost, self.settle_spring_boost)
            damping_scale = min(damping_scale, self.settle_damping_scale)
        else:
            boost = 1.0 + ((self.settle_spring_boost - 1.0) * drag_idle_influence)
            damping_scale = 1.0 + ((self.settle_damping_scale - 1.0) * drag_idle_influence)

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
            scale = self.max_disp_mag / disp_mag
            self._disp[0] *= scale
            self._disp[1] *= scale
            self._vel[0] *= scale
            self._vel[1] *= scale

        if not self.dragging:
            self._settle_elapsed += self.time_step
            self._settle_steps += 1
            vel_mag = math.hypot(self._vel[0], self._vel[1])
            if disp_mag < self.settle_epsilon and vel_mag < self.settle_epsilon:
                self.active = False
                return
            if self._settle_elapsed >= self.release_hard_limit_seconds:
                self._disp[0] = 0.0
                self._disp[1] = 0.0
                self._vel[0] = 0.0
                self._vel[1] = 0.0
                self.active = False
                return
            if (
                self._settle_steps > self._settle_max_steps
                or self._settle_elapsed > self.settle_timeout_seconds
            ):
                self.active = False

    def render(self, surface, theme=None, draw_window_standard=None):
        if not self.active:
            return

        if draw_window_standard is not None and theme is not None:
            if self.buffer is None or self.dragging:
                self._refresh_buffer(surface, theme, draw_window_standard)
        if self.buffer is None:
            return

        if self._release_frame_pending:
            # Render one frame at exact mouse-up geometry before integrating settle.
            self._release_frame_pending = False
        else:
            substeps = max(1, self.simulation_substeps)
            for _ in range(substeps):
                self._step_settle()

        base_x, base_y = self.window.rect.topleft
        w, h = self.window.rect.size
        if w <= 0 or h <= 0:
            return

        disp_mag = min(self.max_distort_px, math.hypot(self._disp[0], self._disp[1]))

        if disp_mag < 0.001:
            surface.blit(self.buffer, (base_x, base_y))
            return

        tile_h = max(2, self.band_height)
        tile_w = max(2, self.tile_width)
        overlap_px = max(0, self.overlap_px)
        dir_x = self._shear_dir_x
        anchor_y = float(self.anchor[1] if self.anchor is not None else (h * 0.5))
        horizontal_weight = min(1.0, abs(dir_x) * self.shear_horizontal_emphasis)
        shear_sign_x = -1.0 if dir_x >= 0.0 else 1.0
        release_blend = 1.0
        if not self.dragging and self._settle_blend_seconds > 1e-6:
            release_t = min(1.0, max(0.0, self._settle_elapsed / self._settle_blend_seconds))
            smooth = (release_t * release_t) * (3.0 - (2.0 * release_t))
            release_blend = 1.0 - smooth

        if self.dragging:
            drag_idle_settle_blend = max(0.0, min(1.0, 1.0 - self._drag_idle_influence))
        else:
            drag_idle_settle_blend = max(0.0, min(1.0, 1.0 - self._release_idle_influence))
        if self.dragging:
            drag_start_blend = self._drag_start_blend
            drag_handover_blend = drag_start_blend * drag_idle_settle_blend
            self._last_drag_frame_valid = True
            self._last_drag_shear_dir_x = dir_x
            self._last_drag_shear_blend = max(0.0, min(1.0, drag_handover_blend))
        else:
            drag_handover_blend = self._release_drag_shear_blend
        shear_release_blend = math.sqrt(release_blend) if not self.dragging else 1.0

        for y in range(0, h, tile_h):
            for x in range(0, w, tile_w):
                src_w = min(tile_w, w - x)
                src_h = min(tile_h, h - y)
                if src_w <= 0 or src_h <= 0:
                    continue

                center_y = float(y + (src_h * 0.5))
                vertical_offset = (center_y - anchor_y) / max(1.0, float(h))
                shear_distance_boost = self.shear_distance_boost_px * drag_idle_settle_blend
                shear_x = (
                    (disp_mag * self.shear_gain) + shear_distance_boost
                ) * vertical_offset * horizontal_weight * shear_sign_x * (0.80 + (0.20 * self._motion_strength))
                shear_x *= shear_release_blend * drag_handover_blend
                off_x = int(max(-self.max_distort_px, min(self.max_distort_px, shear_x)))

                sx = max(0, x - overlap_px)
                sy = max(0, y - overlap_px)
                ex = min(w, x + src_w + overlap_px)
                ey = min(h, y + src_h + overlap_px)
                src = pygame.Rect(sx, sy, ex - sx, ey - sy)
                surface.blit(self.buffer, (base_x + sx + off_x, base_y + sy), src)
