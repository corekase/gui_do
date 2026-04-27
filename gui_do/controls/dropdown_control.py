"""DropdownControl — single-select dropdown backed by OverlayManager."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode
from ..controls.list_view_control import ListItem

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


@dataclass
class DropdownOption:
    label: str
    value: Any = field(default=None)
    enabled: bool = True
    data: Any = None

    def __post_init__(self) -> None:
        if self.value is None:
            self.value = self.label


ChangeCallback = Optional[Callable[[Any, int], None]]

_ARROW = "▼"
_OVERLAY_ID_PREFIX = "__dropdown_overlay__"


class DropdownControl(UiNode):
    """A dropdown control that opens a list overlay on click."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        options: Optional[List[DropdownOption]] = None,
        *,
        selected_index: int = -1,
        on_change: ChangeCallback = None,
        placeholder: str = "Select…",
        font_role: str = "medium",
        max_visible_items: int = 8,
    ) -> None:
        super().__init__(control_id, rect)
        self._options: List[DropdownOption] = list(options) if options else []
        self._selected_index: int = -1
        self._on_change: ChangeCallback = on_change
        self._placeholder: str = placeholder
        self._font_role: str = font_role
        self._max_visible_items: int = max(1, int(max_visible_items))
        self._is_open: bool = False
        self.tab_index = 0

        if 0 <= selected_index < len(self._options):
            self._selected_index = selected_index
        self._ensure_selection_invariant()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @selected_index.setter
    def selected_index(self, value: int) -> None:
        if 0 <= value < len(self._options):
            self._selected_index = value
        else:
            self._selected_index = -1
        self._ensure_selection_invariant()
        self.invalidate()

    @property
    def selected_option(self) -> Optional[DropdownOption]:
        if 0 <= self._selected_index < len(self._options):
            return self._options[self._selected_index]
        return None

    @property
    def is_open(self) -> bool:
        return self._is_open

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_options(self, options: List[DropdownOption]) -> None:
        self._options = list(options)
        self._selected_index = -1
        self._ensure_selection_invariant()
        self.invalidate()

    def _ensure_selection_invariant(self) -> None:
        """Keep one selected option whenever options exist."""
        if not self._options:
            self._selected_index = -1
            return
        if 0 <= self._selected_index < len(self._options):
            return
        self._selected_index = 0

    def open(self, app: "GuiApplication") -> None:
        if self._is_open or not self._options:
            return
        self._is_open = True
        self._show_overlay(app)
        self.invalidate()

    def close(self, app: "GuiApplication") -> None:
        if not self._is_open:
            return
        self._is_open = False
        overlay_id = self._overlay_id()
        app.overlay.hide(overlay_id)
        self.invalidate()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _overlay_id(self) -> str:
        return f"{_OVERLAY_ID_PREFIX}{self.control_id}"

    def _show_overlay(self, app: "GuiApplication") -> None:
        from ..controls.overlay_panel_control import OverlayPanelControl
        from ..controls.list_view_control import ListViewControl

        row_height = 28
        n_visible = min(self._max_visible_items, len(self._options))
        panel_height = n_visible * row_height
        panel_width = self.rect.width

        pos = app.overlay.anchor_position(
            (panel_width, panel_height),
            self.rect,
            side="below",
            align="left",
        )
        panel_rect = Rect(pos[0], pos[1], panel_width, panel_height)
        panel = OverlayPanelControl(self._overlay_id() + "_panel", panel_rect)

        list_items = [
            ListItem(label=opt.label, value=opt.value, enabled=opt.enabled, data=opt.data)
            for opt in self._options
        ]
        list_ctrl = ListViewControl(
            self._overlay_id() + "_list",
            Rect(panel_rect.left, panel_rect.top, panel_width, panel_height),
            list_items,
            row_height=row_height,
            selected_index=self._selected_index,
            on_select=lambda idx, item: self._on_list_select(idx, app),
        )
        panel.children.append(list_ctrl)
        list_ctrl.parent = panel

        app.overlay.show(
            self._overlay_id(),
            panel,
            dismiss_on_outside_click=True,
            dismiss_on_escape=True,
            on_dismiss=lambda: self._on_overlay_dismiss(),
        )

    def _on_list_select(self, idx: int, app: "GuiApplication") -> None:
        old_idx = self._selected_index
        self._selected_index = idx
        self.close(app)
        if old_idx != idx and self._on_change is not None:
            try:
                self._on_change(self._options[idx].value, idx)
            except Exception:
                pass
        self.invalidate()

    def _on_overlay_dismiss(self) -> None:
        self._is_open = False
        self.invalidate()

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
            if self.rect.collidepoint(event.pos):
                if self._is_open:
                    self.close(app)
                else:
                    self.open(app)
                return True

        if event.kind == EventType.KEY_DOWN and self._focused:
            k = event.key
            if k in (pygame.K_RETURN, pygame.K_SPACE):
                if not self._is_open:
                    self.open(app)
                else:
                    self.close(app)
                return True
            if k == pygame.K_ESCAPE and self._is_open:
                self.close(app)
                return True
            if not self._is_open:
                if k == pygame.K_UP:
                    new_idx = max(0, self._selected_index - 1) if self._selected_index > 0 else self._selected_index
                    if new_idx != self._selected_index:
                        self._selected_index = new_idx
                        if self._on_change is not None and 0 <= new_idx < len(self._options):
                            try:
                                self._on_change(self._options[new_idx].value, new_idx)
                            except Exception:
                                pass
                        self.invalidate()
                    return True
                if k == pygame.K_DOWN:
                    new_idx = min(len(self._options) - 1, self._selected_index + 1) if self._options else -1
                    if new_idx != self._selected_index and new_idx >= 0:
                        self._selected_index = new_idx
                        if self._on_change is not None:
                            try:
                                self._on_change(self._options[new_idx].value, new_idx)
                            except Exception:
                                pass
                        self.invalidate()
                    return True

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return
        r = self.rect
        bg = getattr(theme, "medium", (50, 50, 60))
        if hasattr(bg, "value"):
            bg = bg.value
        border = getattr(theme, "text", (180, 180, 200))
        if hasattr(border, "value"):
            border = border.value
        pygame.draw.rect(surface, bg, r, border_radius=3)
        pygame.draw.rect(surface, border, r, 1, border_radius=3)

        font = pygame.font.SysFont(None, 18)
        opt = self.selected_option
        label = opt.label if opt is not None else self._placeholder
        text_color = getattr(theme, "text", (220, 220, 220))
        if hasattr(text_color, "value"):
            text_color = text_color.value
        text_surf = font.render(label, True, text_color)
        surface.blit(text_surf, (r.x + 6, r.y + (r.height - text_surf.get_height()) // 2))

        arrow_surf = font.render(_ARROW, True, text_color)
        surface.blit(arrow_surf, (r.right - arrow_surf.get_width() - 6, r.y + (r.height - arrow_surf.get_height()) // 2))
