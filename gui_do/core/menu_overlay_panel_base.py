"""Internal menu-style overlay panel base with shared input and drawing behavior."""
from __future__ import annotations

from typing import Callable, List, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..controls.overlay_panel_control import OverlayPanelControl
from .gui_event import EventType, GuiEvent

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class _MenuOverlayPanelBase(OverlayPanelControl):
    """Shared interaction and rendering for list-based overlay menus."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        items: List[object],
        on_close: Callable[[], None],
        *,
        item_height: int,
        separator_height: int,
        padding: int,
        text_padding: int,
        min_width: int,
        font_size: int,
    ) -> None:
        super().__init__(control_id, rect, draw_background=False)
        self._items = list(items)
        self._on_close = on_close
        self._item_height = int(item_height)
        self._separator_height = int(separator_height)
        self._padding = int(padding)
        self._text_padding = int(text_padding)
        self._min_width = int(min_width)
        self._font_size = int(font_size)
        self._hovered_index = -1
        self._keyboard_index = -1

    @classmethod
    def measure(
        cls,
        items: List[object],
        *,
        item_height: int,
        separator_height: int,
        padding: int,
        text_padding: int,
        min_width: int,
        font_size: int,
    ) -> Tuple[int, int]:
        h = int(padding) * 2
        for item in items:
            h += int(separator_height) if bool(getattr(item, "separator", False)) else int(item_height)
        try:
            font = pygame.font.SysFont(None, int(font_size))
            widths = [
                font.size(str(getattr(item, "label", "")))[0] + int(text_padding) * 2 + 16
                for item in items
                if not bool(getattr(item, "separator", False))
            ]
            if widths:
                return max(int(min_width), max(widths)), h
        except Exception:
            pass
        return int(min_width), h

    def _item_rects(self) -> List[Rect]:
        rects: List[Rect] = []
        y = self.rect.y + self._padding
        for item in self._items:
            h = self._separator_height if bool(getattr(item, "separator", False)) else self._item_height
            rects.append(Rect(self.rect.x, y, self.rect.width, h))
            y += h
        return rects

    def _selectable_indices(self) -> List[int]:
        return [
            i
            for i, item in enumerate(self._items)
            if not bool(getattr(item, "separator", False)) and bool(getattr(item, "enabled", True))
        ]

    def _activate_item(self, index: int) -> None:
        if 0 <= index < len(self._items):
            item = self._items[index]
            if not bool(getattr(item, "separator", False)) and bool(getattr(item, "enabled", True)):
                action = getattr(item, "action", None)
                if callable(action):
                    try:
                        self._on_close()
                        action()
                    except Exception:
                        pass
                    return
        self._on_close()

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        rects = self._item_rects()

        if event.kind == EventType.MOUSE_MOTION:
            self._hovered_index = -1
            for i, r in enumerate(rects):
                if r.collidepoint(event.pos) and not bool(getattr(self._items[i], "separator", False)):
                    self._hovered_index = i
                    self._keyboard_index = i
                    break
            self.invalidate()
            return self.rect.collidepoint(event.pos)

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            for i, r in enumerate(rects):
                if r.collidepoint(event.pos) and not bool(getattr(self._items[i], "separator", False)):
                    if bool(getattr(self._items[i], "enabled", True)):
                        self._activate_item(i)
                    return True
            return False

        if event.kind == EventType.KEY_DOWN:
            selectable = self._selectable_indices()
            if not selectable:
                return False
            if event.key == pygame.K_DOWN:
                nxt = [i for i in selectable if i > self._keyboard_index]
                self._keyboard_index = nxt[0] if nxt else selectable[0]
                self._hovered_index = self._keyboard_index
                self.invalidate()
                return True
            if event.key == pygame.K_UP:
                prev = [i for i in selectable if i < self._keyboard_index]
                self._keyboard_index = prev[-1] if prev else selectable[-1]
                self._hovered_index = self._keyboard_index
                self.invalidate()
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if 0 <= self._keyboard_index < len(self._items):
                    self._activate_item(self._keyboard_index)
                return True

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        def _c(name: str, fallback: Tuple) -> Tuple:
            v = getattr(theme, name, fallback)
            return v.value if hasattr(v, "value") else v

        bg = _c("panel", (45, 45, 55))
        text_col = _c("text", (220, 220, 220))
        disabled_col = tuple(max(0, min(255, c // 2)) for c in text_col)
        hover_col = _c("highlight", (0, 100, 200))
        border_col = _c("border", (80, 80, 90))

        font = pygame.font.SysFont(None, self._font_size)

        shadow = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 75))
        surface.blit(shadow, (self.rect.x + 3, self.rect.y + 3))

        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, border_col, self.rect, 1)

        rects = self._item_rects()
        for i, (item, r) in enumerate(zip(self._items, rects)):
            if bool(getattr(item, "separator", False)):
                sy = r.y + r.height // 2
                pygame.draw.line(surface, border_col, (r.x + 8, sy), (r.right - 8, sy))
                continue
            if i == self._hovered_index:
                pygame.draw.rect(surface, hover_col, r)
            col = text_col if bool(getattr(item, "enabled", True)) else disabled_col
            label = str(getattr(item, "label", ""))
            ts = font.render(label, True, col)
            surface.blit(ts, (r.x + self._text_padding, r.y + (r.height - ts.get_height()) // 2))
