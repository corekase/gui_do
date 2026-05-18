"""SplitButtonControl — primary action button with an attached dropdown."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..base.ui_node import UiNode
from ...events.gui_event import GuiEvent

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme


_OVERLAY_ID_PREFIX = "__split_button_overlay__"

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
        self._last_app = None
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

    def open_dropdown(self, app: "GuiApplication") -> None:
        if self._dropdown_open or not self._options:
            return
        self._last_app = app
        self._dropdown_open = True
        self._show_overlay(app)
        self.invalidate()

    def close_dropdown(self, app: "GuiApplication" = None) -> None:
        if app is not None:
            self._last_app = app
        app_ref = app if app is not None else self._last_app
        if not self._dropdown_open:
            if app_ref is not None:
                app_ref.overlay.hide(self._overlay_id())
            return
        self._dropdown_open = False
        if app_ref is not None:
            overlay_id = self._overlay_id()
            app_ref.overlay.hide(overlay_id)
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

    def on_focus_changed(self, is_focused: bool) -> None:
        if is_focused:
            return
        self._main_pressed = False
        self._main_hovered = False
        self._arrow_hovered = False
        self.close_dropdown()

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        self._main_hovered = False
        self._arrow_hovered = False
        self._main_pressed = False
        self.close_dropdown()
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        self._main_hovered = False
        self._arrow_hovered = False
        self._main_pressed = False
        self.close_dropdown()
        super()._on_visibility_changed(old_visible, new_visible)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        self._last_app = app
        if not self.visible or not self.enabled:
            self._main_hovered = False
            self._arrow_hovered = False
            self._main_pressed = False
            return False

        fonts = theme.fonts if (theme is not None and hasattr(theme, "fonts")) else None
        arrow_w = self._arrow_btn_w(fonts)
        main_rect, arrow_rect = self._split_rects(arrow_w)
        pos = event.pos

        if event.is_mouse_motion() and pos is not None:
            prev_main = self._main_hovered
            prev_arrow = self._arrow_hovered
            self._main_hovered = main_rect.collidepoint(pos)
            self._arrow_hovered = arrow_rect.collidepoint(pos)
            if (prev_main, prev_arrow) != (self._main_hovered, self._arrow_hovered):
                self.invalidate()
            return False

        if event.is_mouse_down(1) and pos is not None:
            if main_rect.collidepoint(pos):
                self._main_pressed = True
                self.invalidate()
                return True
            if arrow_rect.collidepoint(pos):
                if self._dropdown_open:
                    self.close_dropdown(app)
                else:
                    self.open_dropdown(app)
                self.invalidate()
                return True
            # Any click outside the button returns False to allow default overlay handling
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
            self._label, role=self._font_role,
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

    def _overlay_id(self) -> str:
        return f"{_OVERLAY_ID_PREFIX}{self.control_id}"

    def _show_overlay(self, app: "GuiApplication") -> None:
        from ..composite.overlay_panel_control import OverlayPanelControl
        from ..data.list_view_control import ListViewControl, ListItem

        row_height = 28
        n_options = len(self._options)
        panel_height = n_options * row_height
        panel_width = self.rect.width

        pos = app.overlay.anchor_position(
            (panel_width, panel_height),
            self.rect,
            side="below",
            align="left",
        )
        panel_rect = Rect(pos[0], pos[1], panel_width, panel_height)
        panel = OverlayPanelControl(self._overlay_id() + "_panel", panel_rect, draw_background=False)

        list_items = [
            ListItem(label=opt.label, value=opt.label, enabled=opt.enabled, data=opt)
            for opt in self._options
        ]
        list_ctrl = ListViewControl(
            self._overlay_id() + "_list",
            Rect(panel_rect.left, panel_rect.top, panel_width, panel_height),
            list_items,
            row_height=row_height,
            selected_index=-1,
            on_select=lambda idx, item: self._on_list_select(idx, app),
        )
        # Clear selection for dropdown usage (no pre-selected items, despite invariant auto-selecting)
        list_ctrl._selected_indices = []
        list_ctrl._selected_set = set()
        panel.children.append(list_ctrl)
        list_ctrl.parent = panel

        app.overlay.show(
            self._overlay_id(),
            panel,
            dismiss_on_outside_click=True,
            dismiss_on_escape=True,
            dismiss_on_focus_lost=True,
            focus_owner_id=self.control_id,
            on_dismiss=lambda: self._on_overlay_dismiss(),
        )

    def _on_list_select(self, idx: int, app: "GuiApplication") -> None:
        if 0 <= idx < len(self._options):
            opt = self._options[idx]
            if opt.enabled and opt.on_click:
                opt.on_click()
        self.close_dropdown(app)

    def _on_overlay_dismiss(self) -> None:
        self._dropdown_open = False
        self.invalidate()
