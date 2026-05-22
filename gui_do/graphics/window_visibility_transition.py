from __future__ import annotations

from typing import Any, Optional

import pygame

from ..app.screen_util import get_screen_size
from ..layout.window_layout_handler import WINDOW_TILING_ANIMATION_DURATION_SECONDS
from .window_effect_scratch_pad import WindowEffectScratchPad


class WindowVisibilityTransitionController:
    """Animate window hide/show using a shared promoted surface pool.

    The controller captures a fresh local snapshot every frame so live window
    content can continue updating during the transition.
    """

    _BUFFER_SLOT = "window_effect_buffer"
    _SCALED_SLOT = "window_effect_visibility_scaled"

    def __init__(self, window: Any) -> None:
        self.window = window
        self.base_duration_seconds = WINDOW_TILING_ANIMATION_DURATION_SECONDS
        self._pool_acquired = False
        self._acquire_surface_pool()

        initial_progress = 1.0 if bool(getattr(window, "visible", True)) else 0.0
        self._active = False
        self._start_progress = initial_progress
        self._target_progress = initial_progress
        self._elapsed_seconds = 0.0
        self._duration_seconds = 0.0
        self._start_center = (0.0, 0.0)
        self._target_center = (0.0, 0.0)
        self._render_size = (1, 1)
        self._track_window_tiling_target = False
        self._transition_mode = "hide_show"
        self._post_transition_tile_app = None
        self._post_transition_tile_pending = False

    @property
    def buffer(self) -> Optional[pygame.Surface]:
        return WindowEffectScratchPad.get_surface(self._BUFFER_SLOT)

    @buffer.setter
    def buffer(self, value: Optional[pygame.Surface]) -> None:
        WindowEffectScratchPad.set_surface(self._BUFFER_SLOT, value)

    @property
    def _buffer_size(self) -> tuple[int, int]:
        return WindowEffectScratchPad.get_size(self._BUFFER_SLOT)

    @property
    def scaled_buffer(self) -> Optional[pygame.Surface]:
        return WindowEffectScratchPad.get_surface(self._SCALED_SLOT)

    @scaled_buffer.setter
    def scaled_buffer(self, value: Optional[pygame.Surface]) -> None:
        WindowEffectScratchPad.set_surface(self._SCALED_SLOT, value)

    @property
    def _scaled_size(self) -> tuple[int, int]:
        return WindowEffectScratchPad.get_size(self._SCALED_SLOT)

    def _acquire_surface_pool(self) -> None:
        if self._pool_acquired:
            return
        WindowEffectScratchPad.acquire()
        self._pool_acquired = True

    def _release_surface_pool(self) -> None:
        if not self._pool_acquired:
            return
        WindowEffectScratchPad.release()
        self._pool_acquired = False

    @classmethod
    def dispose_shared_pool(cls) -> None:
        WindowEffectScratchPad.dispose_all()

    @staticmethod
    def _smoothstep(value: float) -> float:
        t = max(0.0, min(1.0, float(value)))
        return t * t * (3.0 - (2.0 * t))

    def is_active(self) -> bool:
        return bool(self._active)

    def progress(self) -> float:
        if not self._active or self._duration_seconds <= 1e-9:
            return float(self._target_progress)
        blend = self._smoothstep(self._elapsed_seconds / self._duration_seconds)
        return self._start_progress + ((self._target_progress - self._start_progress) * blend)

    def should_render(self) -> bool:
        if self._active:
            return True
        if bool(getattr(self.window, "visible", False)):
            return False
        return self.progress() > 1e-3

    def _current_center(self) -> tuple[float, float]:
        target_center = self._resolved_target_center()
        if not self._active or self._duration_seconds <= 1e-9:
            return target_center
        blend = self._smoothstep(self._elapsed_seconds / self._duration_seconds)
        return (
            self._start_center[0] + ((target_center[0] - self._start_center[0]) * blend),
            self._start_center[1] + ((target_center[1] - self._start_center[1]) * blend),
        )

    def _resolved_window_tiling_target_center(self) -> Optional[tuple[float, float]]:
        rect = getattr(self.window, "_window_tiling_target_rect", None)
        if isinstance(rect, pygame.Rect):
            return (float(rect.centerx), float(rect.centery))
        return None

    def _resolved_target_center(self) -> tuple[float, float]:
        if self._track_window_tiling_target:
            target = self._resolved_window_tiling_target_center()
            if target is not None:
                return target
            return tuple(map(float, pygame.Rect(self.window.rect).center))
        return self._target_center

    @staticmethod
    def _resolve_anchor_rect(app, binding) -> Optional[pygame.Rect]:
        if app is None or binding is None:
            return None
        control_id = str(getattr(binding, "task_panel_toggle_button_id", "")).strip()
        if not control_id:
            return None
        find = getattr(app, "find", None)
        if not callable(find):
            return None
        node = find(control_id)
        rect = getattr(node, "rect", None)
        if not isinstance(rect, pygame.Rect):
            return None
        return pygame.Rect(rect)

    @staticmethod
    def _resolve_screen_bottom(app) -> float:
        surface = getattr(app, "surface", None) if app is not None else None
        get_size = getattr(surface, "get_size", None)
        if callable(get_size):
            try:
                _width, height = get_size()
                return float(height)
            except Exception:
                pass
        _width, height = get_screen_size()
        return float(height)

    def begin_transition(self, visible: bool, *, app=None, binding=None, mode: str = "hide_show") -> None:
        target_progress = 1.0 if bool(visible) else 0.0
        transition_mode = str(mode).strip().lower()
        if transition_mode not in {"hide_show", "grow_shrink"}:
            transition_mode = "hide_show"
        self._transition_mode = transition_mode
        current_progress = self.progress()
        current_center = self._current_center() if self._active else tuple(map(float, pygame.Rect(self.window.rect).center))
        current_rect = pygame.Rect(self.window.rect)
        target_center = tuple(map(float, current_rect.center))
        if transition_mode == "grow_shrink":
            start_center = current_center
            self._track_window_tiling_target = False
        else:
            target_center_rect = self._resolve_anchor_rect(app, binding)
            if bool(visible):
                target_center = self._resolved_window_tiling_target_center() or tuple(map(float, current_rect.center))
                start_center = tuple(map(float, target_center_rect.center)) if target_center_rect is not None else target_center
                if self._active:
                    start_center = current_center
                self._track_window_tiling_target = True
            else:
                start_center = current_center
                self._track_window_tiling_target = False
                if target_center_rect is not None:
                    target_center = (
                        float(target_center_rect.centerx),
                        self._resolve_screen_bottom(app),
                    )

        duration = self.base_duration_seconds
        if self._active:
            reversing = abs(target_progress - self._target_progress) > 1e-6
            if reversing:
                # Reverse timing uses elapsed time (inverse of remaining) so a
                # near-complete leg does not snap back unnaturally fast.
                duration = self._elapsed_seconds
            else:
                duration = self._duration_seconds - self._elapsed_seconds
        if duration <= 1e-6:
            duration = self.base_duration_seconds

        self._render_size = (max(1, int(current_rect.width)), max(1, int(current_rect.height)))
        self._start_progress = float(current_progress)
        self._target_progress = float(target_progress)
        self._start_center = (float(start_center[0]), float(start_center[1]))
        self._target_center = (float(target_center[0]), float(target_center[1]))
        self._elapsed_seconds = 0.0
        self._duration_seconds = float(duration)
        self._active = abs(self._target_progress - self._start_progress) > 1e-6
        tile_windows = getattr(app, "tile_windows", None) if app is not None else None
        if callable(tile_windows):
            self._post_transition_tile_app = app
            self._post_transition_tile_pending = True
        else:
            self._post_transition_tile_app = None
            self._post_transition_tile_pending = False

    def _issue_post_transition_tile(self) -> None:
        if not self._post_transition_tile_pending:
            return
        app = self._post_transition_tile_app
        self._post_transition_tile_pending = False
        self._post_transition_tile_app = None
        tile_windows = getattr(app, "tile_windows", None) if app is not None else None
        if not callable(tile_windows):
            return
        is_show = self._target_progress >= 0.5
        try:
            if is_show:
                tile_windows(newly_visible=(self.window,), as_visibility_event=True)
            else:
                tile_windows()
        except TypeError:
            tile_windows()

    def update(self, dt_seconds: float) -> None:
        if not self._active:
            return
        self._elapsed_seconds = min(self._duration_seconds, self._elapsed_seconds + max(0.0, float(dt_seconds)))
        if self._elapsed_seconds + 1e-9 < self._duration_seconds:
            return
        self._elapsed_seconds = self._duration_seconds
        self._start_progress = self._target_progress
        self._start_center = self._resolved_target_center()
        self._active = False
        self._issue_post_transition_tile()

    def _ensure_buffer_capacity(self, size: tuple[int, int]) -> None:
        WindowEffectScratchPad.ensure_capacity(self._BUFFER_SLOT, size, growth_factor=1.5)

    def _ensure_scaled_capacity(self, size: tuple[int, int]) -> None:
        WindowEffectScratchPad.ensure_capacity(self._SCALED_SLOT, size, growth_factor=1.5)

    def _iter_control_subtree(self):
        root = self.window
        stack = [root]
        seen = set()
        while stack:
            node = stack.pop()
            marker = id(node)
            if marker in seen:
                continue
            seen.add(marker)
            yield node
            children = getattr(node, "children", None)
            if children:
                stack.extend(children)

    def _draw_window_local_buffer(self, theme, draw_window_standard) -> None:
        render_w, render_h = self._render_size
        self._ensure_buffer_capacity((render_w, render_h))
        assert self.buffer is not None

        self.buffer.fill((0, 0, 0, 0), pygame.Rect(0, 0, render_w, render_h))
        window_rect = pygame.Rect(self.window.rect)
        offset_x = -window_rect.left
        offset_y = -window_rect.top
        shifted: list[tuple[Any, pygame.Rect]] = []
        try:
            for control in self._iter_control_subtree():
                rect = getattr(control, "rect", None)
                if isinstance(rect, pygame.Rect):
                    original = rect.copy()
                    control.rect = rect.move(offset_x, offset_y)
                    shifted.append((control, original))
            draw_window_standard(self.buffer, theme)
        finally:
            for control, original in reversed(shifted):
                control.rect = original

    def render(self, surface: pygame.Surface, theme, draw_window_standard) -> None:
        progress = self.progress()
        if progress <= 1e-3:
            return

        render_w, render_h = self._render_size
        if render_w <= 0 or render_h <= 0:
            return

        self._draw_window_local_buffer(theme, draw_window_standard)
        assert self.buffer is not None

        scaled_w = max(1, int(round(render_w * progress)))
        scaled_h = max(1, int(round(render_h * progress)))
        self._ensure_scaled_capacity((scaled_w, scaled_h))
        assert self.scaled_buffer is not None

        target = self.scaled_buffer.subsurface(pygame.Rect(0, 0, scaled_w, scaled_h))
        pygame.transform.smoothscale(
            self.buffer.subsurface(pygame.Rect(0, 0, render_w, render_h)),
            (scaled_w, scaled_h),
            target,
        )
        target.set_alpha(max(0, min(255, int(round(255.0 * progress)))))

        center_x, center_y = self._current_center()
        draw_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
        draw_rect.center = (int(round(center_x)), int(round(center_y)))
        surface.blit(target, draw_rect.topleft)

    def dispose(self) -> None:
        self._active = False
        self._release_surface_pool()
