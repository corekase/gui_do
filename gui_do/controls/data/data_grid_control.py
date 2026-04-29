"""DataGridControl — multi-column virtualized table with sorting and keyboard nav."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ...events.gui_event import EventType, GuiEvent
from ..base._virtualized_scroll_list_base import _VirtualizedScrollListBase
from ...data.collection_view import CollectionView
from ..base._thumb_drag_lock import begin_thumb_drag, captured_pointer_pos, end_thumb_drag

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme


_HEADER_HEIGHT = 28
_ROW_HEIGHT = 26
_SCROLLBAR_WIDTH = 12
_MIN_COL_WIDTH = 20
_RESIZE_HIT_ZONE = 5


@dataclass
class GridColumn:
    """Descriptor for a single column in :class:`DataGridControl`."""

    key: str
    title: str
    width: int = 120
    sortable: bool = True
    min_width: int = _MIN_COL_WIDTH


@dataclass
class GridRow:
    """A single data row for :class:`DataGridControl`."""

    data: Dict[str, Any]
    row_id: Any = None


SelectRowCallback = Optional[Callable[[int, "GridRow"], None]]
SortCallback = Optional[Callable[[str, bool], None]]  # (column_key, ascending)


class DataGridControl(_VirtualizedScrollListBase):
    """Virtualized multi-column table control.

    Features
    --------
    - Scrollable rows with optional vertical scrollbar.
    - Header row with sort indicators; click a column header to sort.
    - Column resize by dragging the right edge of each header cell.
    - Single-row keyboard navigation (arrow keys, Page Up/Down, Home/End).
    - ``on_select`` callback when a row is activated by click or keyboard.
    - ``on_sort`` callback when the user changes the sort column/direction.
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        columns: Optional[List[GridColumn]] = None,
        rows: Optional[List[GridRow]] = None,
        *,
        row_height: int = _ROW_HEIGHT,
        show_scrollbar: bool = True,
        font_role: str = "medium",
        on_select: SelectRowCallback = None,
        on_sort: SortCallback = None,
    ) -> None:
        super().__init__(control_id, rect)
        self._columns: List[GridColumn] = list(columns) if columns else []
        self._rows: List[GridRow] = list(rows) if rows else []
        self._row_height: int = max(8, int(row_height))
        self._show_scrollbar: bool = bool(show_scrollbar)
        self._font_role: str = font_role
        self._on_select: SelectRowCallback = on_select
        self._on_sort: SortCallback = on_sort

        self._selected_row: int = -1

        self._sort_col: Optional[str] = None
        self._sort_asc: bool = True

        # Column resize state
        self._resize_col: Optional[int] = None  # index being resized
        self._resize_start_x: int = 0
        self._resize_start_w: int = 0

        # Hot-path caches
        self._col_offsets_cache: List[int] = [0]
        self._col_offsets_dirty: bool = True
        self._draw_font = None
        # Cache rendered text surfaces: (str_value, color_rgb) -> Surface.
        # Avoids re-rendering identical cell text on every frame.
        self._text_cache: Dict[tuple, "pygame.Surface"] = {}

        self.tab_index = 0

    # ------------------------------------------------------------------
    # Data API
    # ------------------------------------------------------------------

    def set_columns(self, columns: List[GridColumn]) -> None:
        self._columns = list(columns)
        self._col_offsets_dirty = True
        self.invalidate()

    def set_rows(self, rows: List[GridRow]) -> None:
        self._rows = list(rows)
        self._selected_row = -1
        self._scroll_offset = 0
        self.invalidate()

    def set_collection_view(self, cv: "CollectionView | None") -> None:
        """Populate rows from a :class:`~gui_do.core.collection_view.CollectionView`.

        Each item in *cv* is converted to a :class:`GridRow` if it is not
        already one — plain dicts become ``GridRow(data=item)`` and other
        values are wrapped as ``GridRow(data={"value": item})``.
        Pass ``None`` to clear without replacing the source.
        """
        if cv is None:
            self.set_rows([])
            return
        converted: List[GridRow] = []
        for item in cv.items:
            if isinstance(item, GridRow):
                converted.append(item)
            elif isinstance(item, dict):
                converted.append(GridRow(data=item))
            else:
                converted.append(GridRow(data={"value": item}))
        self.set_rows(converted)

    def bind_collection_view(
        self,
        cv: "CollectionView",
        on_refresh: Optional[Callable[[], None]] = None,
    ) -> Callable[[], None]:
        """Subscribe to *cv* so this control auto-updates whenever *cv* refreshes.

        Immediately populates the control from *cv* and registers a subscriber.
        Returns an unsub callable; call it to detach the live subscription.
        An optional *on_refresh* callback is fired after each sync.
        """
        self.set_collection_view(cv)

        def _on_cv_refresh() -> None:
            self.set_collection_view(cv)
            if on_refresh is not None:
                on_refresh()

        return cv.subscribe(_on_cv_refresh)

    def append_row(self, row: GridRow) -> None:
        self._rows.append(row)
        self.invalidate()

    def remove_row(self, index: int) -> bool:
        if not (0 <= index < len(self._rows)):
            return False
        self._rows.pop(index)
        if self._selected_row >= len(self._rows):
            self._selected_row = len(self._rows) - 1
        self.invalidate()
        return True

    def clear_rows(self) -> None:
        self._rows.clear()
        self._selected_row = -1
        self._scroll_offset = 0
        self.invalidate()

    @property
    def row_count(self) -> int:
        return len(self._rows)

    @property
    def rows(self) -> "List[GridRow]":
        return list(self._rows)

    @property
    def selected_row_index(self) -> int:
        return self._selected_row

    @property
    def selected_row(self) -> Optional[GridRow]:
        if 0 <= self._selected_row < len(self._rows):
            return self._rows[self._selected_row]
        return None

    # ------------------------------------------------------------------
    # Sort state
    # ------------------------------------------------------------------

    @property
    def sort_column(self) -> Optional[str]:
        return self._sort_col

    @property
    def sort_ascending(self) -> bool:
        return self._sort_asc

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _header_rect(self) -> Rect:
        return Rect(self.rect.x, self.rect.y, self.rect.width, _HEADER_HEIGHT)

    def _content_rect(self) -> Rect:
        x = self.rect.x
        y = self.rect.y + _HEADER_HEIGHT
        sb = _SCROLLBAR_WIDTH if self._show_scrollbar else 0
        w = self.rect.width - sb
        h = self.rect.height - _HEADER_HEIGHT
        return Rect(x, y, max(1, w), max(1, h))

    def _viewport_height(self) -> int:
        return max(1, self.rect.height - _HEADER_HEIGHT)

    def _content_height(self) -> int:
        return len(self._rows) * self._row_height

    def _scrollbar_rect(self) -> Optional[Rect]:
        if not (self._show_scrollbar and self._content_height() > self._viewport_height()):
            return None
        cr = self._content_rect()
        return Rect(cr.right, cr.y, _SCROLLBAR_WIDTH, cr.height)

    def _scrollbar_handle_rect(self) -> Optional[Rect]:
        sb_rect = self._scrollbar_rect()
        if sb_rect is None:
            return None
        ch = self._content_height()
        vh = self._viewport_height()
        ratio = vh / max(1, ch)
        thumb_h = max(16, int(vh * ratio))
        thumb_y = int(sb_rect.y + (self._scroll_offset / max(1, ch - vh)) * (sb_rect.height - thumb_h))
        return Rect(sb_rect.x + 2, thumb_y, sb_rect.width - 4, thumb_h)

    def _col_x_offsets(self) -> List[int]:
        """Return list of x pixel offsets (from content_rect.x) for each column."""
        if self._col_offsets_dirty:
            offsets = [0]
            for col in self._columns:
                offsets.append(offsets[-1] + col.width)
            self._col_offsets_cache = offsets
            self._col_offsets_dirty = False
        return self._col_offsets_cache

    def _col_at_x(self, x: int) -> int:
        """Return column index at pixel x relative to content_rect.x."""
        cr = self._content_rect()
        rx = x - cr.x
        cumulative = 0
        for i, col in enumerate(self._columns):
            cumulative += col.width
            if rx < cumulative:
                return i
        return len(self._columns) - 1

    def _row_at_y(self, y: int) -> int:
        """Return row index at pixel y relative to content area top."""
        return (y + self._scroll_offset) // self._row_height

    def _scroll_to_row(self, index: int) -> None:
        if not self._rows:
            return
        index = max(0, min(index, len(self._rows) - 1))
        top = index * self._row_height
        bottom = top + self._row_height
        vh = self._viewport_height()
        if top < self._scroll_offset:
            self._scroll_offset = top
        elif bottom > self._scroll_offset + vh:
            self._scroll_offset = bottom - vh
        self._clamp_scroll()

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled and self.tab_index >= 0

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            if self._scrollbar_dragging:
                end_thumb_drag(app, self.control_id)
            self._scrollbar_dragging = False
            return False

        event_pointer = event.pos if isinstance(event.pos, tuple) and len(event.pos) == 2 else None
        pointer = event_pointer if event_pointer is not None else app.logical_pointer_pos

        if event.kind == EventType.MOUSE_MOTION and self._scrollbar_dragging:
            pointer_pos = captured_pointer_pos(app, self.control_id, "y")
            if isinstance(pointer_pos, tuple) and len(pointer_pos) == 2:
                handle_rect = self._scrollbar_handle_rect()
                sb_rect = self._scrollbar_rect()
                if handle_rect is not None and sb_rect is not None:
                    top = pointer_pos[1] - self._scrollbar_drag_anchor
                    top = min(max(top, sb_rect.y), sb_rect.bottom - handle_rect.height)
                    self._set_scroll_from_handle_top(top)
                    return True

        if event.kind == EventType.MOUSE_BUTTON_UP and event.button == 1 and self._scrollbar_dragging:
            self._scrollbar_dragging = False
            end_thumb_drag(app, self.control_id)
            return True

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1 and isinstance(pointer, tuple) and len(pointer) == 2:
            handle_rect = self._scrollbar_handle_rect()
            sb_rect = self._scrollbar_rect()
            if handle_rect is not None and sb_rect is not None and handle_rect.collidepoint(pointer):
                self._scrollbar_dragging = True
                self._scrollbar_drag_anchor = begin_thumb_drag(
                    app,
                    self.control_id,
                    "y",
                    sb_rect,
                    (int(pointer[0]), int(pointer[1])),
                    handle_rect,
                )
                return True

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            return self._handle_mouse_down(event)

        if event.kind == EventType.MOUSE_MOTION:
            return self._handle_mouse_motion(event)

        if event.kind == EventType.MOUSE_BUTTON_UP and event.button == 1:
            if self._resize_col is not None:
                self._resize_col = None
                return True
            return False

        if event.kind == EventType.MOUSE_WHEEL:
            pointer = event.pos if isinstance(event.pos, tuple) and len(event.pos) == 2 else app.logical_pointer_pos
            if not (isinstance(pointer, tuple) and len(pointer) == 2 and self.rect.collidepoint(pointer)):
                return False
            delta = event.wheel_delta
            self._scroll_offset -= int(delta) * self._row_height * 3
            self._clamp_scroll()
            self.invalidate()
            return True

        if event.kind == EventType.KEY_DOWN and self._focused:
            return self._handle_key(event.key)

        return False

    def _handle_mouse_down(self, event: GuiEvent) -> bool:
        pos = event.pos
        header = self._header_rect()
        cr = self._content_rect()

        # --- Check header area ---
        if header.collidepoint(pos):
            # Check for column resize hot zones first
            offsets = self._col_x_offsets()
            for i, col in enumerate(self._columns):
                right_x = header.x + offsets[i + 1]
                if abs(pos[0] - right_x) <= _RESIZE_HIT_ZONE:
                    self._resize_col = i
                    self._resize_start_x = pos[0]
                    self._resize_start_w = col.width
                    return True
            # Otherwise, check sort click
            for i, col in enumerate(self._columns):
                col_x = header.x + offsets[i]
                col_rect = Rect(col_x, header.y, col.width, _HEADER_HEIGHT)
                if col_rect.collidepoint(pos) and col.sortable:
                    if self._sort_col == col.key:
                        self._sort_asc = not self._sort_asc
                    else:
                        self._sort_col = col.key
                        self._sort_asc = True
                    if self._on_sort is not None:
                        try:
                            self._on_sort(self._sort_col, self._sort_asc)
                        except Exception:
                            pass
                    self.invalidate()
                    return True
            return True

        # --- Content area ---
        if cr.collidepoint(pos):
            rel_y = pos[1] - cr.y
            idx = self._row_at_y(rel_y)
            if 0 <= idx < len(self._rows):
                self._selected_row = idx
                if self._on_select is not None:
                    try:
                        self._on_select(idx, self._rows[idx])
                    except Exception:
                        pass
                self.invalidate()
                return True
        return False

    def _handle_mouse_motion(self, event: GuiEvent) -> bool:
        if self._resize_col is None:
            return False
        dx = event.pos[0] - self._resize_start_x
        new_w = max(self._columns[self._resize_col].min_width, self._resize_start_w + dx)
        if self._columns[self._resize_col].width != new_w:
            self._columns[self._resize_col].width = new_w
            self._col_offsets_dirty = True
            self.invalidate()
        return True

    def _handle_key(self, key: int) -> bool:
        if not self._rows:
            return False
        cur = self._selected_row
        new_idx: Optional[int] = None
        if key == pygame.K_UP:
            new_idx = max(0, cur - 1) if cur > 0 else 0
        elif key == pygame.K_DOWN:
            new_idx = min(len(self._rows) - 1, cur + 1 if cur >= 0 else 0)
        elif key == pygame.K_HOME:
            new_idx = 0
        elif key == pygame.K_END:
            new_idx = len(self._rows) - 1
        elif key == pygame.K_PAGEUP:
            rows_per_page = max(1, self._viewport_height() // self._row_height)
            new_idx = max(0, (cur if cur >= 0 else 0) - rows_per_page)
        elif key == pygame.K_PAGEDOWN:
            rows_per_page = max(1, self._viewport_height() // self._row_height)
            new_idx = min(len(self._rows) - 1, (cur if cur >= 0 else 0) + rows_per_page)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER) and 0 <= cur < len(self._rows):
            if self._on_select is not None:
                try:
                    self._on_select(cur, self._rows[cur])
                except Exception:
                    pass
            return True

        if new_idx is not None and new_idx != cur:
            self._selected_row = new_idx
            self._scroll_to_row(new_idx)
            self.invalidate()
            return True
        return False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        bg = getattr(theme, "background", (30, 30, 30))
        header_bg = getattr(theme, "panel", (50, 50, 60))
        text_col = theme.text
        sel_col = theme.highlight
        border_col = getattr(theme, "border", (80, 80, 90))
        focus_col = getattr(theme, "focus", (100, 160, 255))

        if self._draw_font is None:
            try:
                self._draw_font = pygame.font.SysFont(None, 18)
                self._text_cache.clear()  # new font object; discard stale surfaces
            except Exception:
                self._draw_font = False
        font = self._draw_font
        r = self.rect
        pygame.draw.rect(surface, bg, r)

        header = self._header_rect()
        cr = self._content_rect()
        offsets = self._col_x_offsets()

        # --- Header ---
        pygame.draw.rect(surface, header_bg, header)
        for i, col in enumerate(self._columns):
            col_x = header.x + offsets[i]
            col_rect = Rect(col_x, header.y, col.width, _HEADER_HEIGHT)
            # Border right
            pygame.draw.line(surface, border_col, (col_x + col.width - 1, header.y), (col_x + col.width - 1, header.bottom - 1))
            title = col.title
            if col.sortable and self._sort_col == col.key:
                title += " ▲" if self._sort_asc else " ▼"
            if font:
                cache_key = (title, text_col)
                ts = self._text_cache.get(cache_key)
                if ts is None:
                    ts = font.render(title, True, text_col)
                    self._text_cache[cache_key] = ts
                surface.blit(ts, (col_rect.x + 4, col_rect.y + (col_rect.height - ts.get_height()) // 2))

        # Header bottom border
        pygame.draw.line(surface, border_col, (header.x, header.bottom - 1), (header.right, header.bottom - 1))

        # --- Rows (clipped to content rect) ---
        old_clip = surface.get_clip()
        surface.set_clip(cr.clip(old_clip) if old_clip else cr)

        row_height = self._row_height
        content_height = len(self._rows) * row_height
        viewport_height = max(1, self.rect.height - _HEADER_HEIGHT)
        first_row = self._scroll_offset // row_height
        last_row = min(len(self._rows), first_row + viewport_height // row_height + 2)

        for i in range(first_row, last_row):
            if i >= len(self._rows):
                break
            row = self._rows[i]
            row_y = cr.y + i * row_height - self._scroll_offset
            row_rect = Rect(cr.x, row_y, cr.width, row_height)

            if i == self._selected_row:
                pygame.draw.rect(surface, sel_col, row_rect)

            # Draw cells
            for j, col in enumerate(self._columns):
                col_x = cr.x + offsets[j]
                cell_rect = Rect(col_x, row_y, col.width, row_height)
                val = row.data.get(col.key, "")
                if font:
                    val_str = str(val)
                    cache_key = (val_str, text_col)
                    ts = self._text_cache.get(cache_key)
                    if ts is None:
                        ts = font.render(val_str, True, text_col)
                        self._text_cache[cache_key] = ts
                    surface.blit(ts, (cell_rect.x + 4, cell_rect.y + (cell_rect.height - ts.get_height()) // 2))
                # column separator
                pygame.draw.line(surface, border_col, (col_x + col.width - 1, row_y), (col_x + col.width - 1, row_y + row_height - 1))

            # row bottom border
            pygame.draw.line(surface, border_col, (cr.x, row_y + row_height - 1), (cr.x + cr.width, row_y + row_height - 1))

        surface.set_clip(old_clip)

        # --- Scrollbar (computed inline using already-derived cr/content/viewport) ---
        if self._show_scrollbar and content_height > viewport_height:
            sb_rect = Rect(cr.right, cr.y, _SCROLLBAR_WIDTH, cr.height)
            ratio = viewport_height / content_height
            thumb_h = max(16, int(viewport_height * ratio))
            travel = max(1, sb_rect.height - thumb_h)
            thumb_y = int(sb_rect.y + (self._scroll_offset / max(1, content_height - viewport_height)) * travel)
            handle_rect = Rect(sb_rect.x + 2, thumb_y, sb_rect.width - 4, thumb_h)
            pygame.draw.rect(surface, border_col, sb_rect)
            pygame.draw.rect(surface, sel_col, handle_rect)

        # --- Focus ring ---
        if self._focused:
            pygame.draw.rect(surface, focus_col, r, 2)
