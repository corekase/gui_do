"""DatePickerControl — date entry field with inline calendar popup."""
from __future__ import annotations

import calendar
from datetime import date
from typing import Callable, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..base.ui_node import UiNode
from ...events.gui_event import EventType, GuiEvent

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme

# All calendar geometry is computed from the active font size so the picker
# scales with the application's typographic settings.
_FONT_SCALE: float = 0.875         # date text size ratio (slightly smaller — fits 7 columns)
_FIELD_H_RATIO: float = 1.875     # height of the text field relative to font size
_BTN_W_RATIO: float = 1.75        # calendar-icon button width ratio
_CAL_HEADER_H_RATIO: float = 1.5  # calendar header row height ratio
_DAY_LABEL_H_RATIO: float = 1.25  # day-of-week label row height ratio
_CELL_W_RATIO: float = 1.75       # calendar cell width (cols = 7, so total = 7 * ratio * font_size)
_CELL_H_RATIO: float = 1.5        # calendar cell height ratio
_CAL_NAV_BTN_W_RATIO: float = 1.5 # prev/next navigation button width ratio

_DAY_NAMES = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")


class DatePickerControl(UiNode):
    """Date input field with an inline calendar popup.

    The field displays the selected date in ISO format (YYYY-MM-DD).
    Clicking the calendar icon (or the field) opens the popup inline below.

    Usage::

        picker = DatePickerControl(
            "birthday", Rect(0, 0, 180, 30),
            value=date(2026, 1, 1),
            on_change=lambda d: print(d),
        )
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        value: Optional[date] = None,
        min_date: Optional[date] = None,
        max_date: Optional[date] = None,
        on_change: Optional[Callable[[date], None]] = None,
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect)
        self._value: date = value or date.today()
        self._min_date = min_date
        self._max_date = max_date
        self._on_change = on_change
        self._font_role = font_role
        self._open = False
        # Calendar nav state — shown month
        self._nav_year = self._value.year
        self._nav_month = self._value.month
        # Hover state
        self._btn_hovered = False
        self._field_hovered = False
        self._cal_hovered_day: Optional[int] = None   # 1-based or None
        self.tab_index = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def value(self) -> date:
        return self._value

    @value.setter
    def value(self, v: date) -> None:
        if not isinstance(v, date):
            raise TypeError("value must be a datetime.date instance")
        v = self._clamp(v)
        if self._value == v:
            return
        self._value = v
        self._nav_year = v.year
        self._nav_month = v.month
        self.invalidate()

    def set_value(self, v: date) -> None:
        self.value = v

    def close(self) -> None:
        if self._open:
            self._open = False
            self.invalidate()

    def open(self) -> None:
        if not self._open:
            self._open = True
            self._nav_year = self._value.year
            self._nav_month = self._value.month
            self.invalidate()

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled

    def reconcile_hover(self, wants_hover: bool) -> None:
        if not wants_hover:
            changed = self._btn_hovered or self._field_hovered
            self._btn_hovered = False
            self._field_hovered = False
            if changed:
                self.invalidate()

    def on_focus_changed(self, is_focused: bool) -> None:
        if is_focused:
            return
        changed = self._open or self._cal_hovered_day is not None
        self._open = False
        self._cal_hovered_day = None
        if changed:
            self.invalidate()

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        self._btn_hovered = False
        self._field_hovered = False
        self._open = False
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        self._btn_hovered = False
        self._field_hovered = False
        self._open = False
        super()._on_visibility_changed(old_visible, new_visible)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            self._open = False
            return False

        fonts = theme.fonts if (theme is not None and hasattr(theme, "fonts")) else None
        field_h, btn_w = self._field_dims(fonts)
        field_rect = Rect(self.rect.left, self.rect.top, self.rect.width - btn_w, field_h)
        btn_rect = Rect(self.rect.right - btn_w, self.rect.top, btn_w, field_h)
        pos = event.pos

        if event.is_mouse_motion() and pos is not None:
            new_fld = field_rect.collidepoint(pos)
            new_btn = btn_rect.collidepoint(pos)
            if self._open:
                self._update_cal_hover(pos, fonts)
            if new_fld != self._field_hovered or new_btn != self._btn_hovered:
                self._field_hovered = new_fld
                self._btn_hovered = new_btn
                self.invalidate()
            return False

        if event.is_mouse_down(1) and pos is not None:
            if btn_rect.collidepoint(pos) or field_rect.collidepoint(pos):
                if self._open:
                    self.close()
                else:
                    self.open()
                return True

            if self._open:
                cal_rect = self._calendar_rect(fonts)
                if cal_rect.collidepoint(pos):
                    return self._handle_cal_click(pos, cal_rect, fonts)
                else:
                    self.close()
            return False

        if event.kind == EventType.KEY_DOWN and self._focused:
            if event.key == pygame.K_ESCAPE and self._open:
                self.close()
                return True
            if event.key == pygame.K_RETURN and not self._open:
                self.open()
                return True

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        r = self.rect
        fonts = theme.fonts
        font_size = fonts.scaled_size(_FONT_SCALE)
        field_h, btn_w = self._field_dims(fonts)
        field_w = r.width - btn_w

        # Field background
        field_rect = Rect(r.left, r.top, field_w, field_h)
        if not self.enabled:
            bg = theme.dark
        elif self._focused:
            bg = theme.light
        else:
            bg = theme.medium
        pygame.draw.rect(surface, bg, field_rect)
        border_color = theme.highlight if self._focused else theme.dark
        pygame.draw.rect(surface, border_color, field_rect, 1)

        # Focus ring
        if self._focused:
            full = Rect(r.left, r.top, r.width, field_h)
            pygame.draw.rect(surface, theme.highlight, full, 2)

        # Value text
        val_color = theme.dark if not self.enabled else theme.text
        val_surf = theme.render_text(
            self._value.isoformat(), role=self._font_role,
            size=font_size, color=val_color,
        )
        ty = field_rect.top + (field_h - val_surf.get_height()) // 2
        surface.blit(val_surf, (field_rect.left + 6, ty))

        # Calendar icon button
        btn_rect = Rect(r.right - btn_w, r.top, btn_w, field_h)
        btn_bg = theme.dark if not self.enabled else (theme.light if self._btn_hovered else theme.medium)
        pygame.draw.rect(surface, btn_bg, btn_rect)
        pygame.draw.rect(surface, theme.dark, btn_rect, 1)
        # Tiny calendar icon
        ic_x = btn_rect.left + btn_rect.width // 2 - 6
        ic_y = btn_rect.top + btn_rect.height // 2 - 6
        ico_color = theme.dark if not self.enabled else theme.text
        pygame.draw.rect(surface, ico_color, Rect(ic_x, ic_y, 12, 10), 1)
        pygame.draw.line(surface, ico_color, (ic_x + 3, ic_y - 2), (ic_x + 3, ic_y + 1))
        pygame.draw.line(surface, ico_color, (ic_x + 8, ic_y - 2), (ic_x + 8, ic_y + 1))
        pygame.draw.line(surface, ico_color, (ic_x, ic_y + 4), (ic_x + 11, ic_y + 4))

        # Calendar popup
        if self._open:
            self._draw_calendar(surface, theme, fonts)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clamp(self, d: date) -> date:
        if self._min_date and d < self._min_date:
            return self._min_date
        if self._max_date and d > self._max_date:
            return self._max_date
        return d

    def _field_dims(self, fonts) -> tuple:
        """Return (field_h, btn_w) from font metrics."""
        if fonts is None:
            return 30, 28
        field_h = max(20, fonts.scaled_size(_FIELD_H_RATIO))
        btn_w = max(20, fonts.scaled_size(_BTN_W_RATIO))
        return field_h, btn_w

    def _calendar_rect(self, fonts) -> Rect:
        font_size = fonts.scaled_size(_FONT_SCALE) if fonts is not None else 14
        cell_w = max(16, round(font_size * _CELL_W_RATIO))
        cal_w = cell_w * 7
        header_h = max(20, round(font_size * _CAL_HEADER_H_RATIO))
        day_lbl_h = max(14, round(font_size * _DAY_LABEL_H_RATIO))
        cell_h = max(14, round(font_size * _CELL_H_RATIO))
        cal_h = header_h + day_lbl_h + cell_h * 6
        field_h, _ = self._field_dims(fonts)
        return Rect(self.rect.left, self.rect.top + field_h, cal_w, cal_h)

    def _update_cal_hover(self, pos: tuple, fonts) -> None:
        cr = self._calendar_rect(fonts)
        if not cr.collidepoint(pos):
            if self._cal_hovered_day is not None:
                self._cal_hovered_day = None
                self.invalidate()
            return
        day = self._pos_to_day(pos, cr, fonts)
        if day != self._cal_hovered_day:
            self._cal_hovered_day = day
            self.invalidate()

    def _handle_cal_click(self, pos: tuple, cal_rect: Rect, fonts) -> bool:
        font_size = fonts.scaled_size(_FONT_SCALE) if fonts else 14
        header_h = max(20, round(font_size * _CAL_HEADER_H_RATIO))
        nav_w = max(16, round(font_size * _CAL_NAV_BTN_W_RATIO))
        prev_rect = Rect(cal_rect.left, cal_rect.top, nav_w, header_h)
        next_rect = Rect(cal_rect.right - nav_w, cal_rect.top, nav_w, header_h)
        if prev_rect.collidepoint(pos):
            self._nav_prev()
            return True
        if next_rect.collidepoint(pos):
            self._nav_next()
            return True
        day = self._pos_to_day(pos, cal_rect, fonts)
        if day is not None:
            try:
                new_date = self._clamp(date(self._nav_year, self._nav_month, day))
                old = self._value
                self._value = new_date
                self._nav_year = new_date.year
                self._nav_month = new_date.month
                self._open = False
                self.invalidate()
                if old != new_date and self._on_change:
                    self._on_change(new_date)
                return True
            except ValueError:
                pass
        return True

    def _nav_prev(self) -> None:
        if self._nav_month == 1:
            self._nav_month = 12
            self._nav_year -= 1
        else:
            self._nav_month -= 1
        self.invalidate()

    def _nav_next(self) -> None:
        if self._nav_month == 12:
            self._nav_month = 1
            self._nav_year += 1
        else:
            self._nav_month += 1
        self.invalidate()

    def _pos_to_day(self, pos: tuple, cal_rect: Rect, fonts) -> Optional[int]:
        """Return the 1-based day under ``pos``, or ``None``."""
        font_size = fonts.scaled_size(_FONT_SCALE) if fonts else 14
        header_h = max(20, round(font_size * _CAL_HEADER_H_RATIO))
        day_lbl_h = max(14, round(font_size * _DAY_LABEL_H_RATIO))
        cell_w = max(16, round(font_size * _CELL_W_RATIO))
        cell_h = max(14, round(font_size * _CELL_H_RATIO))
        grid_top = cal_rect.top + header_h + day_lbl_h
        rel_x = pos[0] - cal_rect.left
        rel_y = pos[1] - grid_top
        if rel_x < 0 or rel_y < 0:
            return None
        col = rel_x // cell_w
        row = rel_y // cell_h
        if col >= 7 or row >= 6:
            return None
        cal_matrix = calendar.monthcalendar(self._nav_year, self._nav_month)
        if row >= len(cal_matrix):
            return None
        day = cal_matrix[row][col]
        return day if day != 0 else None

    def _draw_calendar(self, surface: "pygame.Surface", theme: "ColorTheme", fonts) -> None:
        font_size = fonts.scaled_size(_FONT_SCALE)
        cr = self._calendar_rect(fonts)
        header_h = max(20, round(font_size * _CAL_HEADER_H_RATIO))
        day_lbl_h = max(14, round(font_size * _DAY_LABEL_H_RATIO))
        cell_w = max(16, round(font_size * _CELL_W_RATIO))
        cell_h = max(14, round(font_size * _CELL_H_RATIO))

        pygame.draw.rect(surface, theme.background, cr)
        pygame.draw.rect(surface, theme.dark, cr, 1)

        # Header with month/year and navigation
        hdr_rect = Rect(cr.left, cr.top, cr.width, header_h)
        pygame.draw.rect(surface, theme.medium, hdr_rect)
        lbl = f"< {calendar.month_abbr[self._nav_month]} {self._nav_year} >"
        hdr_surf = theme.render_text(lbl, role=self._font_role, size=font_size)
        hx = cr.left + (cr.width - hdr_surf.get_width()) // 2
        hy = cr.top + (header_h - hdr_surf.get_height()) // 2
        surface.blit(hdr_surf, (hx, hy))

        # Day-name row
        for col, name in enumerate(_DAY_NAMES):
            dn_surf = theme.render_text(name, role=self._font_role, size=font_size, color=theme.dark)
            dx = cr.left + col * cell_w + (cell_w - dn_surf.get_width()) // 2
            dy = cr.top + header_h + (day_lbl_h - dn_surf.get_height()) // 2
            surface.blit(dn_surf, (dx, dy))

        # Day cells
        grid_top = cr.top + header_h + day_lbl_h
        cal_matrix = calendar.monthcalendar(self._nav_year, self._nav_month)
        today = date.today()
        for row, week in enumerate(cal_matrix):
            for col, day in enumerate(week):
                if day == 0:
                    continue
                cell_rect = Rect(cr.left + col * cell_w, grid_top + row * cell_h, cell_w, cell_h)
                is_selected = (day == self._value.day and
                               self._nav_year == self._value.year and
                               self._nav_month == self._value.month)
                is_today = (date(self._nav_year, self._nav_month, day) == today)
                is_hovered = day == self._cal_hovered_day

                if is_selected:
                    pygame.draw.rect(surface, theme.highlight, cell_rect)
                elif is_hovered:
                    pygame.draw.rect(surface, theme.light, cell_rect)

                if is_selected:
                    day_color = theme.background
                elif is_today:
                    day_color = theme.dark
                else:
                    day_color = theme.text
                day_surf = theme.render_text(str(day), role=self._font_role, size=font_size, color=day_color)
                dx = cell_rect.left + (cell_rect.width - day_surf.get_width()) // 2
                dy = cell_rect.top + (cell_rect.height - day_surf.get_height()) // 2
                surface.blit(day_surf, (dx, dy))
                if is_today and not is_selected:
                    pygame.draw.rect(surface, theme.highlight, cell_rect, 1)
