from __future__ import annotations

import math
from pygame import Rect
from typing import Dict, Iterable, List, Optional, TYPE_CHECKING

from ..events import GuiError

if TYPE_CHECKING:
    from ...widgets.window import Window
    from ..gui_manager import GuiManager


class WindowTilingCoordinator:
    """Owns optional non-overlapping window tiling and runtime tiling settings."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Bind tiling behavior to one GUI manager instance."""
        self.gui: "GuiManager" = gui_manager
        self.enabled: bool = False
        self.gap: int = 16
        self.padding: int = 16
        self.avoid_task_panel: bool = True
        self.center_on_failure: bool = True
        self._registration_order_by_window: Dict["Window", int] = {}
        self._next_registration_order: int = 0
        self._last_column_count: Optional[int] = None

    def _ensure_registration_order(self, window: "Window") -> None:
        """Assign immutable registration order used for deterministic tiling order."""
        if window in self._registration_order_by_window:
            return
        self._registration_order_by_window[window] = self._next_registration_order
        self._next_registration_order += 1

    def record_window_registration(self, window: "Window") -> None:
        """Record a new window registration for later ordering decisions."""
        self._ensure_registration_order(window)

    @staticmethod
    def _window_rect(window: "Window") -> Rect:
        """Return full window bounds including title bar in screen coordinates."""
        return Rect(window.x, window.y - window.titlebar_size, window.width, window.height + window.titlebar_size)

    @staticmethod
    def _is_window_visible(window: "Window") -> bool:
        """Return current window visibility."""
        return bool(window.visible)

    @staticmethod
    def _is_tile_eligible(window: "Window") -> bool:
        """Return whether a window has geometry fields required for tiling math."""
        required_attrs = ('x', 'y', 'width', 'height', 'titlebar_size')
        return all(hasattr(window, name) for name in required_attrs)

    def _visible_windows(self) -> List["Window"]:
        """Return currently visible registered windows."""
        return [window for window in self.gui.windows if self._is_tile_eligible(window) and self._is_window_visible(window)]

    def _work_area_rect(self) -> Rect:
        """Return tiling work area inside the surface while honoring panel exclusion."""
        surface_rect = self.gui.surface.get_rect()
        work_rect = Rect(surface_rect)
        if self.avoid_task_panel and self.gui.task_panel is not None and self.gui.task_panel.visible:
            panel_top = self.gui.task_panel.get_rect().top
            if panel_top < work_rect.bottom:
                work_rect.height = max(0, panel_top - work_rect.top)
        work_rect.inflate_ip(-(self.padding * 2), -(self.padding * 2))
        return work_rect

    def _select_column_count(
        self,
        count: int,
        cell_width: int,
        cell_height: int,
        max_cols: int,
        max_rows: int,
        work_rect: Rect,
    ) -> int:
        """Choose a compact feasible column count while preserving layout stability."""
        if count <= 0 or max_cols <= 0 or max_rows <= 0:
            return 0
        feasible_cols = [
            cols
            for cols in range(1, min(max_cols, count) + 1)
            if ((count + cols - 1) // cols) <= max_rows
        ]
        if not feasible_cols:
            return 0
        ideal_cols = max(1, int(round(math.sqrt((count * max(work_rect.width, 1)) / max(work_rect.height, 1)))))
        previous_cols = self._last_column_count

        def score(cols: int) -> tuple[int, int, int, int, int]:
            rows = (count + cols - 1) // cols
            footprint_width = (cols * cell_width) + ((cols - 1) * self.gap)
            footprint_height = (rows * cell_height) + ((rows - 1) * self.gap)
            footprint_area = footprint_width * footprint_height
            footprint_perimeter = footprint_width + footprint_height
            previous_penalty = 0 if previous_cols is None else abs(cols - previous_cols)
            ideal_penalty = abs(cols - ideal_cols)
            # Prefer denser occupancy to reduce apparent gaps after relayout.
            empty_slots = (rows * cols) - count
            return (footprint_area, footprint_perimeter, previous_penalty, ideal_penalty, empty_slots)

        return min(feasible_cols, key=score)

    def _build_slots(self, work_rect: Rect, cell_width: int, cell_height: int, count: int) -> List[Rect]:
        """Build centered slots for exactly ``count`` windows with centered short final row."""
        if count <= 0:
            return []
        pitch_x = cell_width + self.gap
        pitch_y = cell_height + self.gap
        max_cols = max(1, (work_rect.width + self.gap) // pitch_x)
        max_rows = max(1, (work_rect.height + self.gap) // pitch_y)
        cols = self._select_column_count(count, cell_width, cell_height, max_cols, max_rows, work_rect)
        if cols <= 0:
            return []
        rows = (count + cols - 1) // cols
        total_width = (cols * cell_width) + ((cols - 1) * self.gap)
        total_height = (rows * cell_height) + ((rows - 1) * self.gap)
        start_y = work_rect.y + max(0, (work_rect.height - total_height) // 2)
        slots: List[Rect] = []
        remaining = count
        for row in range(rows):
            row_count = min(cols, remaining)
            row_width = (row_count * cell_width) + ((row_count - 1) * self.gap)
            row_start_x = work_rect.x + max(0, (work_rect.width - row_width) // 2)
            for col in range(row_count):
                x = row_start_x + (col * pitch_x)
                y = start_y + (row * pitch_y)
                slots.append(Rect(x, y, cell_width, cell_height))
                if len(slots) == count:
                    self._last_column_count = cols
                    return slots
            remaining -= row_count
        self._last_column_count = cols
        return slots

    def _center_window(self, window: "Window") -> None:
        """Center one window on screen when tiling cannot place it non-overlapping."""
        full_rect = Rect(0, 0, window.width, window.height + window.titlebar_size)
        full_rect.center = self.gui.surface.get_rect().center
        window.position = (full_rect.x, full_rect.y + window.titlebar_size)

    def _assign_slots(self, windows: List["Window"], slots: List[Rect]) -> Dict["Window", int]:
        """Assign slots deterministically by registration order of visible windows."""
        assignments: Dict["Window", int] = {}
        for slot_index, window in enumerate(windows):
            if slot_index >= len(slots):
                break
            assignments[window] = slot_index
        return assignments

    def _prune_removed_windows(self) -> None:
        """Drop cached registration state for windows no longer registered."""
        registered = set(self.gui.windows)
        self._registration_order_by_window = {
            window: order
            for window, order in self._registration_order_by_window.items()
            if window in registered
        }

    def arrange_windows(self, newly_visible: Optional[Iterable["Window"]] = None) -> None:
        """Apply tiling to visible windows or center newly visible windows on failure."""
        self._prune_removed_windows()
        visible_windows = self._visible_windows()
        visible_windows.sort(key=lambda window: self._registration_order_by_window[window])
        visible_set = set(visible_windows)
        if not self.enabled:
            return
        if len(visible_windows) == 0:
            self._last_column_count = None
            return
        if len(visible_windows) == 1:
            only_window = visible_windows[0]
            self._center_window(only_window)
            self._last_column_count = 1
            return

        work_rect = self._work_area_rect()
        if work_rect.width <= 0 or work_rect.height <= 0:
            return

        cell_width = max(window.width for window in visible_windows)
        cell_height = max(window.height + window.titlebar_size for window in visible_windows)

        requested_new = list(newly_visible or [])
        slots = self._build_slots(work_rect, cell_width, cell_height, len(visible_windows))
        if len(slots) < len(visible_windows):
            if self.center_on_failure:
                for window in requested_new:
                    if window in visible_set:
                        self._center_window(window)
            return
        assignments = self._assign_slots(visible_windows, slots)
        for window in visible_windows:
            slot_index = assignments.get(window)
            if slot_index is None:
                continue
            slot = slots[slot_index]
            window.position = (slot.x, slot.y + window.titlebar_size)

    def set_enabled(self, enabled: bool, relayout: bool = True) -> None:
        """Enable or disable window tiling and optionally apply immediately."""
        if not isinstance(enabled, bool):
            raise GuiError('window tiling enabled flag must be a bool')
        if not isinstance(relayout, bool):
            raise GuiError('window tiling relayout flag must be a bool')
        self.enabled = enabled
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
        """Update runtime tiling settings with strict validation."""
        if gap is not None:
            if not isinstance(gap, int) or gap < 0:
                raise GuiError(f'window tiling gap must be an int >= 0, got: {gap}')
            self.gap = gap
        if padding is not None:
            if not isinstance(padding, int) or padding < 0:
                raise GuiError(f'window tiling padding must be an int >= 0, got: {padding}')
            self.padding = padding
        if avoid_task_panel is not None:
            if not isinstance(avoid_task_panel, bool):
                raise GuiError('window tiling avoid_task_panel must be a bool')
            self.avoid_task_panel = avoid_task_panel
        if center_on_failure is not None:
            if not isinstance(center_on_failure, bool):
                raise GuiError('window tiling center_on_failure must be a bool')
            self.center_on_failure = center_on_failure
        if not isinstance(relayout, bool):
            raise GuiError('window tiling relayout flag must be a bool')
        if relayout:
            self.arrange_windows()

    def read_settings(self) -> Dict[str, object]:
        """Return current window tiling runtime settings."""
        return {
            'enabled': self.enabled,
            'gap': self.gap,
            'padding': self.padding,
            'avoid_task_panel': self.avoid_task_panel,
            'center_on_failure': self.center_on_failure,
        }
