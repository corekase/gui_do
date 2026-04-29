"""ListViewControl — virtualized scrollable list with selection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ...events.gui_event import EventType, GuiEvent
from ..base._virtualized_scroll_list_base import _VirtualizedScrollListBase
from ...data.collection_view import CollectionView
from ..base._thumb_drag_lock import begin_thumb_drag, captured_pointer_pos, end_thumb_drag

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme


@dataclass
class ListItem:
    label: str
    value: Any = field(default=None)
    enabled: bool = True
    data: Any = None

    def __post_init__(self) -> None:
        if self.value is None:
            self.value = self.label


SelectCallback = Optional[Callable[[int, "ListItem"], None]]

_SCROLLBAR_WIDTH = 12


class ListViewControl(_VirtualizedScrollListBase):
    """Virtualized list control with single or multi-select."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        items: Optional[List[ListItem]] = None,
        *,
        row_height: int = 28,
        selected_index: int = -1,
        on_select: SelectCallback = None,
        multi_select: bool = False,
        show_scrollbar: bool = True,
        font_role: str = "medium",
    ) -> None:
        super().__init__(control_id, rect)
        self._items: List[ListItem] = list(items) if items else []
        self._row_height: int = max(8, int(row_height))
        self._on_select: SelectCallback = on_select
        self._multi_select: bool = bool(multi_select)
        self._show_scrollbar: bool = bool(show_scrollbar)
        self._font_role: str = font_role
        self._selected_indices: List[int] = []
        self._selected_set: set = set()
        self.tab_index = 0
        self._draw_font: object = None  # cached from pygame.font.SysFont(None, 18)

        if 0 <= selected_index < len(self._items):
            self._selected_indices = [selected_index]
        self._ensure_selection_invariant()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def items(self) -> List[ListItem]:
        return list(self._items)

    @property
    def selected_index(self) -> int:
        return self._selected_indices[0] if self._selected_indices else -1

    @selected_index.setter
    def selected_index(self, value: int) -> None:
        if 0 <= value < len(self._items):
            self._selected_indices = [value]
        else:
            self._selected_indices = []
        self._ensure_selection_invariant()
        self.invalidate()

    @property
    def selected_indices(self) -> List[int]:
        return list(self._selected_indices)

    @property
    def selected_item(self) -> Optional[ListItem]:
        idx = self.selected_index
        if 0 <= idx < len(self._items):
            return self._items[idx]
        return None

    @property
    def scroll_offset(self) -> int:
        return self._scroll_offset

    # ------------------------------------------------------------------
    # Mutation API
    # ------------------------------------------------------------------

    def set_items(self, items: List[ListItem]) -> None:
        self._items = list(items)
        self._selected_indices = []
        self._ensure_selection_invariant()
        self._scroll_offset = 0
        self.invalidate()

    def set_collection_view(self, cv: "CollectionView | None") -> None:
        """Populate the list from a :class:`~gui_do.core.collection_view.CollectionView`.

        Converts each item in *cv* to a :class:`ListItem` if it is not already
        one (using ``str(item)`` for the label and the raw item as the value).
        Pass ``None`` to clear without replacing the source.
        """
        if cv is None:
            self.set_items([])
            return
        converted: List[ListItem] = []
        for item in cv.items:
            if isinstance(item, ListItem):
                converted.append(item)
            else:
                converted.append(ListItem(label=str(item), value=item))
        self.set_items(converted)

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

    def append_item(self, item: ListItem) -> None:
        self._items.append(item)
        self._ensure_selection_invariant()
        self.invalidate()

    def remove_item(self, index: int) -> bool:
        if not (0 <= index < len(self._items)):
            return False
        self._items.pop(index)
        self._selected_indices = [
            (i - 1 if i > index else i) for i in self._selected_indices if i != index
        ]
        self._ensure_selection_invariant()
        self.invalidate()
        return True

    def item_count(self) -> int:
        return len(self._items)

    def select(self, index: int, *, scroll_to: bool = True) -> None:
        if not (0 <= index < len(self._items)):
            return
        if not self._multi_select:
            self._selected_indices = [index]
            self._selected_set = {index}
        elif index not in self._selected_indices:
            self._selected_indices.append(index)
            self._selected_set.add(index)
        if scroll_to:
            self.scroll_to_item(index)
        if self._on_select is not None:
            try:
                self._on_select(index, self._items[index])
            except Exception:
                pass
        self.invalidate()

    def _ensure_selection_invariant(self) -> None:
        """Keep at least one item selected whenever the list has items."""
        if not self._items:
            self._selected_indices = []
            self._selected_set = set()
            return
        valid = [i for i in self._selected_indices if 0 <= i < len(self._items)]
        if valid:
            self._selected_indices = valid
            self._selected_set = set(valid)
            return
        self._selected_indices = [0]
        self._selected_set = {0}

    def scroll_to_item(self, index: int) -> None:
        if not self._items:
            return
        index = max(0, min(index, len(self._items) - 1))
        if self._try_scroll_parent_to_item(index):
            self.invalidate()
            return
        item_top = index * self._row_height
        item_bottom = item_top + self._row_height
        vh = self._viewport_height()
        if item_top < self._scroll_offset:
            self._scroll_offset = item_top
        elif item_bottom > self._scroll_offset + vh:
            self._scroll_offset = item_bottom - vh
        self._clamp_scroll()
        self.invalidate()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _viewport_height(self) -> int:
        parent_scroll = self._parent_scroll_view()
        if parent_scroll is not None:
            try:
                parent_vh = int(parent_scroll._viewport_h())
                return max(1, min(int(self.rect.height), parent_vh))
            except Exception:
                pass
        return max(1, self.rect.height)

    def _parent_scroll_view(self):
        parent = self.parent
        if parent is None:
            return None
        required = ("set_scroll", "scroll_y", "_viewport_h", "children", "_child_content_rects")
        if all(hasattr(parent, name) for name in required):
            return parent
        return None

    def _try_scroll_parent_to_item(self, index: int) -> bool:
        parent_scroll = self._parent_scroll_view()
        if parent_scroll is None or self._show_scrollbar:
            return False
        try:
            child_idx = parent_scroll.children.index(self)
            content_rect = parent_scroll._child_content_rects[child_idx]
            parent_view_h = int(parent_scroll._viewport_h())
            parent_scroll_y = int(parent_scroll.scroll_y)
        except Exception:
            return False

        item_top = int(content_rect.y) + (int(index) * self._row_height)
        item_bottom = item_top + self._row_height
        viewport_bottom = parent_scroll_y + parent_view_h

        if item_top < parent_scroll_y:
            parent_scroll.set_scroll(y=item_top)
            return True
        if item_bottom > viewport_bottom:
            parent_scroll.set_scroll(y=item_bottom - parent_view_h)
            return True
        return True

    def _content_height(self) -> int:
        return len(self._items) * self._row_height

    def _content_rect(self) -> Rect:
        width = self.rect.width
        if self._scrollbar_rect() is not None:
            width -= _SCROLLBAR_WIDTH
        return Rect(self.rect.x, self.rect.y, max(1, width), self.rect.height)

    def _scrollbar_rect(self) -> Optional[Rect]:
        if not self._show_scrollbar:
            return None
        if self._content_height() <= self._viewport_height():
            return None
        return Rect(self.rect.right - _SCROLLBAR_WIDTH, self.rect.y, _SCROLLBAR_WIDTH, self.rect.height)

    def _scrollbar_handle_rect(self) -> Optional[Rect]:
        sb_rect = self._scrollbar_rect()
        if sb_rect is None:
            return None
        content_h = self._content_height()
        viewport_h = self._viewport_height()
        handle_h = max(16, int(viewport_h * viewport_h / max(1, content_h)))
        max_scroll = max(1, content_h - viewport_h)
        handle_y = sb_rect.y + int((sb_rect.height - handle_h) * self._scroll_offset / max_scroll)
        return Rect(sb_rect.x + 2, handle_y, _SCROLLBAR_WIDTH - 4, handle_h)

    def _row_at_y(self, y: int) -> int:
        """Return item index at pixel y (relative to control top)."""
        return (y + self._scroll_offset) // self._row_height

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
            pos = event.pos
            if not self.rect.collidepoint(pos):
                return False
            sb_rect = self._scrollbar_rect()
            if sb_rect is not None and sb_rect.collidepoint(pos):
                return True
            content_rect = self._content_rect()
            if not content_rect.collidepoint(pos):
                return False
            rel_y = pos[1] - self.rect.y
            idx = self._row_at_y(rel_y)
            if 0 <= idx < len(self._items) and self._items[idx].enabled:
                self._toggle_or_select(idx)
                return True
            return False

        if event.kind == EventType.MOUSE_WHEEL:
            pointer = event.pos if isinstance(event.pos, tuple) and len(event.pos) == 2 else app.logical_pointer_pos
            if not (isinstance(pointer, tuple) and len(pointer) == 2 and self.rect.collidepoint(pointer)):
                return False
            if self._parent_scroll_view() is not None and not self._show_scrollbar:
                # Embedded lists can delegate wheel scrolling to parent scrollviews.
                return False
            if self._max_scroll() <= 0:
                return False
            delta = event.wheel_y
            self._scroll_offset -= int(delta) * self._row_height
            self._clamp_scroll()
            self.invalidate()
            return True

        if event.kind == EventType.KEY_DOWN and self._focused:
            return self._handle_key(event.key, event.mod)

        return False

    def _toggle_or_select(self, idx: int) -> None:
        if self._multi_select and idx in self._selected_indices:
            # Preserve at least one selected item when list has content.
            if len(self._selected_indices) > 1:
                self._selected_indices.remove(idx)
                self._selected_set.discard(idx)
        else:
            if not self._multi_select:
                self._selected_indices = [idx]
                self._selected_set = {idx}
            elif idx not in self._selected_indices:
                self._selected_indices.append(idx)
                self._selected_set.add(idx)
        self._ensure_selection_invariant()
        if self._on_select is not None:
            try:
                self._on_select(idx, self._items[idx])
            except Exception:
                pass
        self.invalidate()

    def _handle_key(self, key: int, mod: int) -> bool:
        if not self._items:
            return False
        current = self.selected_index
        new_idx: Optional[int] = None
        if key == pygame.K_UP:
            new_idx = max(0, current - 1) if current > 0 else 0
        elif key == pygame.K_DOWN:
            new_idx = min(len(self._items) - 1, current + 1 if current >= 0 else 0)
        elif key == pygame.K_HOME:
            new_idx = 0
        elif key == pygame.K_END:
            new_idx = len(self._items) - 1
        elif key == pygame.K_PAGEUP:
            rows = max(1, self._viewport_height() // self._row_height)
            new_idx = max(0, (current if current >= 0 else 0) - rows)
        elif key == pygame.K_PAGEDOWN:
            rows = max(1, self._viewport_height() // self._row_height)
            new_idx = min(len(self._items) - 1, (current if current >= 0 else 0) + rows)
        elif key == pygame.K_SPACE and self._multi_select and current >= 0:
            self._toggle_or_select(current)
            return True
        if new_idx is not None and new_idx != current:
            self.select(new_idx, scroll_to=True)
            return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return
        r = self.rect
        # Background
        bg_color = theme.background
        pygame.draw.rect(surface, bg_color, r)

        if self._draw_font is None:
            self._draw_font = pygame.font.SysFont(None, 18)
        font = self._draw_font
        vh = self._viewport_height()
        if self._parent_scroll_view() is not None and not self._show_scrollbar:
            # Parent ScrollView movement determines visibility; render full list
            # so clip-based culling can show the correct rows at all offsets.
            first_row = 0
            last_row = len(self._items)
        else:
            first_row = self._scroll_offset // self._row_height
            last_row = min(len(self._items), first_row + vh // self._row_height + 2)

        content_w = r.width
        if self._scrollbar_rect() is not None:
            content_w = max(1, content_w - _SCROLLBAR_WIDTH)
        content_rect = Rect(r.x, r.y, content_w, r.height)

        clip = surface.get_clip()
        surface.set_clip(content_rect.clip(clip) if clip else content_rect)

        for i in range(first_row, last_row):
            if i >= len(self._items):
                break
            item = self._items[i]
            row_y = r.y + i * self._row_height - self._scroll_offset
            row_rect = Rect(content_rect.x, row_y, content_rect.width, self._row_height)

            if i in self._selected_set:
                pygame.draw.rect(surface, theme.highlight, row_rect)

            text_color = theme.text
            if not item.enabled:
                text_color = (text_color[0] >> 1, text_color[1] >> 1, text_color[2] >> 1)
            text_surf = font.render(item.label, True, text_color)
            surface.blit(text_surf, (row_rect.x + 4, row_rect.y + (self._row_height - text_surf.get_height()) // 2))

        surface.set_clip(clip)

        sb_rect = self._scrollbar_rect()
        handle_rect = self._scrollbar_handle_rect()
        if sb_rect is not None and handle_rect is not None:
            pygame.draw.rect(surface, theme.dark, sb_rect)
            pygame.draw.rect(surface, theme.medium, handle_rect, border_radius=2)
