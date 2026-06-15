from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List, Optional, Tuple

from pygame import Rect


WINDOW_TILING_ANIMATION_DURATION_SECONDS = 0.5


# A "placement" is a tuple of (window, x, y) describing an absolute target.
Placement = Tuple[object, int, int]
# A "shelf" is an ordered list of windows that share a row (aligned titlebars).
Shelf = List[object]
# A "page" is an ordered list of shelves packed into one work-area-sized bin.
Page = List[Shelf]


class WindowLayoutHandler:
    """Arrange window-like scene nodes into a non-overlapping, centered tiling.

    The layout is a *level-oriented shelf packing* (Coffman et al. 1980,
    "Performance Bounds for Level-Oriented Two-Dimensional Packing Algorithms";
    Baker & Schwarz 1983, "Shelf Algorithms for Two-Dimensional Packing").
    Windows keep their own size; they are packed left-to-right into rows
    (shelves). When a row no longer fits horizontally a new shelf is opened, and
    when a shelf no longer fits vertically within the work area a new *page*
    (bin) is started. Pages share the same centered region of the work area and
    are stacked in z-order, giving the "layers on top of each other" behaviour
    requested for overflow. Each shelf is centered horizontally and each page is
    centered vertically, producing balanced rows/columns. The solve runs in
    ``O(n log n)`` and is therefore scalable for large window counts.

    Windows tween to their computed targets unless an immediate move is
    requested. All public method signatures and the window attribute contract
    (``_window_tiling_target_rect`` / ``_window_tiling_animating``) are
    preserved so existing callers and visual transitions continue to work.
    """

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
        # Most recent page layering, exposed for diagnostics/tests.
        self._last_solve_layers: Optional[List[List[object]]] = None

    # ------------------------------------------------------------------
    # Scene traversal / window discovery
    # ------------------------------------------------------------------
    def _bound_scene(self):
        if self.scene is not None:
            return self.scene
        return self.app.scene

    @staticmethod
    def _is_window_like(node: object) -> bool:
        return bool(node.is_window())

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

    # ------------------------------------------------------------------
    # Registration ordering
    # ------------------------------------------------------------------
    def _ensure_registration(self, windows: Iterable[object]) -> None:
        ordered = list(windows)
        self._registration_order = {window: index for index, window in enumerate(ordered)}
        self._next_order = int(len(ordered))

    def prime_registration(self) -> None:
        """Register current scene windows without performing layout."""
        self._ensure_registration(self._scene_windows())

    def promote_window_registration(self, window: object) -> None:
        """Sync registration to current graph order after promotion."""
        if window is None:
            return
        self._ensure_registration(self._scene_windows())

    def demote_window_registration(self, window: object) -> None:
        """Sync registration to current graph order after demotion."""
        if window is None:
            return
        self._ensure_registration(self._scene_windows())

    def remove_window_registration(self, window: object) -> None:
        """Remove one window from layout registration metadata."""
        if window is None:
            return
        self._registration_order.pop(window, None)

    def _ordered_windows(self, *, include_hidden: bool, snapshot: Optional[Dict[str, object]] = None) -> List[object]:
        windows = self._scene_windows(snapshot)
        self._ensure_registration(windows)
        if include_hidden:
            ordered = list(windows)
        else:
            ordered = [w for w in windows if w.visible]
        ordered.sort(key=lambda w: self._registration_order[w])
        return ordered

    def _visible_windows(self) -> List[object]:
        return self._ordered_windows(include_hidden=False)

    def visible_windows_snapshot(self) -> tuple[object, ...]:
        """Return current visible windows in registration order."""
        return tuple(self._visible_windows())

    # ------------------------------------------------------------------
    # Work area
    # ------------------------------------------------------------------
    def _menu_strip_bottom(self, snapshot: Optional[Dict[str, object]] = None) -> int:
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

    # ------------------------------------------------------------------
    # Clamping
    # ------------------------------------------------------------------
    def _fallback_clamp_target(
        self,
        window: object,
        target_x: int,
        target_y: int,
        snapshot: Optional[Dict[str, object]] = None,
    ) -> tuple[int, int]:
        rect = Rect(window.rect)
        surface = getattr(self.app, "surface", None)
        if surface is None:
            return (int(target_x), int(target_y))

        screen_rect = surface.get_rect()
        min_left = int(screen_rect.left)
        max_left = int(screen_rect.right - rect.width)
        top_limit = int(screen_rect.top)
        max_top = int(screen_rect.bottom - rect.height)
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
        parent = getattr(window, "parent", None)
        clamp_fn = getattr(parent, "_clamp_window_drag_target", None)
        if callable(clamp_fn):
            try:
                x, y = clamp_fn(window, int(target_x), int(target_y), self.app)
                return (int(x), int(y))
            except Exception:
                pass
        return self._fallback_clamp_target(window, int(target_x), int(target_y), snapshot)

    # ------------------------------------------------------------------
    # Animation / target metadata
    # ------------------------------------------------------------------
    def _animate_window_to(self, window: object, target_x: int, target_y: int, *, duration: float) -> bool:
        current = Rect(window.rect)
        if (current.x, current.y) == (int(target_x), int(target_y)):
            setattr(window, "_window_tiling_animating", False)
            return True

        tweens = getattr(self.app, "tweens", None)
        if tweens is None or not hasattr(tweens, "tween_fn"):
            setattr(window, "_window_tiling_animating", False)
            window.move_by(int(target_x) - current.x, int(target_y) - current.y)
            return True

        tag = f"window_tiling:{id(window)}"
        cancel_for_tag = getattr(tweens, "cancel_all_for_tag", None)
        if callable(cancel_for_tag):
            cancel_for_tag(tag)
        setattr(window, "_window_tiling_animating", True)

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

        def _finish() -> None:
            setattr(window, "_window_tiling_animating", False)

        handle = None
        try:
            handle = tweens.tween_fn(float(duration), _apply, easing="ease_in_out", on_complete=_finish, tag=tag)
        except Exception:
            handle = None

        scheduled = bool(handle is not None)
        if scheduled and hasattr(handle, "is_complete"):
            try:
                scheduled = not bool(handle.is_complete)
            except Exception:
                scheduled = True

        if not scheduled:
            setattr(window, "_window_tiling_animating", False)
            window.move_by(int(target_x) - current.x, int(target_y) - current.y)
            return True
        return True

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
        """Prefer the stable tiling target rect when available.

        This preserves spatial ordering across repeated "tile now" operations,
        especially while animated movement is still converging.
        """
        ref = getattr(window, "_window_tiling_target_rect", None)
        current = Rect(getattr(window, "rect", Rect(0, 0, 0, 0)))
        if isinstance(ref, Rect):
            if bool(getattr(window, "_window_tiling_animating", False)):
                if abs(int(current.x) - int(ref.x)) > 64 or abs(int(current.y) - int(ref.y)) > 64:
                    setattr(window, "_window_tiling_animating", False)
                    return Rect(current)
                return Rect(ref)
            if abs(int(current.x) - int(ref.x)) > 4 or abs(int(current.y) - int(ref.y)) > 4:
                return Rect(current)
            return Rect(ref)
        return Rect(current.x, current.y, current.width, current.height)

    # ------------------------------------------------------------------
    # Centering helpers
    # ------------------------------------------------------------------
    def _center_window(self, window: object, work_area: Optional[Rect] = None) -> None:
        bounds = Rect(self.app.surface.get_rect()) if work_area is None else Rect(work_area)
        rect = self._full_window_rect(window)
        target = Rect(0, 0, rect.width, rect.height)
        target.center = bounds.center
        self._set_window_tiling_target(window, int(target.x), int(target.y))
        current = Rect(window.rect)
        window.move_by(target.x - current.x, target.y - current.y)

    def center_windows(self, windows: Iterable[object]) -> None:
        for window in windows:
            if window is None:
                continue
            self._center_window(window)

    @staticmethod
    def _center_target(bounds: Rect, window_rect: Rect) -> tuple[int, int]:
        target = Rect(0, 0, int(window_rect.width), int(window_rect.height))
        target.center = bounds.center
        return (int(target.x), int(target.y))

    # ------------------------------------------------------------------
    # Spatial row grouping (used to derive solve order from current layout)
    # ------------------------------------------------------------------
    def _spatial_rows(
        self,
        windows: List[object],
        window_rects: Dict[object, Rect],
    ) -> list[list[object]]:
        """Group windows into spatial rows based on current top alignment."""
        if not windows:
            return []

        heights = sorted(max(1, int(window_rects[w].height)) for w in windows)
        median_h = int(heights[len(heights) // 2])
        # Tolerant enough for drag jitter, but robust to tiny outlier windows
        # that would otherwise collapse tolerance and fragment rows.
        row_tolerance = max(8, min(int(median_h // 3), max(12, int(self.gap * 2))))

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

    # ------------------------------------------------------------------
    # Core shelf packing
    # ------------------------------------------------------------------
    def _fit_height(self, window: object, window_rects: Dict[object, Rect], work: Rect) -> int:
        return min(max(1, int(window_rects[window].height)), max(1, int(work.height)))

    def _shelf_height(self, shelf: Shelf, window_rects: Dict[object, Rect], work: Rect) -> int:
        if not shelf:
            return 0
        return max(self._fit_height(w, window_rects, work) for w in shelf)

    def _page_height(self, page: Page, window_rects: Dict[object, Rect], work: Rect) -> int:
        if not page:
            return 0
        total = sum(self._shelf_height(shelf, window_rects, work) for shelf in page)
        return total + self.gap * (len(page) - 1)

    def _pack_pages(
        self,
        order: List[object],
        window_rects: Dict[object, Rect],
        work: Rect,
        force_row_before: Optional[set[object]] = None,
    ) -> tuple[List[Page], set[object]]:
        """Pack windows into pages of shelves (level-oriented, order preserving).

        Returns the list of pages and the set of windows that are too wide to
        fit the work area (center-fallback windows that will be clamped).
        """
        gap = int(self.gap)
        force_row_before = force_row_before or set()
        pages: List[Page] = []
        fallback: set[object] = set()

        current_page: Page = []
        current_shelf: Shelf = []
        current_shelf_width = 0

        def close_shelf() -> None:
            nonlocal current_shelf, current_shelf_width
            if current_shelf:
                current_page.append(current_shelf)
            current_shelf = []
            current_shelf_width = 0

        def close_page() -> None:
            nonlocal current_page
            close_shelf()
            if current_page:
                pages.append(current_page)
            current_page = []

        for window in order:
            wr = window_rects[window]
            window_width = max(1, int(wr.width))
            fit_h = self._fit_height(window, window_rects, work)
            too_wide = window_width > int(work.width)
            if too_wide:
                fallback.add(window)

            forced_break = window in force_row_before
            wrap_width = bool(
                current_shelf
                and (current_shelf_width + gap + window_width) > int(work.width)
            )
            needs_new_shelf = bool(current_shelf) and (forced_break or too_wide or wrap_width)

            if current_shelf and not needs_new_shelf:
                current_shelf.append(window)
                current_shelf_width += gap + window_width
                if too_wide:
                    close_shelf()
                continue

            # Opening a new shelf: decide whether it still fits the current page.
            prospective: Page = list(current_page)
            if current_shelf:
                prospective = prospective + [current_shelf]
            if prospective:
                committed = self._page_height(prospective, window_rects, work)
                prospective_height = committed + gap + fit_h
                if prospective_height > int(work.height):
                    close_page()

            close_shelf()
            current_shelf = [window]
            current_shelf_width = window_width
            if too_wide:
                close_shelf()

        close_page()
        return pages, fallback

    def _position_pages(
        self,
        pages: List[Page],
        window_rects: Dict[object, Rect],
        work: Rect,
    ) -> tuple[List[Placement], List[List[object]]]:
        """Center each shelf horizontally and each page vertically in the work area."""
        targets: List[Placement] = []
        page_layers: List[List[object]] = []
        gap = int(self.gap)

        for page in pages:
            page_height = self._page_height(page, window_rects, work)
            top = int(work.y) + max(0, (int(work.height) - page_height) // 2)
            y = top
            page_windows: List[object] = []
            for shelf in page:
                shelf_height = self._shelf_height(shelf, window_rects, work)
                row_width = sum(max(1, int(window_rects[w].width)) for w in shelf) + gap * (len(shelf) - 1)
                left = int(work.x) + max(0, (int(work.width) - row_width) // 2)
                x = left
                for window in shelf:
                    window_width = max(1, int(window_rects[window].width))
                    targets.append((window, int(x), int(y)))
                    page_windows.append(window)
                    x += window_width + gap
                y += shelf_height + gap
            page_layers.append(page_windows)

        return targets, page_layers

    def _solve_layout(
        self,
        order: List[object],
        window_rects: Dict[object, Rect],
        work: Rect,
        force_row_before: Optional[set[object]] = None,
    ) -> tuple[List[Placement], set[object], List[List[object]]]:
        pages, fallback = self._pack_pages(order, window_rects, work, force_row_before)
        targets, page_layers = self._position_pages(pages, window_rects, work)
        return targets, fallback, page_layers

    # ------------------------------------------------------------------
    # Z-order normalization (deeper pages render behind nearer pages)
    # ------------------------------------------------------------------
    def _reorder_container(self, container: list, desired: List[object]) -> None:
        """Reorder, in place, the slots of ``container`` occupied by ``desired``.

        Only positions that currently hold windows from ``desired`` are
        rewritten; all other nodes keep their slots. ``desired`` is ordered
        back-to-front (lower index = drawn earlier = further back).
        """
        member = set(desired)
        slots = [index for index, node in enumerate(container) if node in member]
        ordered = [w for w in desired if w in set(container)]
        for slot, window in zip(slots, ordered):
            container[slot] = window

    def _apply_layer_z_order(
        self,
        page_layers: List[List[object]],
        demote: Optional[set[object]] = None,
        promote: Optional[set[object]] = None,
    ) -> None:
        demote = demote or set()
        promote = promote or set()

        desired: List[object] = []
        for page in page_layers:
            desired.extend(page)

        # Demoted windows go to the very back; promoted windows to the very front.
        if demote:
            back = [w for w in desired if w in demote]
            rest = [w for w in desired if w not in demote]
            desired = back + rest
        if promote:
            rest = [w for w in desired if w not in promote]
            front = [w for w in desired if w in promote]
            desired = rest + front

        self._last_solve_layers = [list(page) for page in page_layers]

        # Group desired windows by their container and reorder each.
        containers: List[list] = []
        seen_ids: set[int] = set()
        for window in desired:
            parent = getattr(window, "parent", None)
            container = getattr(parent, "children", None)
            if not isinstance(container, list) or window not in container:
                container = getattr(self._bound_scene(), "nodes", None)
            if isinstance(container, list) and id(container) not in seen_ids:
                containers.append(container)
                seen_ids.add(id(container))

        for container in containers:
            self._reorder_container(container, desired)

    # ------------------------------------------------------------------
    # Applying targets
    # ------------------------------------------------------------------
    def _apply_targets(
        self,
        targets: List[Placement],
        scene_snapshot: Optional[Dict[str, object]],
        *,
        immediate: bool,
        immediate_windows: Optional[Iterable[object]] = None,
        skip_windows: Optional[set[object]] = None,
    ) -> None:
        duration = 0.0 if immediate else WINDOW_TILING_ANIMATION_DURATION_SECONDS
        immediate_window_set = set(immediate_windows or ())
        skip_windows = skip_windows or set()
        for window, target_x, target_y in targets:
            if window in skip_windows:
                continue
            clamped_x, clamped_y = self._clamp_target(window, int(target_x), int(target_y), scene_snapshot)
            self._set_window_tiling_target(window, int(clamped_x), int(clamped_y))
            current = Rect(window.rect)
            if int(clamped_x) != int(current.x) or int(clamped_y) != int(current.y):
                if duration <= 0.0 or window in immediate_window_set:
                    setattr(window, "_window_tiling_animating", False)
                    window.move_by(int(clamped_x) - current.x, int(clamped_y) - current.y)
                else:
                    self._animate_window_to(window, clamped_x, clamped_y, duration=duration)

    # ------------------------------------------------------------------
    # Public: primary tiling
    # ------------------------------------------------------------------
    def arrange_windows(
        self,
        newly_visible: Optional[Iterable[object]] = None,
        raised_windows: Optional[Iterable[object]] = None,
        demoted_windows: Optional[Iterable[object]] = None,
        *,
        include_hidden: bool = False,
        immediate: bool = False,
        immediate_windows: Optional[Iterable[object]] = None,
        force: bool = False,
    ) -> None:
        scene_snapshot = self._scene_layout_snapshot()
        windows = self._ordered_windows(include_hidden=bool(include_hidden), snapshot=scene_snapshot)
        if (not self.enabled and not force) or not windows:
            return
        window_set = set(windows)
        work = self._work_area_rect(scene_snapshot)
        if work.width <= 0 or work.height <= 0:
            return

        if len(windows) == 1:
            self._arrange_single_window(windows[0], work, scene_snapshot, immediate, immediate_windows)
            return

        window_rects = {w: self._full_window_rect(w) for w in windows}

        promoted_raised = set(self._filter_visible(raised_windows, window_set))
        demoted_lowered = set(self._filter_visible(demoted_windows, window_set))
        newly_shown = set(self._filter_visible(newly_visible, window_set))

        # Pure order-based shelf packing: windows are packed left-to-right in
        # registration order, wrapping to a new row by width and to a new
        # z-stacked page by height. This is fully general -- it scales with the
        # actual number and sizes of windows and is independent of any specific
        # window set. Raise/lower/visibility intent only adjusts the z-layer
        # ordering (which page a window lands on), never the geometric packing,
        # so windows that fit side-by-side are never split into overlapping
        # pages.
        order = list(windows)

        targets, fallback, page_layers = self._solve_layout(order, window_rects, work)

        self._apply_layer_z_order(
            page_layers,
            demote=demoted_lowered,
            promote=promoted_raised | newly_shown,
        )
        self._apply_targets(
            targets,
            scene_snapshot,
            immediate=bool(immediate),
            immediate_windows=immediate_windows,
        )

    def _arrange_single_window(
        self,
        window: object,
        work: Rect,
        scene_snapshot: Optional[Dict[str, object]],
        immediate: bool,
        immediate_windows: Optional[Iterable[object]],
    ) -> None:
        target = Rect(0, 0, window.rect.width, window.rect.height)
        target.center = work.center
        clamped_x, clamped_y = self._clamp_target(window, int(target.x), int(target.y), scene_snapshot)
        self._set_window_tiling_target(window, int(clamped_x), int(clamped_y))
        immediate_window_set = set(immediate_windows or ())
        if immediate or window in immediate_window_set:
            setattr(window, "_window_tiling_animating", False)
            current = Rect(window.rect)
            window.move_by(int(clamped_x) - current.x, int(clamped_y) - current.y)
        else:
            self._animate_window_to(
                window,
                int(clamped_x),
                int(clamped_y),
                duration=WINDOW_TILING_ANIMATION_DURATION_SECONDS,
            )

    @staticmethod
    def _filter_visible(candidates: Optional[Iterable[object]], window_set: set[object]) -> List[object]:
        result: List[object] = []
        seen: set[object] = set()
        if candidates is None:
            return result
        for candidate in candidates:
            if candidate in seen or candidate not in window_set:
                continue
            if not bool(getattr(candidate, "visible", False)):
                continue
            result.append(candidate)
            seen.add(candidate)
        return result

    # ------------------------------------------------------------------
    # Drop / drag insertion
    # ------------------------------------------------------------------
    def _insertion_plan_for_drop(
        self,
        moving_window: object,
        drop_point: tuple[int, int],
        other_windows: List[object],
        layout_rects: Dict[object, Rect],
        z_rank: Optional[Dict[object, int]] = None,
    ) -> tuple[List[object], set[object]]:
        """Build a packing plan that inserts ``moving_window`` at the drop slot.

        Returns ``(order, force_row_before)``:

        * ``order`` is the registration-style packing order with the moving
          window spliced in at the resolved position;
        * ``force_row_before`` is the set of windows that must start a new row,
          used to materialise a *new* row above / below / between existing rows
          when the drop lands in the empty space rather than on an existing row.

        The drop is resolved against the current spatial rows of the other
        windows. When several rows overlap the drop vertically (e.g. a large
        backdrop window whose band envelops a smaller foreground row) the
        *frontmost* row -- the one with the highest z-order, i.e. what the user
        actually sees on top -- wins, so a window can be dropped between two
        foreground windows even while a larger window sits behind them. This is
        independent of the specific windows present and scales with their count.
        """
        drop_x = int(drop_point[0])
        drop_y = int(drop_point[1])
        z_rank = z_rank or {}

        rows = self._spatial_rows(other_windows, layout_rects)
        if not rows:
            return [moving_window], set()

        reading_order = [w for row in rows for w in row]

        # Per-row geometry plus the reading-order index where the row begins.
        row_infos: list[dict[str, object]] = []
        start_index = 0
        for row in rows:
            tops = [int(layout_rects[w].top) for w in row]
            bottoms = [int(layout_rects[w].bottom) for w in row]
            row_infos.append(
                {
                    "row": row,
                    "top": int(min(tops)),
                    "bottom": int(max(bottoms)),
                    "z": max((int(z_rank.get(w, 0)) for w in row), default=0),
                    "start_index": int(start_index),
                }
            )
            start_index += len(row)

        # Rows whose vertical band contains the drop point.
        containing = [
            info for info in row_infos
            if int(info["top"]) <= drop_y <= int(info["bottom"])
        ]
        if containing:
            # Prefer the frontmost row (what the user sees on top), so a large
            # backdrop window behind a foreground row never steals the drop.
            target = max(containing, key=lambda info: int(info["z"]))
            row = list(target["row"])
            index = int(target["start_index"])
            for w in row:
                if drop_x <= int(layout_rects[w].centerx):
                    break
                index += 1
            order = reading_order[:index] + [moving_window] + reading_order[index:]
            # Joining an existing row: no forced break.
            return order, set()

        # The drop is in empty vertical space -> create a NEW row above, below,
        # or between existing rows. Find the row position by comparing the drop
        # against each row's vertical center line.
        insert_row_pos = 0
        for info in row_infos:
            center = (int(info["top"]) + int(info["bottom"])) / 2.0
            if drop_y > center:
                insert_row_pos += 1
            else:
                break

        if insert_row_pos <= 0:
            index = 0
        elif insert_row_pos >= len(row_infos):
            index = len(reading_order)
        else:
            index = int(row_infos[insert_row_pos]["start_index"])

        order = reading_order[:index] + [moving_window] + reading_order[index:]
        force: set[object] = {moving_window}
        # Force the following window (head of the next row) to break too, so the
        # new row stays isolated instead of absorbing the moving window.
        if index < len(reading_order):
            force.add(reading_order[index])
        return order, force

    def _drop_z_rank(self, scene_snapshot: Optional[Dict[str, object]]) -> Dict[object, int]:
        """Map each scene window to its z-order rank (higher = drawn in front)."""
        return {window: index for index, window in enumerate(self._scene_windows(scene_snapshot))}


    def arrange_windows_for_drop(
        self,
        window: object,
        drop_point: tuple[int, int],
        *,
        include_hidden: bool = False,
        immediate: bool = False,
        force: bool = False,
        demoted_windows: Optional[Iterable[object]] = None,
        promoted_windows: Optional[Iterable[object]] = None,
    ) -> None:
        scene_snapshot = self._scene_layout_snapshot()
        windows = self._ordered_windows(include_hidden=bool(include_hidden), snapshot=scene_snapshot)
        if (not self.enabled and not force) or not windows:
            return
        if window not in set(windows):
            self.arrange_windows(include_hidden=include_hidden, immediate=immediate, force=force)
            return
        work = self._work_area_rect(scene_snapshot)
        if work.width <= 0 or work.height <= 0:
            return

        if len(windows) == 1:
            self._arrange_single_window(windows[0], work, scene_snapshot, immediate, None)
            return

        window_rects = {w: self._full_window_rect(w) for w in windows}
        other_windows = [w for w in windows if w is not window]
        layout_rects = {w: self._full_window_rect(w) for w in windows}

        z_rank = self._drop_z_rank(scene_snapshot)
        order, force_rows = self._insertion_plan_for_drop(
            window, drop_point, other_windows, layout_rects, z_rank
        )

        demoted_set = set(self._filter_visible(demoted_windows, set(windows)))
        promoted_set = set(self._filter_visible(promoted_windows, set(windows)))

        # The drop slot already determines the dropped window's packing position;
        # caller-supplied promote/demote only adjusts its z-layer.
        targets, fallback, page_layers = self._solve_layout(order, window_rects, work, force_rows)

        self._apply_layer_z_order(page_layers, demote=demoted_set, promote=promoted_set)
        self._apply_targets(targets, scene_snapshot, immediate=bool(immediate))

    def arrange_windows_during_drag(
        self,
        window: object,
        pointer_point: tuple[int, int],
        *,
        include_hidden: bool = False,
    ) -> None:
        """Live drag preview: reflow non-dragged windows to reveal the drop slot.

        The dragged ``window`` is left under the cursor (its target is skipped);
        every other window animates to the layout it would take if ``window``
        were dropped at ``pointer_point``.
        """
        if not self.enabled:
            return
        scene_snapshot = self._scene_layout_snapshot()
        windows = self._ordered_windows(include_hidden=bool(include_hidden), snapshot=scene_snapshot)
        if not windows or window not in set(windows):
            return
        work = self._work_area_rect(scene_snapshot)
        if work.width <= 0 or work.height <= 0:
            return
        if len(windows) == 1:
            return

        window_rects = {w: self._full_window_rect(w) for w in windows}
        other_windows = [w for w in windows if w is not window]
        layout_rects = {w: self._full_window_rect(w) for w in windows}

        z_rank = self._drop_z_rank(scene_snapshot)
        order, force_rows = self._insertion_plan_for_drop(
            window, pointer_point, other_windows, layout_rects, z_rank
        )
        targets, fallback, _page_layers = self._solve_layout(order, window_rects, work, force_rows)
        # Skip the dragged window so it keeps following the cursor.
        self._apply_targets(targets, scene_snapshot, immediate=False, skip_windows={window})

    # ------------------------------------------------------------------
    # Public: misc
    # ------------------------------------------------------------------
    def initialize_window_positions(self) -> None:
        if not self.enabled:
            return
        self.arrange_windows(immediate=True)

    def is_top_level_window(self, window: object) -> bool:
        """Return True if no later (higher z-order) window overlaps ``window``."""
        windows = self._visible_windows()
        if window not in windows:
            return False
        window_rect = self._full_window_rect(window)
        try:
            idx = windows.index(window)
        except ValueError:
            return False
        for later_window in windows[idx + 1:]:
            if window_rect.colliderect(self._full_window_rect(later_window)):
                return False
        return True

    def is_top_z_order_for_group(self, window: object) -> bool:
        return self.is_top_level_window(window)

    def set_enabled(self, enabled: bool, relayout: bool = True) -> None:
        self.enabled = bool(enabled)
        if relayout and self.enabled:
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
        if relayout and self.enabled:
            self.arrange_windows()

    def read_settings(self) -> Dict[str, object]:
        return {
            "enabled": self.enabled,
            "gap": self.gap,
            "padding": self.padding,
            "avoid_task_panel": self.avoid_task_panel,
            "center_on_failure": self.center_on_failure,
        }
