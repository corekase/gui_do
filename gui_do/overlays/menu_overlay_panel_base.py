"""Internal menu-style overlay panel base with shared input and drawing behavior."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from ..controls.composite.overlay_panel_control import OverlayPanelControl
from ..events.gui_event import EventType, GuiEvent
from ..graphics.built_in_factory import BuiltInGraphicsFactory

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
        self._font_size = int(font_size)
        self._hovered_index = -1
        self._keyboard_index = -1
        self._draw_font: object = None     # cached SysFont(None, font_size)
        self._shadow_surface: object = None  # cached shadow Surface
        self._shadow_size: tuple = (0, 0)

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
            if not pygame.font.get_init():
                pygame.font.init()
            font = pygame.font.SysFont(None, int(font_size))
            item_text_padding = int(text_padding) * 2
            widths = []
            for item in items:
                if bool(getattr(item, "separator", False)):
                    continue
                label_width = font.size(str(getattr(item, "label", "")))[0]
                if bool(getattr(item, "_menu_window_checkbox", False)):
                    # 3px left inset + checkbox + 3px gap + text + 3px right padding.
                    line_h = int(item_height)
                    checkbox_size = max(1, line_h - 4)
                    widths.append(3 + checkbox_size + 3 + label_width + 3)
                elif bool(getattr(item, "_menu_scene_compact", False)):
                    # 3px left inset + text + 5px end gutter.
                    widths.append(3 + label_width + 5)
                else:
                    widths.append(label_width + item_text_padding + 16)
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

    def _hover_index_from_pointer(self, pointer_pos, rects: List[Rect]) -> int:
        if not (isinstance(pointer_pos, tuple) and len(pointer_pos) == 2):
            return -1
        for i, r in enumerate(rects):
            if r.collidepoint(pointer_pos) and not bool(getattr(self._items[i], "separator", False)):
                return i
        return -1

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

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
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
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if 0 <= self._keyboard_index < len(self._items):
                    self._activate_item(self._keyboard_index)
                return True

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        bg = getattr(theme, "panel", (45, 45, 55))
        text_col = theme.text
        disabled_col = (text_col[0] >> 1, text_col[1] >> 1, text_col[2] >> 1)
        hover_col = theme.highlight
        border_col = getattr(theme, "border", (80, 80, 90))

        if self._draw_font is None:
            self._draw_font = pygame.font.SysFont(None, self._font_size)
        font = self._draw_font
        graphics_factory = BuiltInGraphicsFactory(theme)

        shadow_size = (self.rect.width, self.rect.height)
        if self._shadow_surface is None or self._shadow_size != shadow_size:
            self._shadow_surface = pygame.Surface(shadow_size, pygame.SRCALPHA)
            self._shadow_surface.fill((0, 0, 0, 75))
            self._shadow_size = shadow_size
        surface.blit(self._shadow_surface, (self.rect.x + 3, self.rect.y + 3))

        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, border_col, self.rect, 1)

        rects = self._item_rects()
        pointer_pos = None
        app = getattr(self, '_last_app', None)
        if app is not None and hasattr(app, 'logical_pointer_pos'):
            pointer_pos = app.logical_pointer_pos
        else:
            pointer_pos = (0, 0)
        pointer_hovered = self._hover_index_from_pointer(pointer_pos, rects)
        draw_hovered_index = pointer_hovered if pointer_hovered >= 0 else self._hovered_index
        for i, (item, r) in enumerate(zip(self._items, rects)):
            if bool(getattr(item, "separator", False)):
                sy = r.y + r.height // 2
                pygame.draw.line(surface, border_col, (r.x + 8, sy), (r.right - 8, sy))
                continue
            if i == draw_hovered_index:
                pygame.draw.rect(surface, hover_col, r)
            col = text_col if bool(getattr(item, "enabled", True)) else disabled_col
            label = str(getattr(item, "label", ""))
            ts = font.render(label, True, col)
            if bool(getattr(item, "_menu_window_checkbox", False)):
                checkbox_area_size = max(1, int(r.height) - 4)
                checkbox_size = max(1, int(round(checkbox_area_size * 0.85)))
                checkbox_area_x = int(r.x) + 3
                checkbox_area_y = int(r.y) + (int(r.height) - checkbox_area_size) // 2
                checkbox_x = checkbox_area_x + (checkbox_area_size - checkbox_size) // 2
                checkbox_y = checkbox_area_y + (checkbox_area_size - checkbox_size) // 2
                checkbox_state = "idle"
                if i == draw_hovered_index:
                    checkbox_state = "hover"
                elif bool(getattr(item, "_menu_window_visible", False)):
                    checkbox_state = "armed"
                checkbox_bitmap = graphics_factory.draw_checkbox_bitmap(checkbox_state, checkbox_size)
                surface.blit(checkbox_bitmap, (checkbox_x, checkbox_y))
                text_x = checkbox_area_x + checkbox_area_size + 3
                surface.blit(ts, (text_x, r.y + (r.height - ts.get_height()) // 2))
            elif bool(getattr(item, "_menu_scene_compact", False)):
                surface.blit(ts, (int(r.x) + 3, r.y + (r.height - ts.get_height()) // 2))
            else:
                surface.blit(ts, (r.x + self._text_padding, r.y + (r.height - ts.get_height()) // 2))
