"""SplitButtonControl — primary action button with an attached dropdown."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..base.ui_node import UiNode
from ...events.gui_event import GuiEvent

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme

# Ratios relative to the default font size.
_FONT_SCALE: float = 1.0           # button label text size ratio
_ARROW_BTN_RATIO: float = 1.125   # arrow button width as fraction of font size
_DROPDOWN_ROW_H_RATIO: float = 1.625  # dropdown row height ratio
_DROPDOWN_PAD_X_RATIO: float = 0.5   # horizontal text padding in dropdown rows


@dataclass
class SplitButtonOption:
    """A secondary option in a :class:`SplitButtonControl` dropdown."""
    label: str
    on_click: Optional[Callable[[], None]] = None
    enabled: bool = True


class SplitButtonControl(UiNode):
    """Button with a primary action and an attached dropdown for alternate actions.

    The left portion is the primary button; clicking it invokes ``on_click``.
    The right chevron portion opens a small dropdown with secondary options.

    Usage::

        btn = SplitButtonControl(
            "save_btn", Rect(0, 0, 120, 30),
            label="Save",
            on_click=save_file,
            options=[
                SplitButtonOption("Save As…", on_click=save_as),
                SplitButtonOption("Save All", on_click=save_all),
            ],
        )
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        label: str = "",
        on_click: Optional[Callable[[], None]] = None,
        options: Optional[List[SplitButtonOption]] = None,
        font_role: str = "body",
        style: str = "box",
    ) -> None:
        super().__init__(control_id, rect)
        self._label = label
        self._on_click = on_click
        self._options: List[SplitButtonOption] = list(options or [])
        self._font_role = font_role
        self._style = style
        self._main_hovered = False
        self._arrow_hovered = False
        self._main_pressed = False
        self._dropdown_open = False
        self._dropdown_hovered_idx = -1
        self.tab_index = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._label = str(value)
        self.invalidate()

    def set_options(self, options: List[SplitButtonOption]) -> None:
        self._options = list(options)
        self._dropdown_open = False
        self.invalidate()

    def close_dropdown(self) -> None:
        if self._dropdown_open:
            self._dropdown_open = False
            self.invalidate()

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled

    def reconcile_hover(self, wants_hover: bool) -> None:
        if not wants_hover:
            changed = self._main_hovered or self._arrow_hovered
            self._main_hovered = False
            self._arrow_hovered = False
            if changed:
                self.invalidate()

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        self._main_hovered = False
        self._arrow_hovered = False
        self._main_pressed = False
        self._dropdown_open = False
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        self._main_hovered = False
        self._arrow_hovered = False
        self._main_pressed = False
        self._dropdown_open = False
        super()._on_visibility_changed(old_visible, new_visible)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            self._main_hovered = False
            self._arrow_hovered = False
            self._main_pressed = False
            self._dropdown_open = False
            return False

        fonts = theme.fonts if (theme is not None and hasattr(theme, "fonts")) else None
        arrow_w = self._arrow_btn_w(fonts)
        main_rect, arrow_rect = self._split_rects(arrow_w)
        dropdown_rect = self._dropdown_rect(arrow_w, fonts)
        pos = event.pos

        if event.is_mouse_motion() and pos is not None:
            prev_main = self._main_hovered
            prev_arrow = self._arrow_hovered
            prev_dd = self._dropdown_hovered_idx
            self._main_hovered = main_rect.collidepoint(pos)
            self._arrow_hovered = arrow_rect.collidepoint(pos)
            if self._dropdown_open and dropdown_rect is not None:
                self._dropdown_hovered_idx = self._dropdown_index_at(pos, dropdown_rect, fonts)
            else:
                self._dropdown_hovered_idx = -1
            if (prev_main, prev_arrow, prev_dd) != (self._main_hovered, self._arrow_hovered, self._dropdown_hovered_idx):
                self.invalidate()
            return False

        if event.is_mouse_down(1) and pos is not None:
            if main_rect.collidepoint(pos):
                self._main_pressed = True
                self.invalidate()
                return True
            if arrow_rect.collidepoint(pos):
                self._dropdown_open = not self._dropdown_open
                self.invalidate()
                return True
            if self._dropdown_open and dropdown_rect and dropdown_rect.collidepoint(pos):
                idx = self._dropdown_index_at(pos, dropdown_rect, fonts)
                if idx >= 0:
                    opt = self._options[idx]
                    if opt.enabled and opt.on_click:
                        opt.on_click()
                    self._dropdown_open = False
                    self.invalidate()
                    return True
            if self._dropdown_open:
                self._dropdown_open = False
                self.invalidate()
            return False

        if event.is_mouse_up(1) and pos is not None:
            was_pressed = self._main_pressed
            self._main_pressed = False
            if was_pressed and main_rect.collidepoint(pos):
                if self._on_click:
                    self._on_click()
                self.invalidate()
                return True
            self.invalidate()
            return False

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        fonts = theme.fonts
        font_size = fonts.scaled_size(_FONT_SCALE)
        arrow_w = self._arrow_btn_w(fonts)
        row_h = max(20, fonts.scaled_size(_DROPDOWN_ROW_H_RATIO))
        pad_x = max(4, fonts.scaled_size(_DROPDOWN_PAD_X_RATIO))
        main_rect, arrow_rect = self._split_rects(arrow_w)

        # Main button
        if not self.enabled:
            main_color = theme.dark
        elif self._main_pressed:
            main_color = theme.dark
        elif self._main_hovered:
            main_color = theme.light
        else:
            main_color = theme.medium
        pygame.draw.rect(surface, main_color, main_rect)
        pygame.draw.rect(surface, theme.dark, main_rect, 1)

        label_color = theme.dark if not self.enabled else (theme.background if self._main_pressed else theme.text)
        label_surf = theme.render_text(
            self._label, role=self._font_role, shadow=False,
            size=font_size, color=label_color,
        )
        lx = main_rect.left + (main_rect.width - label_surf.get_width()) // 2
        ly = main_rect.top + (main_rect.height - label_surf.get_height()) // 2
        surface.blit(label_surf, (lx, ly))

        # Arrow button
        if not self.enabled:
            arrow_color = theme.dark
        elif self._arrow_hovered:
            arrow_color = theme.light
        else:
            arrow_color = theme.medium
        pygame.draw.rect(surface, arrow_color, arrow_rect)
        pygame.draw.rect(surface, theme.dark, arrow_rect, 1)
        # Chevron indicator
        cx = arrow_rect.left + arrow_rect.width // 2
        cy = arrow_rect.top + arrow_rect.height // 2
        chev_color = theme.dark if not self.enabled else theme.text
        chev = arrow_w // 4
        pts = [(cx - chev, cy - chev // 2), (cx + chev, cy - chev // 2), (cx, cy + chev)]
        pygame.draw.polygon(surface, chev_color, pts)

        # Focus ring
        if self._focused:
            full_rect = Rect(self.rect.left, self.rect.top, self.rect.width, self.rect.height)
            pygame.draw.rect(surface, theme.highlight, full_rect, 2)

        # Dropdown panel
        if self._dropdown_open and self._options:
            dr = self._dropdown_rect(arrow_w, fonts)
            if dr:
                pygame.draw.rect(surface, theme.background, dr)
                pygame.draw.rect(surface, theme.dark, dr, 1)
                for idx, opt in enumerate(self._options):
                    row = Rect(dr.left, dr.top + idx * row_h, dr.width, row_h)
                    if idx == self._dropdown_hovered_idx and opt.enabled:
                        pygame.draw.rect(surface, theme.highlight, row)
                    opt_color = theme.dark if not opt.enabled else theme.text
                    opt_surf = theme.render_text(
                        opt.label, role=self._font_role, shadow=False,
                        size=font_size, color=opt_color,
                    )
                    surface.blit(opt_surf, (row.left + pad_x, row.top + (row.height - opt_surf.get_height()) // 2))
                    if idx < len(self._options) - 1:
                        pygame.draw.line(surface, theme.medium, (row.left + 4, row.bottom), (row.right - 4, row.bottom))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _arrow_btn_w(self, fonts) -> int:
        if fonts is None:
            return 18
        return max(14, fonts.scaled_size(_ARROW_BTN_RATIO))

    def _split_rects(self, arrow_w: int):
        r = self.rect
        main_w = max(1, r.width - arrow_w)
        main = Rect(r.left, r.top, main_w, r.height)
        arrow = Rect(r.left + main_w, r.top, arrow_w, r.height)
        return main, arrow

    def _dropdown_rect(self, arrow_w: int, fonts) -> Optional[Rect]:
        if not self._options or fonts is None:
            return None
        row_h = max(20, fonts.scaled_size(_DROPDOWN_ROW_H_RATIO))
        r = self.rect
        dd_h = len(self._options) * row_h
        return Rect(r.left, r.bottom, r.width, dd_h)

    def _dropdown_index_at(self, pos: tuple, dropdown_rect: Rect, fonts) -> int:
        if not dropdown_rect.collidepoint(pos) or fonts is None:
            return -1
        row_h = max(20, fonts.scaled_size(_DROPDOWN_ROW_H_RATIO))
        rel_y = pos[1] - dropdown_rect.top
        idx = rel_y // row_h
        if 0 <= idx < len(self._options):
            return idx
        return -1
