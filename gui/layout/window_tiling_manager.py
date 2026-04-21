from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from pygame import Rect


class WindowTilingManager:
    """Non-overlapping window tiling adapted for the rebased scene graph."""

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
        stack = list(self._bound_scene().nodes)
        while stack:
            node = stack.pop(0)
            children = getattr(node, "children", None)
            if children:
                stack.extend(children)
            if self._is_window_like(node):
                windows.append(node)
        return windows

    @staticmethod
    def _is_window_like(node: object) -> bool:
        return hasattr(node, "titlebar_height") and hasattr(node, "rect") and hasattr(node, "move_by")

    def _ensure_registration(self, windows: Iterable[object]) -> None:
        current = set(windows)
        self._registration_order = {w: idx for w, idx in self._registration_order.items() if w in current}
        for window in windows:
            if window not in self._registration_order:
                self._registration_order[window] = self._next_order
                self._next_order += 1

    def _visible_windows(self) -> List[object]:
        windows = self._scene_windows()
        self._ensure_registration(windows)
        visible = [w for w in windows if bool(getattr(w, "visible", False))]
        visible.sort(key=lambda w: self._registration_order[w])
        return visible

    def _work_area_rect(self) -> Rect:
        work = Rect(self.app.surface.get_rect())
        if self.avoid_task_panel:
            stack = list(self._bound_scene().nodes)
            while stack:
                node = stack.pop(0)
                children = getattr(node, "children", None)
                if children:
                    stack.extend(children)
                if getattr(node, "control_id", "") == "task_panel" and bool(getattr(node, "visible", False)):
                    panel_rect = getattr(node, "rect", None)
                    if panel_rect is not None and panel_rect.top < work.bottom:
                        work.height = max(0, panel_rect.top - work.top)
                    break
        work.inflate_ip(-(self.padding * 2), -(self.padding * 2))
        return work

    @staticmethod
    def _full_window_rect(window: object) -> Rect:
        rect = Rect(getattr(window, "rect"))
        return Rect(rect.x, rect.y, rect.width, rect.height)

    def _center_window(self, window: object, work_area: Optional[Rect] = None) -> None:
        bounds = Rect(self.app.surface.get_rect()) if work_area is None else Rect(work_area)
        rect = self._full_window_rect(window)
        target = Rect(0, 0, rect.width, rect.height)
        target.center = bounds.center
        current = Rect(getattr(window, "rect"))
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

    def arrange_windows(self, newly_visible: Optional[Iterable[object]] = None) -> None:
        visible = self._visible_windows()
        if not self.enabled:
            return
        if not visible:
            return
        work = self._work_area_rect()
        if work.width <= 0 or work.height <= 0:
            return
        if len(visible) == 1:
            self._center_window(visible[0], work)
            return

        cell_width = max(self._full_window_rect(w).width for w in visible)
        cell_height = max(self._full_window_rect(w).height for w in visible)
        pitch_x = cell_width + self.gap
        pitch_y = cell_height + self.gap
        max_cols = max(1, (work.width + self.gap) // max(1, pitch_x))
        max_rows = max(1, (work.height + self.gap) // max(1, pitch_y))
        if max_cols * max_rows < len(visible):
            if self.center_on_failure:
                targets = list(newly_visible or visible)
                for window in targets:
                    if window in visible:
                        self._center_window(window, work)
            return

        cols = min(max_cols, len(visible))
        rows = (len(visible) + cols - 1) // cols
        total_w = (cols * cell_width) + ((cols - 1) * self.gap)
        total_h = (rows * cell_height) + ((rows - 1) * self.gap)
        start_x = work.x + max(0, (work.width - total_w) // 2)
        start_y = work.y + max(0, (work.height - total_h) // 2)

        for idx, window in enumerate(visible):
            row = idx // cols
            col = idx % cols
            target_x = start_x + (col * pitch_x)
            target_y = start_y + (row * pitch_y)
            current = Rect(getattr(window, "rect"))
            window.move_by(target_x - current.x, target_y - current.y)
