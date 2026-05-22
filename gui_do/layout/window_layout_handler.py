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
        bounded_area_rect = getattr(self.app, "bounded_area_rect", None)
        if callable(bounded_area_rect):
            work = Rect(bounded_area_rect())
        else:
            # Fallback for tests/stubs that do not expose bounded_area_rect.
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
    def _layout_reference_rect(window: object) -> Rect:
        """Prefer stable tiling target rect when available.

        This preserves spatial ordering across repeated "tile now" operations,
        especially while animated movement is still converging.
        """
        ref = getattr(window, "_window_tiling_target_rect", None)
        current = Rect(getattr(window, "rect", Rect(0, 0, 0, 0)))
        if isinstance(ref, Rect):
            # If the live rect diverges significantly from the stored target,
            # treat live geometry as authoritative (e.g. user drag reposition).
            if abs(int(current.x) - int(ref.x)) > 4 or abs(int(current.y) - int(ref.y)) > 4:
                return Rect(current)
            return Rect(ref)
        return Rect(current.x, current.y, current.width, current.height)

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

    @staticmethod
    def _layer_column_cap(window_count: int, *, prefer_vertical: bool) -> int:
        """Return a soft per-row column cap to keep sparse layouts readable."""
        if window_count <= 0:
            return 1
        if prefer_vertical:
            if window_count <= 2:
                return 1
            if window_count <= 4:
                return 2
            return 3
        if window_count <= 3:
            return 2
        if window_count <= 6:
            return 3
        return max(3, int(window_count ** 0.5))

    def _pack_single_layer(
        self,
        windows: List[object],
        window_rects: Dict[object, Rect],
        work: Rect,
        *,
        prefer_vertical: bool,
        force_row_before: Optional[set[object]] = None,
    ) -> tuple[list[tuple[object, int, int]], list[object], list[object]]:
        """Pack one non-overlapping layer in row-major order.

        Returns (placements, remaining_windows, center_fallback_windows).
        """
        if not windows:
            return ([], [], [])

        placements: list[tuple[object, int, int]] = []
        center_fallback: list[object] = []
        remaining: list[object] = []
        hard_column_cap = 1 if (prefer_vertical and len(windows) <= 2) else 0

        row_x = 0
        row_y = 0
        row_h = 0
        row_count = 0

        idx = 0
        while idx < len(windows):
            window = windows[idx]
            wr = window_rects[window]
            ww = max(1, int(wr.width))
            wh = max(1, int(wr.height))
            fit_h = min(int(wh), int(work.height))

            too_large = ww > int(work.width)
            if too_large:
                center_fallback.append(window)
                idx += 1
                continue

            if row_count == 0:
                candidate_x = 0
                candidate_y = row_y
            else:
                force_new_row = bool(force_row_before is not None and window in force_row_before)
                if force_new_row:
                    candidate_x = 0
                    candidate_y = row_y + row_h + self.gap
                elif hard_column_cap > 0 and row_count >= hard_column_cap:
                    candidate_x = 0
                    candidate_y = row_y + row_h + self.gap
                else:
                    candidate_x = row_x + self.gap
                    candidate_y = row_y

            if candidate_x + ww > int(work.width):
                candidate_x = 0
                candidate_y = row_y + row_h + self.gap

            if candidate_y + fit_h > int(work.height):
                remaining.extend(windows[idx:])
                break

            placements.append((window, int(candidate_x), int(candidate_y)))

            if candidate_x == 0 and (row_count == 0 or candidate_y != row_y):
                row_y = int(candidate_y)
                row_h = int(fit_h)
                row_count = 1
            else:
                row_h = max(int(row_h), int(fit_h))
                row_count += 1
            row_x = int(candidate_x + ww)
            idx += 1

        return (placements, remaining, center_fallback)

    @staticmethod
    def _center_layer_in_work(
        placements: list[tuple[object, int, int]],
        window_rects: Dict[object, Rect],
        work: Rect,
    ) -> list[tuple[object, int, int]]:
        if not placements:
            return []

        # Center each row horizontally in work bounds (titlebars aligned per-row),
        # then center the full layer vertically.
        row_map: dict[int, list[tuple[object, int, int]]] = {}
        for window, x, y in placements:
            row_map.setdefault(int(y), []).append((window, int(x), int(y)))

        row_centered: list[tuple[object, int, int]] = []
        for row_y in sorted(row_map.keys()):
            row_items = sorted(row_map[row_y], key=lambda item: int(item[1]))
            row_min_x = min(int(x) for _w, x, _y in row_items)
            row_max_x = max(int(x + int(window_rects[w].width)) for w, x, _y in row_items)
            row_width = int(row_max_x - row_min_x)
            row_left = int(work.x + max(0, (int(work.width) - row_width) // 2))
            shift_x = int(row_left - row_min_x)
            for window, x, y in row_items:
                row_centered.append((window, int(x + shift_x), int(y)))

        min_y = min(int(y) for _w, _x, y in row_centered)
        max_y = max(int(y + int(window_rects[w].height)) for w, _x, y in row_centered)
        layer_h = int(max_y - min_y)
        centered_top = int(work.y + max(0, (int(work.height) - layer_h) // 2))
        shift_y = int(centered_top - min_y)
        return [(w, int(x), int(y + shift_y)) for w, x, y in row_centered]

    def _solve_layered_targets(
        self,
        ordered_windows: List[object],
        window_rects: Dict[object, Rect],
        work: Rect,
        *,
        prefer_vertical: bool,
        force_row_before: Optional[set[object]] = None,
    ) -> tuple[list[tuple[object, int, int]], set[object], int]:
        targets: list[tuple[object, int, int]] = []
        center_fallback: set[object] = set()
        layer_count = 0

        pending = list(ordered_windows)
        while pending:
            layer, remaining, layer_fallback = self._pack_single_layer(
                pending,
                window_rects,
                work,
                prefer_vertical=prefer_vertical,
                force_row_before=force_row_before,
            )
            if layer or layer_fallback:
                layer_count += 1
            centered_layer = self._center_layer_in_work(layer, window_rects, work)
            targets.extend(centered_layer)
            center_fallback.update(layer_fallback)

            if not centered_layer and not layer_fallback and remaining == pending:
                break
            pending = remaining

        for window in center_fallback:
            cx, cy = self._center_target(work, window_rects[window])
            targets.append((window, int(cx), int(cy)))
        return (targets, center_fallback, int(layer_count))

    def _spatial_rows(
        self,
        windows: List[object],
        window_rects: Dict[object, Rect],
    ) -> list[list[object]]:
        """Group windows into spatial rows based on current top alignment."""
        if not windows:
            return []

        heights = sorted(max(1, int(window_rects[w].height)) for w in windows)
        min_h = int(heights[0])
        # Keep row grouping tolerant enough for drag jitter but bounded so a
        # single very large window does not collapse adjacent rows.
        row_tolerance = max(8, min(int(min_h // 3), max(12, int(self.gap * 2))))

        rows: list[dict[str, object]] = []
        for window in sorted(windows, key=lambda w: (int(window_rects[w].top), int(window_rects[w].left))):
            top_y = int(window_rects[window].top)
            match = None
            match_dy: Optional[int] = None
            for row in rows:
                dy = abs(int(row["y"]) - top_y)
                if dy <= row_tolerance and (match_dy is None or dy < match_dy):
                    match = row
                    match_dy = dy
            if match is None:
                rows.append({"y": int(top_y), "items": [window]})
            else:
                items = list(match["items"])
                items.append(window)
                match["items"] = items
                match["y"] = int(round(sum(int(window_rects[w].top) for w in items) / float(len(items))))

        rows.sort(key=lambda r: int(r["y"]))
        return [
            sorted(list(row["items"]), key=lambda w: int(window_rects[w].centerx))
            for row in rows
        ]

    def _spatial_row_major_order(
        self,
        windows: List[object],
        window_rects: Dict[object, Rect],
    ) -> list[object]:
        rows = self._spatial_rows(windows, window_rects)
        return [w for row in rows for w in row]

    def _apply_targets(
        self,
        targets: list[tuple[object, int, int]],
        window_rects: Dict[object, Rect],
        scene_snapshot: Optional[Dict[str, object]],
        *,
        immediate: bool,
        center_fallback: Optional[set[object]] = None,
    ) -> None:
        duration = 0.0 if immediate else WINDOW_TILING_ANIMATION_DURATION_SECONDS
        center_fallback = center_fallback or set()
        for window, target_x, target_y in targets:
            if window in center_fallback:
                clamped_x, clamped_y = self._clamp_target(window, int(target_x), int(target_y), scene_snapshot)
            else:
                clamped_x, clamped_y = self._clamp_target(window, int(target_x), int(target_y), scene_snapshot)
            self._set_window_tiling_target(window, int(clamped_x), int(clamped_y))
            if duration <= 0.0:
                current = Rect(window.rect)
                window.move_by(int(clamped_x) - current.x, int(clamped_y) - current.y)
            else:
                self._animate_window_to(window, clamped_x, clamped_y, duration=duration)

    @staticmethod
    def _overlap_pair_count(
        targets: list[tuple[object, int, int]],
        window_rects: Dict[object, Rect],
    ) -> int:
        placed: list[Rect] = []
        for window, x, y in targets:
            wr = window_rects[window]
            placed.append(Rect(int(x), int(y), int(wr.width), int(wr.height)))

        overlaps = 0
        for idx in range(len(placed)):
            a = placed[idx]
            for jdx in range(idx + 1, len(placed)):
                if a.colliderect(placed[jdx]):
                    overlaps += 1
        return int(overlaps)

    def _fit_pass_repack_layers(
        self,
        targets: list[tuple[object, int, int]],
        window_rects: Dict[object, Rect],
        work: Rect,
        *,
        prefer_vertical: bool,
        center_fallback: Optional[set[object]] = None,
    ) -> tuple[list[tuple[object, int, int]], set[object]]:
        """Best-effort cleanup pass that repacks only within inferred layers.

        This pass is intentionally conservative: it only runs when the selected
        solution still has overlap, and it is only accepted when overlap count
        is reduced.
        """
        center_fallback = set(center_fallback or set())
        if not targets:
            return (targets, center_fallback)

        original_overlap = self._overlap_pair_count(targets, window_rects)
        if int(original_overlap) <= 0:
            return (targets, center_fallback)

        movable_targets = [(w, int(x), int(y)) for w, x, y in targets if w not in center_fallback]
        if not movable_targets:
            return (targets, center_fallback)

        def repack_from_layer_windows(layer_windows_list: list[list[object]]) -> list[tuple[object, int, int]]:
            repacked: list[tuple[object, int, int]] = []
            for layer_windows in layer_windows_list:
                if not layer_windows:
                    continue
                layer_rects = {
                    w: Rect(
                        int(next(x for lw, x, _y in movable_targets if lw is w)),
                        int(next(y for lw, _x, y in movable_targets if lw is w)),
                        int(window_rects[w].width),
                        int(window_rects[w].height),
                    )
                    for w in layer_windows
                }
                layer_rows = self._spatial_rows(layer_windows, layer_rects)
                layer_order = [w for row in layer_rows for w in row]
                force_row_before = {row[0] for row in layer_rows[1:] if row}

                layer_packed, remaining, layer_fallback = self._pack_single_layer(
                    layer_order,
                    window_rects,
                    work,
                    prefer_vertical=prefer_vertical,
                    force_row_before=force_row_before,
                )

                if remaining or layer_fallback:
                    repacked.extend(
                        [
                            (w, int(layer_rects[w].x), int(layer_rects[w].y))
                            for w in layer_windows
                        ]
                    )
                    continue

                repacked.extend(self._center_layer_in_work(layer_packed, window_rects, work))
            return repacked

        # Infer depth layers from current target geometry using first-fit
        # non-overlap grouping in existing target order.
        layers: list[list[tuple[object, int, int]]] = []
        for window, x, y in movable_targets:
            wr = window_rects[window]
            rect = Rect(int(x), int(y), int(wr.width), int(wr.height))
            placed = False
            for layer in layers:
                if all(
                    not rect.colliderect(
                        Rect(int(lx), int(ly), int(window_rects[lw].width), int(window_rects[lw].height))
                    )
                    for lw, lx, ly in layer
                ):
                    layer.append((window, int(x), int(y)))
                    placed = True
                    break
            if not placed:
                layers.append([(window, int(x), int(y))])

        repacked_targets = repack_from_layer_windows([[w for w, _x, _y in layer] for layer in layers])

        # Preserve fallback windows exactly as selected by the main solver.
        fallback_targets = [(w, int(x), int(y)) for w, x, y in targets if w in center_fallback]
        candidate_targets = list(repacked_targets) + fallback_targets
        candidate_overlap = self._overlap_pair_count(candidate_targets, window_rects)
        if int(candidate_overlap) < int(original_overlap):
            return (candidate_targets, center_fallback)

        # Fallback fit strategy: repack by spatial row bands from current
        # target positions when overlap-layer inference cannot improve.
        target_rects = {
            w: Rect(int(x), int(y), int(window_rects[w].width), int(window_rects[w].height))
            for w, x, y in movable_targets
        }
        row_band_layers = self._spatial_rows([w for w, _x, _y in movable_targets], target_rects)
        if row_band_layers:
            row_band_targets = repack_from_layer_windows([list(row) for row in row_band_layers]) + fallback_targets
            row_band_overlap = self._overlap_pair_count(row_band_targets, window_rects)
            if int(row_band_overlap) < int(original_overlap):
                return (row_band_targets, center_fallback)

        return (targets, center_fallback)

    @staticmethod
    def _infer_target_layers(
        targets: list[tuple[object, int, int]],
        window_rects: Dict[object, Rect],
    ) -> list[list[object]]:
        """Infer front-to-back layout layers preserving per-layer target order.

        Targets are emitted in layer sequence by the solver/fit passes, so we
        keep contiguous layer groups and start a new layer when an item would
        overlap the current layer.
        """
        layers: list[list[object]] = []
        current_layer: list[object] = []
        current_layer_rects: list[Rect] = []

        for window, x, y in targets:
            wr = window_rects[window]
            rect = Rect(int(x), int(y), int(wr.width), int(wr.height))
            overlaps_current = any(rect.colliderect(existing) for existing in current_layer_rects)

            if overlaps_current and current_layer:
                layers.append(list(current_layer))
                current_layer = []
                current_layer_rects = []

            current_layer.append(window)
            current_layer_rects.append(rect)

        if current_layer:
            layers.append(list(current_layer))
        return layers

    def _window_current_z_index(self, window: object) -> int:
        parent = getattr(window, "parent", None)
        children = getattr(parent, "children", None)
        if isinstance(children, list) and window in children:
            return int(children.index(window))
        return int(self._registration_order.get(window, 0))

    def _normalize_window_z_order_from_targets(
        self,
        targets: list[tuple[object, int, int]],
        window_rects: Dict[object, Rect],
        *,
        preferred_layer_tail: Optional[set[object]] = None,
    ) -> None:
        """Assign per-layer z-order slices so deeper layers stay behind front layers."""
        if not targets:
            return

        layers = self._infer_target_layers(targets, window_rects)
        if not layers:
            return

        # Render order is children list order; earlier is behind, later is front.
        # Inferred layers are back-to-front in solved target order.
        ordered_windows: list[object] = []
        for layer in layers:
            if preferred_layer_tail:
                layer_head = [w for w in layer if w not in preferred_layer_tail]
                layer_tail = [w for w in layer if w in preferred_layer_tail]
                ordered_windows.extend(layer_head + layer_tail)
            else:
                ordered_windows.extend(list(layer))

        parent_to_ordered_windows: dict[object, list[object]] = {}
        for window in ordered_windows:
            parent = getattr(window, "parent", None)
            if parent is None:
                continue
            parent_to_ordered_windows.setdefault(parent, []).append(window)

        for parent, desired in parent_to_ordered_windows.items():
            children = getattr(parent, "children", None)
            if not isinstance(children, list):
                continue
            if len(desired) <= 1:
                continue

            desired_set = set(desired)
            slot_indices = [
                idx for idx, child in enumerate(children)
                if child in desired_set
            ]
            if len(slot_indices) <= 1:
                continue

            reordered = list(children)
            for slot_idx, window in zip(slot_indices, desired):
                reordered[slot_idx] = window
            parent.children[:] = reordered

    def arrange_windows(
        self,
        newly_visible: Optional[Iterable[object]] = None,
        raised_windows: Optional[Iterable[object]] = None,
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

        window_rects = {w: self._full_window_rect(w) for w in windows}
        layout_rects = {w: self._layout_reference_rect(w) for w in windows}
        prefer_vertical = self._prefer_vertical_packing(windows, layout_rects)
        spatial_rows = self._spatial_rows(windows, layout_rects)
        solve_order = [w for row in spatial_rows for w in row]
        force_row_before = {row[0] for row in spatial_rows[1:] if row}

        # Visibility-event hint: newly shown windows should enter from the
        # trailing solve segment so existing visible layout stabilizes first.
        trailing_newly_visible: list[object] = []
        layer_tail_hint: set[object] = set()
        if newly_visible is not None:
            seen_new: set[object] = set()
            for candidate in newly_visible:
                if candidate in seen_new:
                    continue
                if candidate not in windows:
                    continue
                if not bool(getattr(candidate, "visible", False)):
                    continue
                trailing_newly_visible.append(candidate)
                layer_tail_hint.add(candidate)
                seen_new.add(candidate)
        if raised_windows is not None:
            for candidate in raised_windows:
                if candidate in windows and bool(getattr(candidate, "visible", False)):
                    layer_tail_hint.add(candidate)
        if trailing_newly_visible:
            trailing_set = set(trailing_newly_visible)
            solve_order = [w for w in solve_order if w not in trailing_set] + trailing_newly_visible

        forced_targets, forced_fallback, forced_layers = self._solve_layered_targets(
            solve_order,
            window_rects,
            work,
            prefer_vertical=prefer_vertical,
            force_row_before=force_row_before,
        )

        relaxed_targets, relaxed_fallback, relaxed_layers = self._solve_layered_targets(
            solve_order,
            window_rects,
            work,
            prefer_vertical=prefer_vertical,
        )

        # Preserve existing row membership by default; only relax when it
        # clearly reduces fragmentation pressure.
        targets = forced_targets
        center_fallback = forced_fallback
        forced_overlap = self._overlap_pair_count(forced_targets, window_rects)
        relaxed_overlap = self._overlap_pair_count(relaxed_targets, window_rects)
        if int(forced_overlap) > 0 and int(relaxed_overlap) < int(forced_overlap):
            targets = relaxed_targets
            center_fallback = relaxed_fallback
        elif int(forced_overlap) == 0 and int(relaxed_overlap) == 0:
            # Keep row membership unless relaxation is a substantial win.
            if int(relaxed_layers) + 2 < int(forced_layers):
                targets = relaxed_targets
                center_fallback = relaxed_fallback
        elif int(relaxed_layers) + 1 < int(forced_layers):
            targets = relaxed_targets
            center_fallback = relaxed_fallback

        targets, center_fallback = self._fit_pass_repack_layers(
            targets,
            window_rects,
            work,
            prefer_vertical=prefer_vertical,
            center_fallback=center_fallback,
        )

        self._normalize_window_z_order_from_targets(
            targets,
            window_rects,
            preferred_layer_tail=set(layer_tail_hint),
        )

        self._apply_targets(
            targets,
            window_rects,
            scene_snapshot,
            immediate=immediate,
            center_fallback=center_fallback,
        )

    def arrange_windows_for_drop(
        self,
        window: object,
        drop_point: tuple[int, int] | None,
        *,
        include_hidden: bool = False,
        immediate: bool = False,
        force: bool = False,
    ) -> None:
        """Retile after a user drop by spatially reinserting the dropped window.

        Spatial decision order is top-most to behind-most to better match drag-drop
        intent, then the final solve still emits standard tiling targets.
        """
        scene_snapshot = self._scene_layout_snapshot()
        windows = self._ordered_windows(include_hidden=bool(include_hidden), snapshot=scene_snapshot)
        if (not self.enabled and not force) or not windows:
            return
        if window not in windows:
            self.arrange_windows(
                include_hidden=include_hidden,
                immediate=immediate,
                force=force,
            )
            return

        work = self._work_area_rect(scene_snapshot)
        if work.width <= 0 or work.height <= 0:
            return

        clamped_drop = None
        if isinstance(drop_point, tuple) and len(drop_point) == 2:
            clamped_drop = (
                max(int(work.left), min(int(drop_point[0]), int(work.right))),
                max(int(work.top), min(int(drop_point[1]), int(work.bottom))),
            )

        if clamped_drop is None:
            self.arrange_windows(
                include_hidden=include_hidden,
                immediate=immediate,
                force=force,
            )
            return

        window_rects = {w: self._full_window_rect(w) for w in windows}
        layout_rects = {w: self._layout_reference_rect(w) for w in windows}
        prefer_vertical = self._prefer_vertical_packing(windows, layout_rects)

        top_to_back = [w for w in reversed(windows) if w is not window]
        drop_x, drop_y = clamped_drop
        insertion_gap = max(4, int(self.gap * 2))

        # Build front-to-back depth layers using current overlap relationships,
        # then insert into the first eligible layer and stop (no deeper search).
        depth_layers: list[list[object]] = []
        for candidate in top_to_back:
            candidate_rect = window_rects[candidate]
            placed = False
            for layer in depth_layers:
                if all(not candidate_rect.colliderect(window_rects[existing]) for existing in layer):
                    layer.append(candidate)
                    placed = True
                    break
            if not placed:
                depth_layers.append([candidate])

        selected_layer_index = 0
        selected_rows: list[list[object]] | None = None
        nearest_layer_index = 0
        nearest_layer_distance: Optional[int] = None

        for layer_index, layer_windows in enumerate(depth_layers):
            layer_rows = self._spatial_rows(layer_windows, layout_rects)
            if not layer_rows:
                continue

            layer_top = min(int(layout_rects[w].top) for row in layer_rows for w in row)
            layer_bottom = max(int(layout_rects[w].bottom) for row in layer_rows for w in row)
            min_band_y = int(layer_top - insertion_gap)
            max_band_y = int(layer_bottom + insertion_gap)

            if int(drop_y) >= min_band_y and int(drop_y) <= max_band_y:
                selected_layer_index = int(layer_index)
                selected_rows = [list(row) for row in layer_rows]
                break

            distance = 0
            if int(drop_y) < min_band_y:
                distance = int(min_band_y - int(drop_y))
            elif int(drop_y) > max_band_y:
                distance = int(int(drop_y) - max_band_y)
            if nearest_layer_distance is None or int(distance) < int(nearest_layer_distance):
                nearest_layer_distance = int(distance)
                nearest_layer_index = int(layer_index)

        if selected_rows is None:
            if depth_layers:
                selected_layer_index = int(nearest_layer_index)
                selected_rows = [list(row) for row in self._spatial_rows(depth_layers[selected_layer_index], layout_rects)]
            else:
                selected_layer_index = 0
                selected_rows = []

        rows = [list(row) for row in selected_rows if row]
        if not rows:
            rows = [[window]]
        else:
            row_spans: list[tuple[int, int, int]] = []
            for row in rows:
                top = min(int(layout_rects[w].top) for w in row)
                bottom = max(int(layout_rects[w].bottom) for w in row)
                center = int(round(sum(int(layout_rects[w].centery) for w in row) / float(max(1, len(row)))))
                row_spans.append((top, bottom, center))

            create_new_row = False
            target_row_index = len(rows) - 1
            if int(drop_y) < int(row_spans[0][0] - insertion_gap):
                create_new_row = True
                target_row_index = 0
            elif int(drop_y) > int(row_spans[-1][1] + insertion_gap):
                create_new_row = True
                target_row_index = len(rows)
            else:
                found_gap = False
                for idx in range(len(row_spans) - 1):
                    upper_bottom = int(row_spans[idx][1])
                    lower_top = int(row_spans[idx + 1][0])
                    if int(drop_y) > int(upper_bottom - insertion_gap) and int(drop_y) < int(lower_top + insertion_gap):
                        create_new_row = True
                        target_row_index = idx + 1
                        found_gap = True
                        break
                if not found_gap:
                    containing_index = None
                    for idx, (top, bottom, _center) in enumerate(row_spans):
                        if int(drop_y) >= int(top) and int(drop_y) <= int(bottom):
                            containing_index = idx
                            break
                    if containing_index is not None:
                        target_row_index = containing_index
                    else:
                        target_row_index = min(
                            range(len(row_spans)),
                            key=lambda idx: abs(int(row_spans[idx][2]) - int(drop_y)),
                        )

            if create_new_row:
                rows.insert(target_row_index, [window])
            else:
                target_row = list(rows[target_row_index])
                target_row.sort(key=lambda w: (int(layout_rects[w].left), int(layout_rects[w].centerx)))
                insert_in_row = len(target_row)

                if target_row:
                    first_rect = layout_rects[target_row[0]]
                    last_rect = layout_rects[target_row[-1]]
                    if int(drop_x) <= int(first_rect.left + insertion_gap):
                        insert_in_row = 0
                    elif int(drop_x) >= int(last_rect.right - insertion_gap):
                        insert_in_row = len(target_row)
                    else:
                        placed = False
                        for idx in range(len(target_row) - 1):
                            left_rect = layout_rects[target_row[idx]]
                            right_rect = layout_rects[target_row[idx + 1]]
                            boundary = int((int(left_rect.right) + int(right_rect.left)) // 2)
                            if abs(int(drop_x) - boundary) <= insertion_gap or int(drop_x) <= boundary:
                                insert_in_row = idx + 1
                                placed = True
                                break
                        if not placed:
                            # If pointer is inside an existing item band, split
                            # before/after that item by its center x.
                            for idx, candidate in enumerate(target_row):
                                rect = layout_rects[candidate]
                                if int(drop_x) >= int(rect.left) and int(drop_x) <= int(rect.right):
                                    insert_in_row = idx if int(drop_x) <= int(rect.centerx) else idx + 1
                                    placed = True
                                    break
                        if not placed:
                            insert_in_row = len(target_row)

                target_row.insert(insert_in_row, window)
                rows[target_row_index] = target_row

        solve_rows: list[list[object]] = []
        if depth_layers:
            for layer_index, layer_windows in enumerate(depth_layers):
                if int(layer_index) == int(selected_layer_index):
                    solve_rows.extend([list(row) for row in rows if row])
                else:
                    solve_rows.extend([list(row) for row in self._spatial_rows(layer_windows, layout_rects) if row])
        else:
            solve_rows = [list(row) for row in rows if row]

        # Preserve row boundaries from the spatial insertion model while solving.
        solve_order = [w for row in solve_rows for w in row]
        force_row_before = {row[0] for row in solve_rows[1:] if row}

        targets, center_fallback, forced_layers = self._solve_layered_targets(
            solve_order,
            window_rects,
            work,
            prefer_vertical=prefer_vertical,
            force_row_before=force_row_before,
        )

        # If row constraints force extra overlap-prone layers, retry without
        # forced row breaks and prefer the solution with fewer layers.
        relaxed_targets, relaxed_fallback, relaxed_layers = self._solve_layered_targets(
            solve_order,
            window_rects,
            work,
            prefer_vertical=prefer_vertical,
        )

        # Drop solves prioritize explicit row/slot insertion intent.
        forced_overlap = self._overlap_pair_count(targets, window_rects)
        relaxed_overlap = self._overlap_pair_count(relaxed_targets, window_rects)

        forced_drop_target = next(((tx, ty) for w, tx, ty in targets if w is window), None)
        relaxed_drop_target = next(((tx, ty) for w, tx, ty in relaxed_targets if w is window), None)
        drop_proximity_tolerance = max(12, int(self.gap * 2))

        if int(forced_overlap) > 0 and int(relaxed_overlap) < int(forced_overlap):
            use_relaxed = True
            if forced_drop_target is not None and relaxed_drop_target is not None:
                forced_drop_dy = abs(int(forced_drop_target[1]) - int(drop_y))
                relaxed_drop_dy = abs(int(relaxed_drop_target[1]) - int(drop_y))
                if int(relaxed_drop_dy) > int(forced_drop_dy) + int(drop_proximity_tolerance):
                    use_relaxed = False
            if use_relaxed:
                targets = relaxed_targets
                center_fallback = relaxed_fallback
        elif int(relaxed_layers) + 1 < int(forced_layers):
            targets = relaxed_targets
            center_fallback = relaxed_fallback

        targets, center_fallback = self._fit_pass_repack_layers(
            targets,
            window_rects,
            work,
            prefer_vertical=prefer_vertical,
            center_fallback=center_fallback,
        )

        self._normalize_window_z_order_from_targets(targets, window_rects)

        self._apply_targets(
            targets,
            window_rects,
            scene_snapshot,
            immediate=immediate,
            center_fallback=center_fallback,
        )

    def initialize_window_positions(self) -> None:
        """Seed scene window internal positions using immediate tiling targets."""
        self.arrange_windows(include_hidden=True, immediate=True, force=True)
