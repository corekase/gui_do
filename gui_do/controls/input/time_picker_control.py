"""TimePickerControl — hour/minute selector with spin-button affordances."""
from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..base.ui_node import UiNode
from ...events.gui_event import EventType, GuiEvent

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme

# Ratios relative to the default font size.
_FONT_SCALE: float = 1.0             # time text size ratio
_FIELD_W_RATIO: float = 1.75        # width of each numeric field (hh / mm)
_SEP_W_RATIO: float = 0.75          # colon separator width
_SPIN_W_RATIO: float = 1.0          # spin arrow button width
_AMPM_W_RATIO: float = 2.0          # AM/PM toggle button width


class TimePickerControl(UiNode):
    """Hour/minute time picker with up/down spin buttons.

    Supports 24-hour mode (default) or 12-hour AM/PM mode.

    Usage::

        tp = TimePickerControl(
            "start_time", Rect(0, 0, 120, 30),
            hour=9, minute=30,
            on_change=lambda h, m: print(h, m),
        )
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        hour: int = 0,
        minute: int = 0,
        use_24h: bool = True,
        on_change: Optional[Callable[[int, int], None]] = None,
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect)
        self._hour = max(0, min(23, int(hour)))
        self._minute = max(0, min(59, int(minute)))
        self._use_24h = use_24h
        self._on_change = on_change
        self._font_role = font_role
        # "hour" or "minute" — which field is active
        self._active_field: str = "hour"
        # hover tracking
        self._hour_up_hov = False
        self._hour_dn_hov = False
        self._min_up_hov = False
        self._min_dn_hov = False
        self._ampm_hov = False
        self.tab_index = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def hour(self) -> int:
        return self._hour

    @property
    def minute(self) -> int:
        return self._minute

    @property
    def value(self) -> Tuple[int, int]:
        return (self._hour, self._minute)

    def set_time(self, hour: int, minute: int) -> None:
        old = (self._hour, self._minute)
        self._hour = max(0, min(23, int(hour)))
        self._minute = max(0, min(59, int(minute)))
        if old != (self._hour, self._minute):
            self.invalidate()
            if self._on_change:
                self._on_change(self._hour, self._minute)

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled

    def reconcile_hover(self, wants_hover: bool) -> None:
        if not wants_hover:
            changed = any([
                self._hour_up_hov, self._hour_dn_hov,
                self._min_up_hov, self._min_dn_hov, self._ampm_hov,
            ])
            self._hour_up_hov = False
            self._hour_dn_hov = False
            self._min_up_hov = False
            self._min_dn_hov = False
            self._ampm_hov = False
            if changed:
                self.invalidate()

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        self._hour_up_hov = False
        self._hour_dn_hov = False
        self._min_up_hov = False
        self._min_dn_hov = False
        self._ampm_hov = False
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        self._hour_up_hov = False
        self._hour_dn_hov = False
        self._min_up_hov = False
        self._min_dn_hov = False
        self._ampm_hov = False
        super()._on_visibility_changed(old_visible, new_visible)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            self._hour_up_hov = False
            self._hour_dn_hov = False
            self._min_up_hov = False
            self._min_dn_hov = False
            self._ampm_hov = False
            return False

        fonts = theme.fonts if (theme is not None and hasattr(theme, "fonts")) else None
        pos = event.pos
        rects = self._build_rects(fonts)

        if event.is_mouse_motion() and pos is not None:
            self._hour_up_hov = rects["h_up"].collidepoint(pos)
            self._hour_dn_hov = rects["h_dn"].collidepoint(pos)
            self._min_up_hov = rects["m_up"].collidepoint(pos)
            self._min_dn_hov = rects["m_dn"].collidepoint(pos)
            self._ampm_hov = not self._use_24h and rects["ampm"].collidepoint(pos)
            self.invalidate()
            return False

        if event.is_mouse_down(1) and pos is not None:
            if rects["h_field"].collidepoint(pos):
                self._active_field = "hour"
                self.invalidate()
                return True
            if rects["m_field"].collidepoint(pos):
                self._active_field = "minute"
                self.invalidate()
                return True
            if rects["h_up"].collidepoint(pos):
                self._step_hour(1)
                return True
            if rects["h_dn"].collidepoint(pos):
                self._step_hour(-1)
                return True
            if rects["m_up"].collidepoint(pos):
                self._step_minute(1)
                return True
            if rects["m_dn"].collidepoint(pos):
                self._step_minute(-1)
                return True
            if not self._use_24h and rects["ampm"].collidepoint(pos):
                self._toggle_ampm()
                return True

        if event.kind == EventType.KEY_DOWN and self._focused:
            key = event.key
            if key == pygame.K_LEFT:
                self._active_field = "hour"
                self.invalidate()
                return True
            if key == pygame.K_RIGHT:
                self._active_field = "minute"
                self.invalidate()
                return True
            if key == pygame.K_UP:
                if self._active_field == "hour":
                    self._step_hour(1)
                else:
                    self._step_minute(1)
                return True
            if key == pygame.K_DOWN:
                if self._active_field == "hour":
                    self._step_hour(-1)
                else:
                    self._step_minute(-1)
                return True

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        fonts = theme.fonts
        font_size = fonts.scaled_size(_FONT_SCALE)
        rects = self._build_rects(fonts)

        # Overall background
        full_r = self._full_rect(fonts)
        bg = theme.dark if not self.enabled else (theme.light if self._focused else theme.medium)
        pygame.draw.rect(surface, bg, full_r)
        border_color = theme.highlight if self._focused else theme.dark
        pygame.draw.rect(surface, border_color, full_r, 1)

        field_color = theme.dark if not self.enabled else theme.text

        # Hour field
        h_active = self._active_field == "hour" and self._focused and self.enabled
        if h_active:
            pygame.draw.rect(surface, theme.highlight, rects["h_field"])
        h_str = f"{self._hour:02d}" if self._use_24h else f"{self._display_hour():02d}"
        self._draw_field_text(surface, theme, h_str, rects["h_field"], font_size, field_color)

        # Separator
        sep_surf = theme.render_text(":", role=self._font_role, size=font_size, color=field_color)
        sep_x = rects["sep"].left + (rects["sep"].width - sep_surf.get_width()) // 2
        sep_y = rects["sep"].top + (rects["sep"].height - sep_surf.get_height()) // 2
        surface.blit(sep_surf, (sep_x, sep_y))

        # Minute field
        m_active = self._active_field == "minute" and self._focused and self.enabled
        if m_active:
            pygame.draw.rect(surface, theme.highlight, rects["m_field"])
        self._draw_field_text(surface, theme, f"{self._minute:02d}", rects["m_field"], font_size, field_color)

        # Spin buttons
        for key, hov_attr, label in [
            ("h_up", "_hour_up_hov", "▲"),
            ("h_dn", "_hour_dn_hov", "▼"),
            ("m_up", "_min_up_hov", "▲"),
            ("m_dn", "_min_dn_hov", "▼"),
        ]:
            spin_rect = rects[key]
            hov = getattr(self, hov_attr) and self.enabled
            spin_bg = theme.dark if not self.enabled else (theme.light if hov else theme.medium)
            pygame.draw.rect(surface, spin_bg, spin_rect)
            pygame.draw.rect(surface, theme.dark, spin_rect, 1)
            arrow_color = theme.dark if not self.enabled else theme.text
            arrow_surf = theme.render_text(label, role=self._font_role, size=font_size, color=arrow_color)
            ax = spin_rect.left + (spin_rect.width - arrow_surf.get_width()) // 2
            ay = spin_rect.top + (spin_rect.height - arrow_surf.get_height()) // 2
            surface.blit(arrow_surf, (ax, ay))

        # AM/PM toggle
        if not self._use_24h:
            ampm_rect = rects["ampm"]
            ampm_bg = theme.dark if not self.enabled else (theme.light if self._ampm_hov else theme.medium)
            pygame.draw.rect(surface, ampm_bg, ampm_rect)
            pygame.draw.rect(surface, theme.dark, ampm_rect, 1)
            ampm_label = "AM" if self._hour < 12 else "PM"
            ampm_surf = theme.render_text(ampm_label, role=self._font_role, size=font_size, color=field_color)
            ax = ampm_rect.left + (ampm_rect.width - ampm_surf.get_width()) // 2
            ay = ampm_rect.top + (ampm_rect.height - ampm_surf.get_height()) // 2
            surface.blit(ampm_surf, (ax, ay))
        # Focus ring
        if self._focused:
            pygame.draw.rect(surface, theme.highlight, full_r, 2)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw_field_text(self, surface, theme, text: str, field_rect: Rect, font_size: int, color) -> None:
        surf = theme.render_text(text, role=self._font_role, size=font_size, color=color)
        tx = field_rect.left + (field_rect.width - surf.get_width()) // 2
        ty = field_rect.top + (field_rect.height - surf.get_height()) // 2
        surface.blit(surf, (tx, ty))

    def _build_rects(self, fonts) -> dict:
        fs = fonts.scaled_size(_FONT_SCALE) if fonts else 16
        field_w = max(20, round(fs * _FIELD_W_RATIO))
        sep_w = max(8, round(fs * _SEP_W_RATIO))
        spin_w = max(12, round(fs * _SPIN_W_RATIO))
        ampm_w = max(24, round(fs * _AMPM_W_RATIO))
        field_h = self.rect.height
        arrow_h = max(1, field_h // 2)
        x = self.rect.left
        y = self.rect.top
        h_field = Rect(x, y, field_w, field_h)
        h_up = Rect(x + field_w, y, spin_w, arrow_h)
        h_dn = Rect(x + field_w, y + arrow_h, spin_w, field_h - arrow_h)
        x2 = x + field_w + spin_w
        sep = Rect(x2, y, sep_w, field_h)
        x3 = x2 + sep_w
        m_field = Rect(x3, y, field_w, field_h)
        m_up = Rect(x3 + field_w, y, spin_w, arrow_h)
        m_dn = Rect(x3 + field_w, y + arrow_h, spin_w, field_h - arrow_h)
        x4 = x3 + field_w + spin_w + 2
        ampm = Rect(x4, y, ampm_w, field_h)
        return {
            "h_field": h_field, "h_up": h_up, "h_dn": h_dn,
            "sep": sep,
            "m_field": m_field, "m_up": m_up, "m_dn": m_dn,
            "ampm": ampm,
        }

    def _full_rect(self, fonts) -> Rect:
        fs = fonts.scaled_size(_FONT_SCALE) if fonts else 16
        field_w = max(20, round(fs * _FIELD_W_RATIO))
        sep_w = max(8, round(fs * _SEP_W_RATIO))
        spin_w = max(12, round(fs * _SPIN_W_RATIO))
        ampm_w = max(24, round(fs * _AMPM_W_RATIO)) if not self._use_24h else 0
        total_w = (field_w + spin_w) * 2 + sep_w + (2 + ampm_w if ampm_w else 0)
        return Rect(self.rect.left, self.rect.top, total_w, self.rect.height)

    def _step_hour(self, delta: int) -> None:
        old = (self._hour, self._minute)
        self._hour = (self._hour + delta) % 24
        self.invalidate()
        if old != (self._hour, self._minute) and self._on_change:
            self._on_change(self._hour, self._minute)

    def _step_minute(self, delta: int) -> None:
        old = (self._hour, self._minute)
        self._minute = (self._minute + delta) % 60
        self.invalidate()
        if old != (self._hour, self._minute) and self._on_change:
            self._on_change(self._hour, self._minute)

    def _display_hour(self) -> int:
        h = self._hour % 12
        return 12 if h == 0 else h

    def _toggle_ampm(self) -> None:
        old = (self._hour, self._minute)
        self._hour = (self._hour + 12) % 24
        self.invalidate()
        if old != (self._hour, self._minute) and self._on_change:
            self._on_change(self._hour, self._minute)
