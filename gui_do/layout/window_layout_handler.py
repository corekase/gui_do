from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List, Optional

from pygame import Rect


WINDOW_TILING_ANIMATION_DURATION_SECONDS = 0.5


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

    def _scene_layout_snapshot(self) -> Dict[str, object]:
        """Capture one traversal of scene nodes for layout helper reuse."""
        windows: List[object] = []
        menu_bottom = 0
        task_panel_rect: Optional[Rect] = None
        scene = self._bound_scene()
        queue: deque = deque(getattr(scene, "nodes", ()))
        while queue:
            node = queue.popleft()
            queue.extend(getattr(node, "children", ()))

            if self._is_window_like(node):
                windows.append(node)

            class_name = str(getattr(getattr(node, "__class__", object), "__name__", ""))
            if class_name == "MenuStripControl" and bool(getattr(node, "visible", False)) and bool(getattr(node, "enabled", False)):
                rect = getattr(node, "rect", Rect(0, 0, 0, 0))
                menu_bottom = max(menu_bottom, int(rect.bottom))

            if task_panel_rect is None and bool(getattr(node, "visible", False)) and hasattr(node, "is_task_panel"):
                try:
                    if node.is_task_panel():
                        task_panel_rect = Rect(getattr(node, "rect", Rect(0, 0, 0, 0)))
                except Exception:
                    pass

        return {
            "windows": windows,
            "menu_bottom": int(menu_bottom),
            "task_panel_rect": task_panel_rect,
        }

    def _scene_windows(self, snapshot: Optional[Dict[str, object]] = None) -> List[object]:
        if snapshot is not None:
            return list(snapshot.get("windows", ()))
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

    def _menu_strip_bottom(self, snapshot: Optional[Dict[str, object]] = None) -> int:
        """Return bottom y of visible+enabled menu strip controls in the bound scene."""
        if snapshot is not None:
            return int(snapshot.get("menu_bottom", 0))
        menu_bottom = 0
        scene = self._bound_scene()
        queue: deque = deque(getattr(scene, "nodes", ()))
        while queue:
            node = queue.popleft()
            queue.extend(getattr(node, "children", ()))
            class_name = str(getattr(getattr(node, "__class__", object), "__name__", ""))
            if class_name == "MenuStripControl" and bool(getattr(node, "visible", False)) and bool(getattr(node, "enabled", False)):
                rect = getattr(node, "rect", Rect(0, 0, 0, 0))
                menu_bottom = max(menu_bottom, int(rect.bottom))
        return int(menu_bottom)

    def _ordered_windows(self, *, include_hidden: bool, snapshot: Optional[Dict[str, object]] = None) -> List[object]:
        windows = self._scene_windows(snapshot)
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

    def _work_area_rect(self, snapshot: Optional[Dict[str, object]] = None) -> Rect:
        work = Rect(self.app.surface.get_rect())
        menu_bottom = self._menu_strip_bottom(snapshot)
        if menu_bottom > int(work.top):
            work.top = int(menu_bottom)
        if self.avoid_task_panel:
            panel_rect = None
            if snapshot is not None:
                panel_rect = snapshot.get("task_panel_rect")
            if panel_rect is None:
                queue: deque = deque(self._bound_scene().nodes)
                while queue:
                    node = queue.popleft()
                    queue.extend(node.children)
                    if node.is_task_panel() and node.visible:
                        panel_rect = node.rect
                        break
            if panel_rect is not None and panel_rect.top < work.bottom:
                work.height = max(0, panel_rect.top - work.top)
        work.inflate_ip(-(self.padding * 2), -(self.padding * 2))
        return work

    def _fallback_clamp_target(
        self,
        window: object,
        target_x: int,
        target_y: int,
        snapshot: Optional[Dict[str, object]] = None,
    ) -> tuple[int, int]:
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

        # Match drag semantics: windows cannot cross visible menu strips.
        top_limit = max(top_limit, self._menu_strip_bottom(snapshot))

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

    def _clamp_target(
        self,
        window: object,
        target_x: int,
        target_y: int,
        snapshot: Optional[Dict[str, object]] = None,
    ) -> tuple[int, int]:
        """Clamp target coordinates using the same logic as window drag bounds when available."""
        parent = getattr(window, "parent", None)
        clamp_fn = getattr(parent, "_clamp_window_drag_target", None)
        if callable(clamp_fn):
            try:
                x, y = clamp_fn(window, int(target_x), int(target_y), self.app)
                return (int(x), int(y))
            except Exception:
                pass
        return self._fallback_clamp_target(window, int(target_x), int(target_y), snapshot)

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
    def _set_window_tiling_target(window: object, target_x: int, target_y: int) -> None:
        rect = Rect(getattr(window, "rect", Rect(0, 0, 0, 0)))
        setattr(
            window,
            "_window_tiling_target_rect",
            Rect(int(target_x), int(target_y), int(rect.width), int(rect.height)),
        )

    @staticmethod
    def _full_window_rect(window: object) -> Rect:
        rect = Rect(window.rect)
        return Rect(rect.x, rect.y, rect.width, rect.height)

    @staticmethod
    def _center_target(bounds: Rect, window_rect: Rect) -> tuple[int, int]:
        target = Rect(0, 0, int(window_rect.width), int(window_rect.height))
        target.center = bounds.center
        return (int(target.x), int(target.y))

    def _center_window(self, window: object, work_area: Optional[Rect] = None) -> None:
        bounds = Rect(self.app.surface.get_rect()) if work_area is None else Rect(work_area)
        rect = self._full_window_rect(window)
        target = Rect(0, 0, rect.width, rect.height)
        target.center = bounds.center
        self._set_window_tiling_target(window, int(target.x), int(target.y))
        current = Rect(window.rect)
        dx = target.x - current.x
        dy = target.y - current.y
        window.move_by(dx, dy)

    def center_windows(self, windows: Iterable[object]) -> None:
        for window in windows:
            if window is None:
                continue
            self._center_window(window)

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

    @staticmethod
    def _prefer_vertical_packing(windows: List[object], window_rects: Dict[object, Rect]) -> bool:
        """Infer whether current layout intent is primarily vertical.

        Fast-path uses spread and adjacent-step dominance over registration
        order. Ambiguous cases fall back to nearest-neighbor voting.
        """
        if len(windows) < 2:
            return False

        centers: Dict[object, tuple[int, int]] = {
            w: (int(rect.centerx), int(rect.centery))
            for w, rect in window_rects.items()
        }

        xs = [centers[w][0] for w in windows]
        ys = [centers[w][1] for w in windows]
        x_span = int(max(xs) - min(xs))
        y_span = int(max(ys) - min(ys))

        dominant_scale = 1.20
        if y_span > int(x_span * dominant_scale):
            return True
        if x_span > int(y_span * dominant_scale):
            return False

        total_step_dx = 0
        total_step_dy = 0
        for idx in range(1, len(windows)):
            prev = windows[idx - 1]
            cur = windows[idx]
            px, py = centers[prev]
            cx, cy = centers[cur]
            total_step_dx += abs(int(cx - px))
            total_step_dy += abs(int(cy - py))

        if total_step_dy > int(total_step_dx * dominant_scale):
            return True
        if total_step_dx > int(total_step_dy * dominant_scale):
            return False

        vertical_links = 0
        horizontal_links = 0
        for window in windows:
            cx, cy = centers[window]
            nearest = None
            nearest_dist = None
            for other in windows:
                if other is window:
                    continue
                ox, oy = centers[other]
                dx = int(ox - cx)
                dy = int(oy - cy)
                dist = (dx * dx) + (dy * dy)
                if nearest_dist is None or dist < nearest_dist:
                    nearest_dist = dist
                    nearest = (abs(dx), abs(dy))
            if nearest is None:
                continue
            nx, ny = nearest
            if ny > nx:
                vertical_links += 1
            elif nx > ny:
                horizontal_links += 1

        return vertical_links > horizontal_links

    def arrange_windows(
        self,
        newly_visible: Optional[Iterable[object]] = None,
        *,
        include_hidden: bool = False,
        immediate: bool = False,
        force: bool = False,
    ) -> None:
        scene_snapshot = self._scene_layout_snapshot()
        windows = self._ordered_windows(include_hidden=bool(include_hidden), snapshot=scene_snapshot)
        if (not self.enabled and not force) or not windows:
            return
        work = self._work_area_rect(scene_snapshot)
        if work.width <= 0 or work.height <= 0:
            return
        if len(windows) == 1:
            only_window = windows[0]
            target = Rect(0, 0, only_window.rect.width, only_window.rect.height)
            target.center = work.center
            clamped_x, clamped_y = self._clamp_target(only_window, int(target.x), int(target.y), scene_snapshot)
            self._set_window_tiling_target(only_window, int(clamped_x), int(clamped_y))
            if immediate:
                current = Rect(only_window.rect)
                only_window.move_by(int(clamped_x) - current.x, int(clamped_y) - current.y)
            else:
                self._animate_window_to(
                    only_window,
                    int(clamped_x),
                    int(clamped_y),
                    duration=WINDOW_TILING_ANIMATION_DURATION_SECONDS,
                )
            return

        order_idx = self._registration_order
        window_rects = {w: self._full_window_rect(w) for w in windows}
        prefer_vertical = self._prefer_vertical_packing(windows, window_rects)

        if prefer_vertical:
            # Vertical-aware preference order: preserve top/bottom first,
            # then left/right, with registration as deterministic tie-breaker.
            visible_sorted = sorted(
                windows,
                key=lambda w: (
                    int(window_rects[w].y),
                    int(window_rects[w].x),
                    int(order_idx.get(w, 0)),
                ),
            )
        else:
            # Spatial preference order: preserve left/right first, then top/bottom,
            # with registration as a deterministic tie-breaker.
            visible_sorted = sorted(
                windows,
                key=lambda w: (
                    int(window_rects[w].x),
                    int(window_rects[w].y),
                    int(order_idx.get(w, 0)),
                ),
            )

        # Tight shelf packing in row tracks: each row shares one top y for all
        # windows in that row; next row starts at (row_top + tallest_row_height + gap).
        rows: list[list[tuple[object, int, int]]] = []
        row: list[tuple[object, int, int]] = []
        row_width = 0
        row_height = 0
        used_height = 0
        overflow: list[object] = []
        row_source_top: int | None = None
        row_source_first_height: int | None = None

        for window in visible_sorted:
            wr = window_rects[window]
            ww = max(1, int(wr.width))
            wh = max(1, int(wr.height))
            add_w = ww if not row else (self.gap + ww)

            # Preserve strong above/below intent without making small cascade
            # offsets "sticky" across subsequent relayouts.
            force_new_row = False
            if prefer_vertical and row and row_source_top is not None and row_source_first_height is not None:
                source_dy = int(wr.y) - int(row_source_top)
                vertical_split_threshold = max(48, int(min(row_source_first_height, wh) * 0.5))
                if source_dy >= vertical_split_threshold:
                    force_new_row = True

            # New shelf when width would overflow current row.
            # Always allow full repack so previously cascaded layouts can
            # separate back into normal tiled rows when visibility changes.
            if row and (force_new_row or (row_width + add_w > int(work.width))):
                if used_height + row_height > int(work.height):
                    overflow.extend(w for w, _ww, _wh in row)
                else:
                    rows.append(row)
                    used_height += row_height + self.gap
                row = []
                row_width = 0
                row_height = 0
                row_source_top = None
                row_source_first_height = None
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
            if row_source_top is None:
                row_source_top = int(wr.y)
                row_source_first_height = int(wh)

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

        # Overflow windows: repeat the same tiled layer pattern and center each
        # layer's overall rect in the work area as it is processed.
        center_fallback: set[object] = set()
        exact_overflow_targets: set[object] = set()
        if overflow:
            overflow_queue = list(overflow)
            too_large_layer_retried: set[object] = set()
            while overflow_queue:
                pending = list(overflow_queue)
                overflow_queue = []

                provisional: list[tuple[object, int, int]] = []
                min_x = None
                min_y = None
                max_x = None
                max_y = None

                # Build one centered layer from the current queue in row shelves.
                rows: list[list[tuple[object, int, int]]] = []
                row: list[tuple[object, int, int]] = []
                row_width = 0
                row_height = 0
                for window in pending:
                    wr = window_rects[window]
                    ww = max(1, int(wr.width))
                    wh = max(1, int(wr.height))
                    add_w = ww if not row else (self.gap + ww)
                    if row and (row_width + add_w > int(work.width)):
                        rows.append(row)
                        row = []
                        row_width = 0
                        row_height = 0
                        add_w = ww
                    row.append((window, ww, wh))
                    row_width += add_w
                    row_height = max(row_height, wh)
                if row:
                    rows.append(row)

                cy_local = 0
                for r in rows:
                    cx_local = 0
                    row_h = max(item[2] for item in r) if r else 0
                    for window, ww, _wh in r:
                        tx = int(cx_local)
                        ty = int(cy_local)
                        wr = window_rects[window]
                        provisional.append((window, tx, ty))

                        left = int(tx)
                        top = int(ty)
                        right = int(tx + int(wr.width))
                        bottom = int(ty + int(wr.height))
                        min_x = left if min_x is None else min(min_x, left)
                        min_y = top if min_y is None else min(min_y, top)
                        max_x = right if max_x is None else max(max_x, right)
                        max_y = bottom if max_y is None else max(max_y, bottom)

                        cx_local += int(ww) + self.gap
                    cy_local += int(row_h) + self.gap

                if min_x is None or min_y is None or max_x is None or max_y is None:
                    break

                layer_width = int(max_x - min_x)
                layer_height = int(max_y - min_y)
                centered_left = int(work.x + max(0, (int(work.width) - layer_width) // 2))
                centered_top = int(work.y + max(0, (int(work.height) - layer_height) // 2))
                shift_x = int(centered_left - min_x)
                shift_y = int(centered_top - min_y)

                deferred: list[object] = []
                layer_center_fallback: list[object] = []
                for window, tx, ty in provisional:
                    target_x = int(tx + shift_x)
                    target_y = int(ty + shift_y)
                    wr = window_rects[window]
                    overflows_work = (
                        int(target_x) < int(work.left)
                        or int(target_y) < int(work.top)
                        or int(target_x + int(wr.width)) > int(work.right)
                        or int(target_y + int(wr.height)) > int(work.bottom)
                    )

                    too_large_for_work = int(wr.width) > int(work.width) or int(wr.height) > int(work.height)
                    if overflows_work and too_large_for_work:
                        # Retry once when multiple windows in the same layer
                        # would all center-stack on fallback.
                        if self.center_on_failure and window not in too_large_layer_retried:
                            layer_center_fallback.append(window)
                            continue
                        # After one retry, preserve tiled offsets and use final
                        # clamping to keep as much non-overlap as possible.
                        targets.append((window, target_x, target_y))
                        continue

                    if overflows_work:
                        deferred.append(window)
                        continue

                    exact_overflow_targets.add(window)
                    targets.append((window, target_x, target_y))

                if len(layer_center_fallback) > 1:
                    too_large_layer_retried.update(layer_center_fallback)
                    deferred.extend(layer_center_fallback)
                else:
                    for window in layer_center_fallback:
                        center_fallback.add(window)
                        targets.append((window, 0, 0))

                if not deferred:
                    break
                overflow_queue = deferred

        # Clamp targets to drag-safe bounds, then animate to new positions.
        duration = 0.0 if immediate else WINDOW_TILING_ANIMATION_DURATION_SECONDS
        for window, target_x, target_y in targets:
            if window in center_fallback:
                centered_x, centered_y = self._center_target(work, window_rects[window])
                clamped_x, clamped_y = self._clamp_target(window, centered_x, centered_y, scene_snapshot)
            elif window in exact_overflow_targets:
                clamped_x, clamped_y = (int(target_x), int(target_y))
            else:
                clamped_x, clamped_y = self._clamp_target(window, int(target_x), int(target_y), scene_snapshot)
            self._set_window_tiling_target(window, int(clamped_x), int(clamped_y))
            if duration <= 0.0:
                current = Rect(window.rect)
                window.move_by(int(clamped_x) - current.x, int(clamped_y) - current.y)
            else:
                self._animate_window_to(window, clamped_x, clamped_y, duration=duration)

    def initialize_window_positions(self) -> None:
        """Seed scene window internal positions using immediate tiling targets."""
        self.arrange_windows(include_hidden=True, immediate=True, force=True)
