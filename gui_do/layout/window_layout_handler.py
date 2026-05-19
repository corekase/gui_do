from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List, Optional

from pygame import Rect


class WindowLayoutHandler:
    """Arrange window-like scene nodes into a non-overlapping tiled grid."""

    def __init__(self, app, scene=None) -> None:
        self.app = app
        self.scene = scene
        self.enabled = False
        self.gap = 16
        self.padding = 16
        self.avoid_task_panel = True
        self.center_on_failure = True
        self._registration_order: Dict[object, int] = {}
        self._next_order = 0

    def _bound_scene(self):
        if self.scene is not None:
            return self.scene
        return self.app.scene

    def _scene_windows(self) -> List[object]:
        windows: List[object] = []
        queue: deque = deque(self._bound_scene().nodes)
        while queue:
            node = queue.popleft()
            queue.extend(node.children)
            if self._is_window_like(node):
                windows.append(node)
        return windows

    @staticmethod
    def _is_window_like(node: object) -> bool:
        return node.is_window()

    def _ensure_registration(self, windows: Iterable[object]) -> None:
        current = set(windows)
        self._registration_order = {
            w: idx for w, idx in self._registration_order.items() if w in current
        }
        for window in windows:
            if window not in self._registration_order:
                self._registration_order[window] = self._next_order
                self._next_order += 1

    def prime_registration(self) -> None:
        """Register current scene windows without performing layout."""
        self._ensure_registration(self._scene_windows())

    def _visible_windows(self) -> List[object]:
        return self._ordered_windows(include_hidden=False)

    def _ordered_windows(self, *, include_hidden: bool) -> List[object]:
        windows = self._scene_windows()
        self._ensure_registration(windows)
        if include_hidden:
            ordered = list(windows)
        else:
            ordered = [w for w in windows if w.visible]
        ordered.sort(key=lambda w: self._registration_order[w])
        return ordered

    def visible_windows_snapshot(self) -> tuple[object, ...]:
        """Return current visible windows in registration order."""
        return tuple(self._visible_windows())

    def _work_area_rect(self) -> Rect:
        work = Rect(self.app.surface.get_rect())
        if self.avoid_task_panel:
            queue: deque = deque(self._bound_scene().nodes)
            while queue:
                node = queue.popleft()
                queue.extend(node.children)
                if node.is_task_panel() and node.visible:
                    panel_rect = node.rect
                    if panel_rect.top < work.bottom:
                        work.height = max(0, panel_rect.top - work.top)
                    break
        work.inflate_ip(-(self.padding * 2), -(self.padding * 2))
        return work

    def _fallback_clamp_target(self, window: object, target_x: int, target_y: int) -> tuple[int, int]:
        """Clamp one window target to visible screen bounds with menu-strip top exclusion."""
        rect = Rect(window.rect)
        surface = getattr(self.app, "surface", None)
        if surface is None:
            return (int(target_x), int(target_y))

        screen_rect = surface.get_rect()
        min_left = int(screen_rect.left)
        max_left = int(screen_rect.right - rect.width)
        top_limit = int(screen_rect.top)
        max_top = int(screen_rect.bottom - rect.height)

        # Match drag semantics: if a menu strip is present, windows cannot cross it.
        scene = self._bound_scene()
        queue: deque = deque(getattr(scene, "nodes", ()))
        while queue:
            node = queue.popleft()
            queue.extend(getattr(node, "children", ()))
            class_name = str(getattr(getattr(node, "__class__", object), "__name__", ""))
            if class_name == "MenuStripControl" and bool(getattr(node, "visible", False)) and bool(getattr(node, "enabled", False)):
                top_limit = max(top_limit, int(getattr(node, "rect", Rect(0, 0, 0, 0)).bottom))

        clamped_x = int(target_x)
        clamped_y = int(target_y)
        if max_left < min_left:
            clamped_x = min_left
        else:
            clamped_x = max(min_left, min(clamped_x, max_left))

        if max_top < top_limit:
            clamped_y = top_limit
        else:
            clamped_y = max(top_limit, min(clamped_y, max_top))
        return (int(clamped_x), int(clamped_y))

    def _clamp_target(self, window: object, target_x: int, target_y: int) -> tuple[int, int]:
        """Clamp target coordinates using the same logic as window drag bounds when available."""
        parent = getattr(window, "parent", None)
        clamp_fn = getattr(parent, "_clamp_window_drag_target", None)
        if callable(clamp_fn):
            try:
                x, y = clamp_fn(window, int(target_x), int(target_y), self.app)
                return (int(x), int(y))
            except Exception:
                pass
        return self._fallback_clamp_target(window, int(target_x), int(target_y))

    def _animate_window_to(self, window: object, target_x: int, target_y: int, *, duration: float) -> None:
        current = Rect(window.rect)
        if (current.x, current.y) == (int(target_x), int(target_y)):
            return

        tweens = getattr(self.app, "tweens", None)
        if tweens is None or not hasattr(tweens, "tween_fn"):
            window.move_by(int(target_x) - current.x, int(target_y) - current.y)
            return

        tag = f"window_tiling:{id(window)}"
        cancel_for_tag = getattr(tweens, "cancel_all_for_tag", None)
        if callable(cancel_for_tag):
            cancel_for_tag(tag)

        start_x = int(current.x)
        start_y = int(current.y)
        end_x = int(target_x)
        end_y = int(target_y)
        last_x = start_x
        last_y = start_y

        def _apply(t: float) -> None:
            nonlocal last_x, last_y
            next_x = int(round(start_x + ((end_x - start_x) * float(t))))
            next_y = int(round(start_y + ((end_y - start_y) * float(t))))
            dx = int(next_x - last_x)
            dy = int(next_y - last_y)
            if dx != 0 or dy != 0:
                window.move_by(dx, dy)
                last_x = next_x
                last_y = next_y

        tweens.tween_fn(float(duration), _apply, easing="ease_in_out", tag=tag)

    @staticmethod
    def _full_window_rect(window: object) -> Rect:
        rect = Rect(window.rect)
        return Rect(rect.x, rect.y, rect.width, rect.height)

    def _center_window(self, window: object, work_area: Optional[Rect] = None) -> None:
        bounds = Rect(self.app.surface.get_rect()) if work_area is None else Rect(work_area)
        rect = self._full_window_rect(window)
        target = Rect(0, 0, rect.width, rect.height)
        target.center = bounds.center
        current = Rect(window.rect)
        dx = target.x - current.x
        dy = target.y - current.y
        window.move_by(dx, dy)

    def set_enabled(self, enabled: bool, relayout: bool = True) -> None:
        self.enabled = bool(enabled)
        if relayout:
            self.arrange_windows()

    def configure(
        self,
        *,
        gap: Optional[int] = None,
        padding: Optional[int] = None,
        avoid_task_panel: Optional[bool] = None,
        center_on_failure: Optional[bool] = None,
        relayout: bool = True,
    ) -> None:
        if gap is not None:
            self.gap = max(0, int(gap))
        if padding is not None:
            self.padding = max(0, int(padding))
        if avoid_task_panel is not None:
            self.avoid_task_panel = bool(avoid_task_panel)
        if center_on_failure is not None:
            self.center_on_failure = bool(center_on_failure)
        if relayout:
            self.arrange_windows()

    def read_settings(self) -> Dict[str, object]:
        return {
            "enabled": self.enabled,
            "gap": self.gap,
            "padding": self.padding,
            "avoid_task_panel": self.avoid_task_panel,
            "center_on_failure": self.center_on_failure,
        }

    def arrange_windows(
        self,
        newly_visible: Optional[Iterable[object]] = None,
        *,
        include_hidden: bool = False,
        immediate: bool = False,
    ) -> None:
        windows = self._ordered_windows(include_hidden=bool(include_hidden))
        if not self.enabled or not windows:
            return
        work = self._work_area_rect()
        if work.width <= 0 or work.height <= 0:
            return
        if len(windows) == 1:
            only_window = windows[0]
            target = Rect(0, 0, only_window.rect.width, only_window.rect.height)
            target.center = work.center
            clamped_x, clamped_y = self._clamp_target(only_window, int(target.x), int(target.y))
            if immediate:
                current = Rect(only_window.rect)
                only_window.move_by(int(clamped_x) - current.x, int(clamped_y) - current.y)
            else:
                self._animate_window_to(only_window, int(clamped_x), int(clamped_y), duration=0.5)
            return

        order_idx = self._registration_order
        # Spatial preference order: preserve left/right first, then top/bottom,
        # with registration as a deterministic tie-breaker.
        visible_sorted = sorted(
            windows,
            key=lambda w: (
                int(getattr(w, "rect", Rect(0, 0, 0, 0)).x),
                int(getattr(w, "rect", Rect(0, 0, 0, 0)).y),
                int(order_idx.get(w, 0)),
            ),
        )

        window_rects = {w: self._full_window_rect(w) for w in visible_sorted}

        # Tight shelf packing: each row is only as tall as its tallest member;
        # x advances by each window width + gap (no max-cell inflation).
        rows: list[list[tuple[object, int, int]]] = []
        row: list[tuple[object, int, int]] = []
        row_width = 0
        row_height = 0
        used_height = 0
        overflow: list[object] = []

        for window in visible_sorted:
            wr = window_rects[window]
            ww = max(1, int(wr.width))
            wh = max(1, int(wr.height))
            add_w = ww if not row else (self.gap + ww)

            # New shelf when width would overflow current row.
            if row and (row_width + add_w > int(work.width)):
                if used_height + row_height > int(work.height):
                    overflow.extend(w for w, _ww, _wh in row)
                else:
                    rows.append(row)
                    used_height += row_height + self.gap
                row = []
                row_width = 0
                row_height = 0
                add_w = ww

            if row and (row_width + add_w > int(work.width)):
                overflow.append(window)
                continue

            next_row_h = max(row_height, wh)
            if used_height + next_row_h > int(work.height):
                overflow.append(window)
                continue

            row.append((window, ww, wh))
            row_width += add_w
            row_height = next_row_h

        if row:
            if used_height + row_height <= int(work.height):
                rows.append(row)
            else:
                overflow.extend(w for w, _ww, _wh in row)

        packed_w = 0
        packed_h = 0
        for idx, r in enumerate(rows):
            width_r = sum(item[1] for item in r) + (self.gap * max(0, len(r) - 1))
            height_r = max(item[2] for item in r) if r else 0
            packed_w = max(packed_w, width_r)
            packed_h += height_r
            if idx < len(rows) - 1:
                packed_h += self.gap

        packed_left = int(work.x + max(0, (int(work.width) - packed_w) // 2))
        packed_top = int(work.y + max(0, (int(work.height) - packed_h) // 2))

        targets: list[tuple[object, int, int]] = []
        cy = packed_top
        for r in rows:
            row_width = sum(item[1] for item in r) + (self.gap * max(0, len(r) - 1))
            row_height = max(item[2] for item in r) if r else 0
            cx = int(packed_left + max(0, (packed_w - row_width) // 2))
            for window, ww, _wh in r:
                targets.append((window, int(cx), int(cy)))
                cx += int(ww) + self.gap
            cy += int(row_height) + self.gap

        # Overflow windows: repeated cascades from top-left of packed area.
        if overflow:
            avg_w = max(1, int(sum(window_rects[w].width for w in overflow) / len(overflow)))
            avg_h = max(1, int(sum(window_rects[w].height for w in overflow) / len(overflow)))

            # Use one titlebar height as the shared diagonal cascade unit.
            # This applies equally to +x and +y for first overflow offset and stride.
            titlebar_height = max(14, int(getattr(overflow[0], "titlebar_height", 24)))
            step_x = int(titlebar_height)
            step_y = int(titlebar_height)
            initial_offset_x = int(step_x)
            initial_offset_y = int(step_y)

            # Keep cascade steps moderate and bounded by the work area.
            max_steps_x = max(
                0,
                (int(work.width) - max(1, avg_w) - initial_offset_x) // max(1, step_x),
            )
            max_steps_y = max(
                0,
                (int(work.height) - max(1, avg_h) - initial_offset_y) // max(1, step_y),
            )
            cascade_capacity = max(1, min(max_steps_x, max_steps_y) + 1)

            base_x = int(packed_left)
            base_y = int(packed_top)
            for idx, window in enumerate(overflow):
                step = int(idx % cascade_capacity)
                # After each cascade pass overflows, restart from top-left offset
                # and repeat the same cascade pattern.
                target_x = int(base_x + initial_offset_x + (step * step_x))
                target_y = int(base_y + initial_offset_y + (step * step_y))
                targets.append((window, target_x, target_y))

        # Clamp targets to drag-safe bounds, then animate to new positions.
        duration = 0.0 if immediate else 0.5
        for window, target_x, target_y in targets:
            clamped_x, clamped_y = self._clamp_target(window, int(target_x), int(target_y))
            if duration <= 0.0:
                current = Rect(window.rect)
                window.move_by(int(clamped_x) - current.x, int(clamped_y) - current.y)
            else:
                self._animate_window_to(window, clamped_x, clamped_y, duration=duration)

    def initialize_window_positions(self) -> None:
        """Seed scene window internal positions using immediate tiling targets."""
        self.arrange_windows(include_hidden=True, immediate=True)
