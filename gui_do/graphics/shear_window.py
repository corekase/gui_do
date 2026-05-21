"""Shear-only window drag renderer for pygame-backed windows."""

from __future__ import annotations

import math
from time import perf_counter
from typing import Any, Optional

import pygame


class ShearWindowController:
    """Applies a horizontal shear deformation while dragging a window titlebar."""

    _pool_buffer: Optional[pygame.Surface] = None
    _pool_buffer_size: tuple[int, int] = (0, 0)
    _pool_scratch: Optional[pygame.Surface] = None
    _pool_scratch_size: tuple[int, int] = (0, 0)
    _pool_refcount: int = 0

    def __init__(self, window: Any):
        self.window = window

        self.active = False
        self.dragging = False
        self.anchor: Optional[tuple[int, int]] = None
        self._prev_mouse_pos: Optional[tuple[int, int]] = None

        self._pool_acquired = False
        self._acquire_surface_pool()
        self._tile_cache_key: tuple[int, int, int, int] | None = None
        self._tile_rows: list[tuple[int, int, float]] = []
        self._tile_cols: list[tuple[int, int]] = []

        # Automatic quality scaling keeps shear responsive on slower hardware
        # while preserving high-fidelity deformation on faster systems.
        self._auto_quality_level = 0  # 0=high, 1=balanced, 2=performance
        self._auto_quality_hold_frames = 0
        self._auto_render_ms_ema: Optional[float] = None
        self._auto_render_ema_alpha = 0.22
        self._auto_degrade_threshold_ms = (2.2, 3.4)
        self._auto_upgrade_threshold_ms = (0.0, 1.4, 2.3)
        self._auto_hold_degrade_frames = 8
        self._auto_hold_upgrade_frames = 30

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
        self.band_height = 10
        self.tile_width = 16
        self.overlap_px = 4
        self.surface_growth_factor = 1.5

        self.time_step = 1.0 / 120.0
        self.simulation_substeps = 3
        self.spring_k = 62.0
        self.damping = 0.60
        self.drag_coupling = 0.78
        self.max_impulse = 128.0
        self.max_velocity = 300.0
        self.max_disp_mag = 108.0
        self.max_distort_px = 96.0

        self.shear_gain = 3.5
        self.shear_horizontal_emphasis = 1.7
        self.shear_distance_boost_px = 40.0

        self.drag_idle_speed_threshold = 1.10
        self.drag_idle_speed_enter = self.drag_idle_speed_threshold
        self.drag_idle_speed_exit = self.drag_idle_speed_enter * 1.35
        self.drag_speed_smoothing_seconds = 0.050
        self.drag_idle_influence_smoothing_seconds = 0.080
        self.drag_direction_handover_seconds = 0.06
        self.drag_start_handover_seconds = 0.07
        self.drag_idle_settle_delay_seconds = 0.07

        self.settle_timeout_seconds = 0.22
        self.settle_hard_limit_seconds = 0.12
        self.release_blend_seconds = 0.16
        self.release_hard_limit_seconds = 0.24
        self._settle_blend_seconds = max(1e-6, min(self.release_blend_seconds, self.release_hard_limit_seconds))
        self.settle_spring_boost = 2.35
        self.settle_damping_scale = 0.74
        self.settle_target_fps = 120.0
        self.settle_epsilon = 0.12
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

    @property
    def buffer(self) -> Optional[pygame.Surface]:
        return type(self)._pool_buffer

    @buffer.setter
    def buffer(self, value: Optional[pygame.Surface]) -> None:
        type(self)._pool_buffer = value

    @property
    def _buffer_size(self) -> tuple[int, int]:
        return type(self)._pool_buffer_size

    @_buffer_size.setter
    def _buffer_size(self, value: tuple[int, int]) -> None:
        type(self)._pool_buffer_size = value

    @property
    def _scratch(self) -> Optional[pygame.Surface]:
        return type(self)._pool_scratch

    @_scratch.setter
    def _scratch(self, value: Optional[pygame.Surface]) -> None:
        type(self)._pool_scratch = value

    @property
    def _scratch_size(self) -> tuple[int, int]:
        return type(self)._pool_scratch_size

    @_scratch_size.setter
    def _scratch_size(self, value: tuple[int, int]) -> None:
        type(self)._pool_scratch_size = value

    def _acquire_surface_pool(self) -> None:
        if self._pool_acquired:
            return
        type(self)._pool_refcount += 1
        self._pool_acquired = True

    def _release_surface_pool(self) -> None:
        if not self._pool_acquired:
            return

        cls = type(self)
        if cls._pool_refcount > 0:
            cls._pool_refcount -= 1
        self._pool_acquired = False

        if cls._pool_refcount > 0:
            return

        old_buffer = cls._pool_buffer
        old_scratch = cls._pool_scratch
        cls._pool_buffer = None
        cls._pool_buffer_size = (0, 0)
        cls._pool_scratch = None
        cls._pool_scratch_size = (0, 0)
        del old_buffer
        del old_scratch

    @staticmethod
    def _smoothstep(edge0: float, edge1: float, value: float) -> float:
        if edge1 <= edge0:
            return 1.0 if value >= edge1 else 0.0
        t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
        return t * t * (3.0 - (2.0 * t))

    def _ensure_tile_cache(self, w: int, h: int, tile_w: int, tile_h: int) -> None:
        key = (w, h, tile_w, tile_h)
        if self._tile_cache_key == key:
            return

        self._tile_cache_key = key
        self._tile_rows = []
        self._tile_cols = []

        inv_h = 1.0 / max(1.0, float(h))
        for y in range(0, h, tile_h):
            src_h = min(tile_h, h - y)
            center_ratio = float(y + (src_h * 0.5)) * inv_h
            self._tile_rows.append((y, src_h, center_ratio))

        for x in range(0, w, tile_w):
            src_w = min(tile_w, w - x)
            self._tile_cols.append((x, src_w))

    def _current_quality_params(self) -> tuple[int, int, int, int]:
        level = self._auto_quality_level
        if level <= 0:
            return (
                max(2, int(self.band_height)),
                max(2, int(self.tile_width)),
                max(0, int(self.overlap_px)),
                max(1, int(self.simulation_substeps)),
            )
        if level == 1:
            return (
                max(2, int(round(self.band_height * 1.2))),
                max(2, int(round(self.tile_width * 1.25))),
                max(1, int(self.overlap_px) - 1),
                max(1, int(self.simulation_substeps) - 1),
            )
        return (
            max(2, int(round(self.band_height * 1.4))),
            max(2, int(round(self.tile_width * 1.5))),
            max(1, int(self.overlap_px) - 2),
            1,
        )

    @staticmethod
    def _surface_can_fit(capacity: tuple[int, int], needed: tuple[int, int]) -> bool:
        return capacity[0] >= needed[0] and capacity[1] >= needed[1]

    def _expanded_surface_size(self, needed: tuple[int, int]) -> tuple[int, int]:
        growth = max(1.0, float(self.surface_growth_factor))
        width = max(1, int(math.ceil(float(needed[0]) * growth)))
        height = max(1, int(math.ceil(float(needed[1]) * growth)))
        return width, height

    @staticmethod
    def _replace_surface(
        current: Optional[pygame.Surface],
        allocated: tuple[int, int],
    ) -> pygame.Surface:
        # Explicitly drop the previous surface reference as soon as the enlarged
        # surface is installed so lifecycle ownership is unambiguous.
        old_surface = current
        current = pygame.Surface(allocated, pygame.SRCALPHA)
        del old_surface
        return current

    def _ensure_buffer_capacity(self, needed: tuple[int, int]) -> None:
        if self.buffer is None or not self._surface_can_fit(self._buffer_size, needed):
            allocated = self._expanded_surface_size(needed)
            self.buffer = self._replace_surface(self.buffer, allocated)
            self._buffer_size = allocated

    def _ensure_scratch_capacity(self, needed: tuple[int, int]) -> None:
        if self._scratch is None or not self._surface_can_fit(self._scratch_size, needed):
            allocated = self._expanded_surface_size(needed)
            self._scratch = self._replace_surface(self._scratch, allocated)
            self._scratch_size = allocated

    def dispose(self) -> None:
        self.active = False
        self.dragging = False
        self._release_surface_pool()
        self._tile_cache_key = None
        self._tile_rows = []
        self._tile_cols = []

    def _update_auto_quality(self, render_ms: float) -> None:
        if render_ms <= 0.0:
            return

        if self._auto_render_ms_ema is None:
            self._auto_render_ms_ema = render_ms
        else:
            alpha = max(0.01, min(1.0, self._auto_render_ema_alpha))
            self._auto_render_ms_ema += (render_ms - self._auto_render_ms_ema) * alpha

        ema = self._auto_render_ms_ema
        if ema is None:
            return

        if self._auto_quality_hold_frames > 0:
            self._auto_quality_hold_frames -= 1
            return

        level = self._auto_quality_level
        if level < 2 and ema > self._auto_degrade_threshold_ms[level]:
            self._auto_quality_level = level + 1
            self._auto_quality_hold_frames = self._auto_hold_degrade_frames
            self._tile_cache_key = None
            return

        if level > 0 and ema < self._auto_upgrade_threshold_ms[level]:
            self._auto_quality_level = level - 1
            self._auto_quality_hold_frames = self._auto_hold_upgrade_frames
            self._tile_cache_key = None

    def _scaled_quality_for_window(
        self,
        w: int,
        h: int,
        tile_h: int,
        tile_w: int,
        overlap_px: int,
    ) -> tuple[int, int, int]:
        area = max(1, int(w) * int(h))
        if area < 120_000:
            return tile_h, tile_w, overlap_px

        level = max(0, min(2, int(self._auto_quality_level)))
        if area < 220_000:
            tier = 0
        elif area < 360_000:
            tier = 1
        else:
            tier = 2

        band_scale = (
            (0.96, 0.90, 0.84),
            (1.00, 0.95, 0.90),
            (1.02, 0.98, 0.94),
        )[level][tier]
        width_scale = (
            (1.18, 1.34, 1.52),
            (1.24, 1.42, 1.62),
            (1.34, 1.56, 1.78),
        )[level][tier]
        overlap_drop = (1, 1, 2)[tier]

        scaled_tile_h = max(2, int(round(tile_h * band_scale)))
        scaled_tile_w = max(2, int(round(tile_w * width_scale)))

        # Keep enough vertical rows on large windows to limit visible striping.
        min_rows_target = (52, 44, 36)[level]
        max_tile_h_for_rows = max(2, int(math.ceil(float(h) / float(min_rows_target))))
        scaled_tile_h = min(scaled_tile_h, max_tile_h_for_rows)

        return (
            scaled_tile_h,
            scaled_tile_w,
            max(0, overlap_px - overlap_drop),
        )

    def _should_use_per_pixel_shear(self, h: int, tile_h: int, max_shear_extent: int, area: int) -> bool:
        # Per-pixel rows are visually smoother for short windows under strong shear,
        # but are significantly more expensive. Keep them for small/high-quality cases only.
        if area >= 160_000:
            return False
        if self._auto_quality_level > 0:
            return False
        num_bands = max(1, h // max(1, tile_h))
        distort_per_band = float(max_shear_extent) / float(max(1, num_bands))
        return h <= 240 and distort_per_band > 2.0

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

        self._tile_cache_key = None
        self._tile_rows = []
        self._tile_cols = []
        if surface is not None:
            rect = self.window.rect.clip(surface.get_rect())
            if rect.width > 0 and rect.height > 0 and rect.size == self.window.rect.size:
                needed = self.window.rect.size
                self._ensure_buffer_capacity(needed)
                assert self.buffer is not None
                self.buffer.fill((0, 0, 0, 0), pygame.Rect(0, 0, needed[0], needed[1]))
                self.buffer.blit(surface, (0, 0), self.window.rect)

    def update_drag(self, mouse_pos, *, blocked: bool = False):
        if not self.active or not self.dragging:
            return
        wx, wy = self.window.rect.topleft
        self.anchor = (int(mouse_pos[0] - wx), int(mouse_pos[1] - wy))

        if blocked:
            speed_tau = max(1e-6, self.drag_speed_smoothing_seconds)
            speed_decay = math.exp(-(self.time_step / speed_tau))
            self._drag_speed_smoothed *= speed_decay
            self._motion_strength *= 0.86
            self._prev_mouse_pos = mouse_pos
            return

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

    def end_drag(self, mouse_pos: Optional[tuple[int, int]] = None, *, blocked: bool = False):
        if mouse_pos is not None and self.active and self.dragging:
            # Fold the release-point mouse sample into drag state so settle starts
            # from the exact final direction/velocity envelope.
            self.update_drag(mouse_pos, blocked=blocked)
        elif mouse_pos is not None:
            wx, wy = self.window.rect.topleft
            self.anchor = (int(mouse_pos[0] - wx), int(mouse_pos[1] - wy))

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
        self.buffer.fill((0, 0, 0, 0), pygame.Rect(0, 0, window_rect.width, window_rect.height))

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
        self._ensure_buffer_capacity(window_rect.size)
        assert self.buffer is not None
        needed_buffer_rect = pygame.Rect(0, 0, window_rect.width, window_rect.height)

        surface_rect = surface.get_rect()
        clip = window_rect.clip(surface_rect)

        # If any part of the window is offscreen, render to a local buffer so
        # uncovered pixels do not become transparent/black in the shear pass.
        if clip.size != window_rect.size:
            self._draw_window_local_buffer(theme, draw_window_standard, window_rect)
            return

        size = surface.get_size()
        self._ensure_scratch_capacity(size)

        scratch = self._scratch
        assert scratch is not None
        scratch.fill((0, 0, 0, 0), window_rect)
        draw_window_standard(scratch, theme)
        self.buffer.fill((0, 0, 0, 0), needed_buffer_rect)

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

            moving_factor = self._smoothstep(enter, exit_speed, self._drag_speed_smoothed)
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

    def _compute_drag_blends(self, dir_x: float, *, capture_drag_frame: bool) -> tuple[float, float]:
        if self.dragging:
            drag_idle_settle_blend = max(0.0, min(1.0, 1.0 - self._drag_idle_influence))
            drag_start_blend = self._drag_start_blend
            drag_handover_blend = max(0.0, min(1.0, drag_start_blend * drag_idle_settle_blend))
            if capture_drag_frame:
                self._last_drag_frame_valid = True
                self._last_drag_shear_dir_x = dir_x
                self._last_drag_shear_blend = drag_handover_blend
            return drag_idle_settle_blend, drag_handover_blend

        drag_idle_settle_blend = max(0.0, min(1.0, 1.0 - self._release_idle_influence))
        drag_handover_blend = max(0.0, min(1.0, self._release_drag_shear_blend))
        return drag_idle_settle_blend, drag_handover_blend

    def _current_shear_factors(self, w: int, h: int, *, capture_drag_frame: bool) -> Optional[tuple[float, float, float, float, float, float, float]]:
        disp_mag = min(self.max_distort_px, math.hypot(self._disp[0], self._disp[1]))
        if disp_mag < 0.001:
            return None

        dir_x = self._shear_dir_x
        anchor_y = float(self.anchor[1] if self.anchor is not None else (h * 0.5))
        horizontal_weight = min(1.0, abs(dir_x) * self.shear_horizontal_emphasis)
        shear_sign_x = -1.0 if dir_x >= 0.0 else 1.0

        release_blend = 1.0
        if not self.dragging and self._settle_blend_seconds > 1e-6:
            release_t = min(1.0, max(0.0, self._settle_elapsed / self._settle_blend_seconds))
            smooth = (release_t * release_t) * (3.0 - (2.0 * release_t))
            release_blend = 1.0 - smooth
        shear_release_blend = math.sqrt(release_blend) if not self.dragging else 1.0

        drag_idle_settle_blend, drag_handover_blend = self._compute_drag_blends(
            dir_x,
            capture_drag_frame=capture_drag_frame,
        )
        return (
            disp_mag,
            anchor_y,
            horizontal_weight,
            shear_sign_x,
            drag_idle_settle_blend,
            shear_release_blend,
            drag_handover_blend,
        )

    def _blit_sheared_source(
        self,
        surface: pygame.Surface,
        source: pygame.Surface,
        base_x: int,
        base_y: int,
        w: int,
        h: int,
        disp_mag: float,
        anchor_y: float,
        horizontal_weight: float,
        shear_sign_x: float,
        drag_idle_settle_blend: float,
        shear_release_blend: float,
        drag_handover_blend: float,
        local_bounds: Optional[pygame.Rect] = None,
    ) -> None:
        tile_h, tile_w, overlap_px, _ = self._current_quality_params()
        tile_h, tile_w, overlap_px = self._scaled_quality_for_window(w, h, tile_h, tile_w, overlap_px)
        self._ensure_tile_cache(w, h, tile_w, tile_h)

        x_start = 0
        y_start = 0
        x_end = w
        y_end = h
        if local_bounds is not None:
            clipped = local_bounds.clip(pygame.Rect(0, 0, w, h))
            if clipped.width <= 0 or clipped.height <= 0:
                return
            x_start = max(0, (clipped.left // tile_w) * tile_w)
            y_start = max(0, (clipped.top // tile_h) * tile_h)
            x_end = min(w, ((clipped.right + tile_w - 1) // tile_w) * tile_w)
            y_end = min(h, ((clipped.bottom + tile_h - 1) // tile_h) * tile_h)

        anchor_ratio = float(anchor_y) / max(1.0, float(h))
        shear_distance_boost = self.shear_distance_boost_px * drag_idle_settle_blend
        shear_common = (
            ((disp_mag * self.shear_gain) + shear_distance_boost)
            * horizontal_weight
            * shear_sign_x
            * (0.80 + (0.20 * self._motion_strength))
            * shear_release_blend
            * drag_handover_blend
        )
        max_distort = self.max_distort_px

        area = max(1, int(w) * int(h))
        max_shear_extent = min(max_distort, abs(int(shear_common)))
        use_per_pixel = self._should_use_per_pixel_shear(h, tile_h, max_shear_extent, area)

        # If the window is too short for smooth bands, use per-pixel vertical lines
        if use_per_pixel:
            # Per-pixel vertical lines for smoothest effect
            for y in range(y_start, y_end):
                vertical_offset = (float(y) + 0.5) / max(1.0, float(h)) - anchor_ratio
                shear_x = shear_common * vertical_offset
                off_x = int(max(-max_distort, min(max_distort, shear_x)))
                # Blit a single horizontal line
                for x, src_w in self._tile_cols:
                    if x < x_start or x >= x_end:
                        continue
                    sx = max(0, x - overlap_px)
                    ex = min(w, x + src_w + overlap_px)
                    blit_w = ex - sx
                    if blit_w <= 0:
                        continue
                    surface.blit(
                        source,
                        (base_x + sx + off_x, base_y + y),
                        (sx, y, blit_w, 1),
                    )
        else:
            # Default banded approach for tall windows
            for y, src_h, center_ratio in self._tile_rows:
                if y < y_start or y >= y_end:
                    continue

                vertical_offset = center_ratio - anchor_ratio
                shear_x = shear_common * vertical_offset
                off_x = int(max(-max_distort, min(max_distort, shear_x)))

                sy = max(0, y - overlap_px)
                ey = min(h, y + src_h + overlap_px)
                blit_h = ey - sy
                if blit_h <= 0:
                    continue

                for x, src_w in self._tile_cols:
                    if x < x_start or x >= x_end:
                        continue

                    sx = max(0, x - overlap_px)
                    ex = min(w, x + src_w + overlap_px)
                    blit_w = ex - sx
                    if blit_w <= 0:
                        continue
                    surface.blit(
                        source,
                        (base_x + sx + off_x, base_y + sy),
                        (sx, sy, blit_w, blit_h),
                    )

    def blit_sheared_overlay(
        self,
        surface: pygame.Surface,
        overlay: pygame.Surface,
        local_bounds: Optional[pygame.Rect] = None,
    ) -> bool:
        if not self.active:
            return False

        base_x, base_y = self.window.rect.topleft
        w, h = self.window.rect.size
        if w <= 0 or h <= 0:
            return False
        if overlay.get_size() != (w, h):
            return False

        factors = self._current_shear_factors(w, h, capture_drag_frame=False)
        if factors is None:
            surface.blit(overlay, (base_x, base_y))
            return True

        self._blit_sheared_source(
            surface,
            overlay,
            base_x,
            base_y,
            w,
            h,
            *factors,
            local_bounds=local_bounds,
        )
        return True

    def render(self, surface, theme=None, draw_window_standard=None):
        if not self.active:
            return

        render_start = perf_counter()

        if draw_window_standard is not None and theme is not None:
            # Keep the source buffer live during settle so child content keeps
            # updating and release work stays in the normal frame pass.
            self._refresh_buffer(surface, theme, draw_window_standard)
        if self.buffer is None:
            return

        if self._release_frame_pending:
            # Render one frame at exact mouse-up geometry before integrating settle.
            self._release_frame_pending = False
        else:
            _, _, _, substeps = self._current_quality_params()
            for _ in range(substeps):
                self._step_settle()

        base_x, base_y = self.window.rect.topleft
        w, h = self.window.rect.size
        if w <= 0 or h <= 0:
            return

        factors = self._current_shear_factors(w, h, capture_drag_frame=True)
        if factors is None:
            surface.blit(self.buffer, (base_x, base_y), pygame.Rect(0, 0, w, h))
            self._update_auto_quality((perf_counter() - render_start) * 1000.0)
            return

        self._blit_sheared_source(surface, self.buffer, base_x, base_y, w, h, *factors)
        self._update_auto_quality((perf_counter() - render_start) * 1000.0)
