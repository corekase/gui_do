"""ListViewControl — virtualized scrollable list with selection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode
from ..layout.layout_axis import LayoutAxis

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


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


class ListViewControl(UiNode):
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
        self._scroll_offset: int = 0  # in pixels
        self.tab_index = 0

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

    def append_item(self, item: ListItem) -> None:
        self._items.append(item)
        self._ensure_selection_invariant()
        self.invalidate()

    def insert_item(self, index: int, item: ListItem) -> None:
        index = max(0, min(index, len(self._items)))
        self._items.insert(index, item)
        # Shift selected indices
        self._selected_indices = [
            (i + 1 if i >= index else i) for i in self._selected_indices
        ]
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
        elif index not in self._selected_indices:
            self._selected_indices.append(index)
        if scroll_to:
            self.scroll_to_item(index)
        if self._on_select is not None:
            try:
                self._on_select(index, self._items[index])
            except Exception:
                pass
        self.invalidate()

    def deselect_all(self) -> None:
        self._selected_indices = []
        self._ensure_selection_invariant()
        self.invalidate()

    def _ensure_selection_invariant(self) -> None:
        """Keep at least one item selected whenever the list has items."""
        if not self._items:
            self._selected_indices = []
            return
        valid = [i for i in self._selected_indices if 0 <= i < len(self._items)]
        if valid:
            self._selected_indices = valid
            return
        self._selected_indices = [0]

    def scroll_to_item(self, index: int) -> None:
        if not self._items:
            return
        index = max(0, min(index, len(self._items) - 1))
        item_top = index * self._row_height
        item_bottom = item_top + self._row_height
        vh = self._viewport_height()
        if item_top < self._scroll_offset:
            self._scroll_offset = item_top
        elif item_bottom > self._scroll_offset + vh:
            self._scroll_offset = item_bottom - vh
        self._clamp_scroll()
        self.invalidate()

    def scroll_to_top(self) -> None:
        self._scroll_offset = 0
        self.invalidate()

    def scroll_to_bottom(self) -> None:
        self._scroll_offset = self._max_scroll()
        self.invalidate()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _viewport_height(self) -> int:
        return max(1, self.rect.height)

    def _content_height(self) -> int:
        return len(self._items) * self._row_height

    def _max_scroll(self) -> int:
        return max(0, self._content_height() - self._viewport_height())

    def _clamp_scroll(self) -> None:
        self._scroll_offset = max(0, min(self._scroll_offset, self._max_scroll()))

    def _row_at_y(self, y: int) -> int:
        """Return item index at pixel y (relative to control top)."""
        return (y + self._scroll_offset) // self._row_height

    def _get_font(self, app: "Optional[GuiApplication]" = None) -> pygame.font.Font:
        try:
            if app is not None:
                attr = getattr(app.theme, self._font_role, None)
                if attr is not None and hasattr(attr, "render"):
                    return attr
        except Exception:
            pass
        return pygame.font.SysFont(None, 18)

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled and self.tab_index >= 0

    def update(self, dt_seconds: float) -> None:
        pass

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            pos = event.pos
            if not self.rect.collidepoint(pos):
                return False
            rel_y = pos[1] - self.rect.y
            idx = self._row_at_y(rel_y)
            if 0 <= idx < len(self._items) and self._items[idx].enabled:
                self._toggle_or_select(idx)
                return True
            return False

        if event.kind == EventType.MOUSE_WHEEL:
            delta = getattr(event, "y", 0)
            self._scroll_offset -= int(delta) * self._row_height * 3
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
        else:
            if not self._multi_select:
                self._selected_indices = [idx]
            elif idx not in self._selected_indices:
                self._selected_indices.append(idx)
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
        bg_color = getattr(theme, "background", (30, 30, 30))
        if hasattr(bg_color, "value"):
            bg_color = bg_color.value
        pygame.draw.rect(surface, bg_color, r)

        font = pygame.font.SysFont(None, 18)
        vh = self._viewport_height()
        first_row = self._scroll_offset // self._row_height
        last_row = min(len(self._items), first_row + vh // self._row_height + 2)

        clip = surface.get_clip()
        surface.set_clip(r)

        for i in range(first_row, last_row):
            if i >= len(self._items):
                break
            item = self._items[i]
            row_y = r.y + i * self._row_height - self._scroll_offset
            row_rect = Rect(r.x, row_y, r.width, self._row_height)

            if i in self._selected_indices:
                sel_color = getattr(theme, "highlight", (0, 100, 200))
                if hasattr(sel_color, "value"):
                    sel_color = sel_color.value
                pygame.draw.rect(surface, sel_color, row_rect)

            text_color = getattr(theme, "text", (220, 220, 220))
            if hasattr(text_color, "value"):
                text_color = text_color.value
            if not item.enabled:
                text_color = tuple(max(0, min(255, c // 2)) for c in text_color)
            text_surf = font.render(item.label, True, text_color)
            surface.blit(text_surf, (row_rect.x + 4, row_rect.y + (self._row_height - text_surf.get_height()) // 2))

        surface.set_clip(clip)
