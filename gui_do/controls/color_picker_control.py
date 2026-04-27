"""ColorPickerControl — interactive HSV color picker with hex input."""
from __future__ import annotations

import colorsys
from typing import Callable, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme

# Layout constants
_HUE_W = 16         # width of the hue strip
_PREVIEW_H = 20     # height of the color preview bar at the bottom
_HEX_H = 24         # height of the hex input row
_PAD = 4            # inner padding
_HEX_W = 80         # width of the hex text field


class ColorPickerControl(UiNode):
    """Interactive HSV color picker control.

    Renders an SV (saturation × value) gradient square on the left, a vertical
    hue strip on the right, a color preview bar, and a hex text input.  All
    components are drawn inline — no overlays required.

    Usage::

        picker = ColorPickerControl(
            "pick", Rect(10, 10, 220, 200),
            color=(255, 128, 0),
            on_change=lambda rgb: print(rgb),
        )
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        color: Tuple[int, int, int] = (255, 0, 0),
        *,
        on_change: Optional[Callable[[Tuple[int, int, int]], None]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self.on_change = on_change
        self.tab_index = 0

        # Internal HSV state
        r, g, b = (max(0, min(255, int(c))) for c in color)
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self._hue: float = h
        self._sat: float = s
        self._val: float = v

        # Drag state
        self._dragging_sv: bool = False
        self._dragging_hue: bool = False

        # Hex edit state
        self._hex_editing: bool = False
        self._hex_text: str = self._rgb_to_hex(r, g, b)
        self._hex_error: bool = False

        # Gradient cache — invalidated when hue changes
        self._sv_surface: Optional[pygame.Surface] = None
        self._sv_surface_hue: float = -1.0
        self._sv_surface_size: Optional[Tuple[int, int]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def color(self) -> Tuple[int, int, int]:
        """Current color as an ``(r, g, b)`` tuple with values in 0–255."""
        return self._hsv_to_rgb()

    @color.setter
    def color(self, rgb: Tuple[int, int, int]) -> None:
        r, g, b = (max(0, min(255, int(c))) for c in rgb)
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self._hue = h
        self._sat = s
        self._val = v
        self._hex_text = self._rgb_to_hex(r, g, b)
        self._hex_error = False
        self.invalidate()

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled

    def update(self, dt_seconds: float) -> None:
        pass

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        sv_rect, hue_rect, _preview_rect, hex_rect = self._layout_rects()

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            pos = event.pos
            if pos is None:
                return False
            if not self.rect.collidepoint(pos):
                if self._hex_editing:
                    self._commit_hex()
                return False
            if sv_rect.collidepoint(pos):
                self._dragging_sv = True
                self._update_sv_from_pos(pos, sv_rect)
                return True
            if hue_rect.collidepoint(pos):
                self._dragging_hue = True
                self._update_hue_from_pos(pos, hue_rect)
                return True
            if hex_rect.collidepoint(pos):
                self._hex_editing = True
                self.invalidate()
                return True
            return True

        if event.kind == EventType.MOUSE_MOTION:
            pos = event.pos
            if pos is None:
                return False
            if self._dragging_sv:
                self._update_sv_from_pos(pos, sv_rect)
                return True
            if self._dragging_hue:
                self._update_hue_from_pos(pos, hue_rect)
                return True

        if event.kind == EventType.MOUSE_BUTTON_UP and event.button == 1:
            self._dragging_sv = False
            self._dragging_hue = False

        if event.kind == EventType.KEY_DOWN and self._focused:
            return self._handle_key(event.key)

        if event.kind == EventType.TEXT_INPUT and self._focused and self._hex_editing:
            char = event.text or ""
            allowed = set("0123456789abcdefABCDEF#")
            for ch in char:
                if ch in allowed and len(self._hex_text) < 7:
                    self._hex_text += ch
            self._hex_error = False
            self.invalidate()
            return True

        return False

    def _handle_key(self, key: int) -> bool:
        if self._hex_editing:
            if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
                self._commit_hex()
                return True
            if key == pygame.K_ESCAPE:
                self._hex_editing = False
                self._hex_text = self._rgb_to_hex(*self._hsv_to_rgb())
                self._hex_error = False
                self.invalidate()
                return True
            if key == pygame.K_BACKSPACE:
                self._hex_text = self._hex_text[:-1]
                self._hex_error = False
                self.invalidate()
                return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        sv_rect, hue_rect, preview_rect, hex_rect = self._layout_rects()

        # SV gradient square
        self._draw_sv_gradient(surface, sv_rect)
        # Draw SV cursor
        cx = sv_rect.x + int(self._sat * (sv_rect.width - 1))
        cy = sv_rect.y + int((1.0 - self._val) * (sv_rect.height - 1))
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 5, width=2)
        pygame.draw.circle(surface, (0, 0, 0), (cx, cy), 6, width=1)

        # Hue strip
        self._draw_hue_strip(surface, hue_rect)
        # Hue cursor line
        hy = hue_rect.y + int(self._hue * (hue_rect.height - 1))
        pygame.draw.line(surface, (255, 255, 255), (hue_rect.x, hy), (hue_rect.right - 1, hy), 2)

        # Color preview
        pygame.draw.rect(surface, self._hsv_to_rgb(), preview_rect)
        border = getattr(theme, "border", (80, 80, 80))
        if hasattr(border, "value"):
            border = border.value
        pygame.draw.rect(surface, border, preview_rect, width=1)

        # Hex input
        hex_bg = getattr(theme, "input_bg", (40, 40, 40))
        if hasattr(hex_bg, "value"):
            hex_bg = hex_bg.value
        if self._hex_editing:
            hex_bg = getattr(theme, "input_focused", (45, 45, 60))
            if hasattr(hex_bg, "value"):
                hex_bg = hex_bg.value
        pygame.draw.rect(surface, hex_bg, hex_rect, border_radius=2)
        hex_border = (200, 50, 50) if self._hex_error else border
        pygame.draw.rect(surface, hex_border, hex_rect, width=1, border_radius=2)
        font = pygame.font.SysFont(None, 16)
        text_color = getattr(theme, "text", (220, 220, 220))
        if hasattr(text_color, "value"):
            text_color = text_color.value
        display_hex = self._hex_text + ("|" if self._hex_editing else "")
        hex_surf = font.render(display_hex, True, text_color)
        surface.blit(hex_surf, (hex_rect.x + 3, hex_rect.centery - hex_surf.get_height() // 2))

        # Focus ring
        if self._focused:
            focus_color = getattr(theme, "focus_ring", (0, 150, 255))
            if hasattr(focus_color, "value"):
                focus_color = focus_color.value
            pygame.draw.rect(surface, focus_color, self.rect, width=1, border_radius=2)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _layout_rects(self) -> Tuple[Rect, Rect, Rect, Rect]:
        r = self.rect
        bottom_strip_h = _PREVIEW_H + _PAD + _HEX_H
        sv_h = max(1, r.height - bottom_strip_h - _PAD)
        sv_w = max(1, r.width - _HUE_W - _PAD)
        sv_rect = Rect(r.x, r.y, sv_w, sv_h)
        hue_rect = Rect(r.x + sv_w + _PAD, r.y, _HUE_W, sv_h)
        preview_rect = Rect(r.x, r.y + sv_h + _PAD, r.width, _PREVIEW_H)
        hex_rect = Rect(r.x, r.y + sv_h + _PAD + _PREVIEW_H + _PAD, _HEX_W, _HEX_H)
        return sv_rect, hue_rect, preview_rect, hex_rect

    # ------------------------------------------------------------------
    # Gradient rendering
    # ------------------------------------------------------------------

    def _draw_sv_gradient(self, surface: "pygame.Surface", sv_rect: Rect) -> None:
        w, h = sv_rect.width, sv_rect.height
        size = (w, h)
        if (
            self._sv_surface is None
            or self._sv_surface_hue != self._hue
            or self._sv_surface_size != size
        ):
            self._sv_surface = self._build_sv_surface(w, h, self._hue)
            self._sv_surface_hue = self._hue
            self._sv_surface_size = size
        surface.blit(self._sv_surface, (sv_rect.x, sv_rect.y))

    @staticmethod
    def _build_sv_surface(w: int, h: int, hue: float) -> "pygame.Surface":
        surf = pygame.Surface((max(1, w), max(1, h)))
        for sx in range(max(1, w)):
            s = sx / max(1, w - 1)
            for sy in range(max(1, h)):
                v = 1.0 - sy / max(1, h - 1)
                r, g, b = colorsys.hsv_to_rgb(hue, s, v)
                surf.set_at((sx, sy), (int(r * 255), int(g * 255), int(b * 255)))
        return surf

    @staticmethod
    def _draw_hue_strip(surface: "pygame.Surface", hue_rect: Rect) -> None:
        h = max(1, hue_rect.height)
        for sy in range(h):
            hue = sy / max(1, h - 1)
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color = (int(r * 255), int(g * 255), int(b * 255))
            pygame.draw.line(
                surface,
                color,
                (hue_rect.x, hue_rect.y + sy),
                (hue_rect.right - 1, hue_rect.y + sy),
            )

    # ------------------------------------------------------------------
    # Interaction helpers
    # ------------------------------------------------------------------

    def _update_sv_from_pos(self, pos: Tuple[int, int], sv_rect: Rect) -> None:
        s = (pos[0] - sv_rect.x) / max(1, sv_rect.width - 1)
        v = 1.0 - (pos[1] - sv_rect.y) / max(1, sv_rect.height - 1)
        self._sat = max(0.0, min(1.0, s))
        self._val = max(0.0, min(1.0, v))
        self._hex_text = self._rgb_to_hex(*self._hsv_to_rgb())
        self._hex_error = False
        self.invalidate()
        self._fire_change()

    def _update_hue_from_pos(self, pos: Tuple[int, int], hue_rect: Rect) -> None:
        h = (pos[1] - hue_rect.y) / max(1, hue_rect.height - 1)
        self._hue = max(0.0, min(1.0, h))
        self._sv_surface = None  # invalidate gradient cache
        self._hex_text = self._rgb_to_hex(*self._hsv_to_rgb())
        self._hex_error = False
        self.invalidate()
        self._fire_change()

    def _commit_hex(self) -> None:
        self._hex_editing = False
        text = self._hex_text.lstrip("#")
        try:
            if len(text) == 6:
                r = int(text[0:2], 16)
                g = int(text[2:4], 16)
                b = int(text[4:6], 16)
                h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
                self._hue = h
                self._sat = s
                self._val = v
                self._sv_surface = None
                self._hex_error = False
                self._fire_change()
            else:
                self._hex_error = True
        except ValueError:
            self._hex_error = True
        self.invalidate()

    def _fire_change(self) -> None:
        if self.on_change is not None:
            try:
                self.on_change(self._hsv_to_rgb())
            except Exception:
                pass

    def _hsv_to_rgb(self) -> Tuple[int, int, int]:
        r, g, b = colorsys.hsv_to_rgb(self._hue, self._sat, self._val)
        return (int(r * 255), int(g * 255), int(b * 255))

    @staticmethod
    def _rgb_to_hex(r: int, g: int, b: int) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"
