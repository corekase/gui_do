"""DockWorkspacePanel — UI control that renders a DockWorkspace as an interactive tab bar.

Only the *top-level* node of the workspace is rendered:

* **DockTabs** — draws a row of clickable tab buttons; clicking switches
  ``active_pane_id`` and fires ``on_change``.
* **DockPane** — draws the pane title as a single non-interactive header.
* **DockSplit** / ``None`` — draws a placeholder label.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ...events.gui_event import EventType, GuiEvent
from ..base.ui_node import UiNode
from ...layout.dock_workspace import DockPane, DockSplit, DockTabs, DockWorkspace

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


_TAB_H = 32


class DockWorkspacePanel(UiNode):
    """Renders a :class:`~gui_do.DockWorkspace` as an interactive tab strip.

    When the workspace root is a :class:`~gui_do.DockTabs` node the panel
    draws one clickable button per pane.  Clicking a button sets
    ``tabs.active_pane_id`` and invokes ``on_change(pane_id)``.

    For other root kinds the panel shows a simple descriptive label.

    Usage::

        workspace = DockWorkspace(DockTabs("main", panes=[
            DockPane("editor", "Editor"),
            DockPane("preview", "Preview"),
        ]))
        panel = DockWorkspacePanel("dock", Rect(0, 0, 600, 36), workspace,
                                   on_change=lambda pid: print("switched to", pid))
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        workspace: Optional[DockWorkspace] = None,
        *,
        tab_height: int = _TAB_H,
        on_change: Optional[Callable[[str], None]] = None,
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect)
        self._workspace: Optional[DockWorkspace] = workspace
        self._tab_height: int = max(16, int(tab_height))
        self._on_change: Optional[Callable[[str], None]] = on_change
        self.font_role: str = str(font_role)
        self.tab_index = 0
        self._draw_font: object = None  # cached from pygame.font.SysFont(None, 14)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def workspace(self) -> Optional[DockWorkspace]:
        return self._workspace

    def set_workspace(self, workspace: Optional[DockWorkspace]) -> None:
        """Replace the backing workspace model and redraw."""
        self._workspace = workspace
        self.invalidate()

    @property
    def active_pane_id(self) -> Optional[str]:
        """Return the active pane id from the root DockTabs, or *None*."""
        tabs = self._active_tabs()
        return tabs.active_pane_id if tabs is not None else None

    def switch_pane(self, pane_id: str) -> bool:
        """Programmatically switch the active pane.  Returns *True* on success."""
        tabs = self._active_tabs()
        if tabs is None:
            return False
        target = str(pane_id)
        if not any(p.pane_id == target for p in tabs.panes):
            return False
        tabs.active_pane_id = target
        self.invalidate()
        if self._on_change is not None:
            try:
                self._on_change(target)
            except Exception:
                pass
        return True

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        if not self.visible:
            return

        bg = getattr(theme, "panel_bg", (30, 30, 35))
        pygame.draw.rect(surface, bg, self.rect)

        tabs = self._active_tabs()
        if tabs is None:
            self._draw_placeholder(surface, theme)
            return

        tab_rects = self._tab_rects(tabs)
        for pane, tab_rect in zip(tabs.panes, tab_rects):
            is_active = pane.pane_id == tabs.active_pane_id
            self._draw_tab(surface, theme, tab_rect, pane.title or pane.pane_id, is_active)

    def _draw_placeholder(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        fg = getattr(theme, "label_fg", (160, 160, 160))
        root = self._workspace.root if self._workspace else None
        if root is None:
            text = "(empty workspace)"
        elif isinstance(root, DockPane):
            text = root.title or root.pane_id
        elif isinstance(root, DockSplit):
            axis = root.axis
            text = f"(split — {axis}, {len(root.children)} pane(s))"
        else:
            text = "(unsupported root)"
        try:
            if self._draw_font is None:
                self._draw_font = pygame.font.SysFont(None, 14)
            surf = self._draw_font.render(text, True, fg)
            cx = self.rect.x + (self.rect.width - surf.get_width()) // 2
            cy = self.rect.y + (self.rect.height - surf.get_height()) // 2
            surface.blit(surf, (cx, cy))
        except Exception:
            pass

    def _draw_tab(
        self,
        surface: pygame.Surface,
        theme: "ColorTheme",
        tab_rect: Rect,
        label: str,
        active: bool,
    ) -> None:
        if active:
            bg = getattr(theme, "tab_active_bg", (50, 100, 160))
            fg = getattr(theme, "tab_active_fg", (240, 240, 240))
        else:
            bg = getattr(theme, "tab_inactive_bg", (40, 40, 48))
            fg = getattr(theme, "tab_inactive_fg", (180, 180, 180))
        pygame.draw.rect(surface, bg, tab_rect)
        border_col = getattr(theme, "tab_border", (60, 60, 70))
        pygame.draw.rect(surface, border_col, tab_rect, 1)
        try:
            if self._draw_font is None:
                self._draw_font = pygame.font.SysFont(None, 14)
            surf = self._draw_font.render(label, True, fg)
            cx = tab_rect.x + (tab_rect.width - surf.get_width()) // 2
            cy = tab_rect.y + (tab_rect.height - surf.get_height()) // 2
            surface.blit(surf, (cx, cy))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            tabs = self._active_tabs()
            if tabs is None:
                return False
            pos = event.pos
            if not self.rect.collidepoint(pos):
                return False
            tab_rects = self._tab_rects(tabs)
            for pane, tab_rect in zip(tabs.panes, tab_rects):
                if tab_rect.collidepoint(pos):
                    self.switch_pane(pane.pane_id)
                    return True
            return False

        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _active_tabs(self) -> Optional[DockTabs]:
        if self._workspace is None or self._workspace.root is None:
            return None
        if isinstance(self._workspace.root, DockTabs):
            return self._workspace.root
        return None

    def _tab_rects(self, tabs: DockTabs) -> List[Rect]:
        """Divide the panel rect evenly into one tab button per pane."""
        n = len(tabs.panes)
        if n == 0:
            return []
        tab_w = max(1, self.rect.width // n)
        rects: List[Rect] = []
        x = self.rect.x
        for i in range(n):
            w = tab_w if i < n - 1 else self.rect.right - x
            rects.append(Rect(x, self.rect.y, w, self._tab_height))
            x += tab_w
        return rects
