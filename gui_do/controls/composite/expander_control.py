"""ExpanderControl — collapsible section with animated height transition."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from ..base.ui_node import UiNode
from ...events.gui_event import GuiEvent

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme

# All geometry is derived at draw/event time from the active font size so the
# control scales correctly with any theme configuration.
_FONT_SCALE: float = 1.0            # header label text size ratio
_HEADER_PAD_RATIO: float = 0.5     # vertical padding inside header (each side)
_HEADER_PAD_X_RATIO: float = 0.625 # horizontal padding before arrow / title
_ARROW_RATIO: float = 0.625        # arrow indicator width/height relative to font size
_EXPAND_SPEED: float = 8.0         # px per ms of animation


class ExpanderControl(UiNode):
    """Collapsible container with a clickable header.

    The header label and a disclosure arrow are drawn.  When expanded, all
    child controls added via :meth:`add_child` are visible inside the body
    area.  Animated expansion uses a simple linear interpolation that callers
    drive by calling :meth:`update` each frame.

    Usage::

        expander = ExpanderControl(
            "settings_expander", Rect(0, 0, 300, 28),
            title="Advanced Settings",
            expanded=False,
            body_height=120,
        )
        expander.add_child(SomeControl(...))
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        title: str = "",
        expanded: bool = True,
        body_height: int = 80,
        on_toggled: Optional[Callable[[bool], None]] = None,
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect)
        self._title = title
        self._expanded = bool(expanded)
        self._target_body_height = max(0, int(body_height))
        self._current_body_height: float = float(self._target_body_height) if self._expanded else 0.0
        self._on_toggled = on_toggled
        self._font_role = font_role
        self._children: List[UiNode] = []
        self.tab_index = 0
        self._hovered = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = str(value)
        self.invalidate()

    @property
    def expanded(self) -> bool:
        return self._expanded

    @expanded.setter
    def expanded(self, value: bool) -> None:
        if self._expanded == bool(value):
            return
        self._expanded = bool(value)
        if self._on_toggled:
            self._on_toggled(self._expanded)
        self.invalidate()

    @property
    def body_height(self) -> int:
        return self._target_body_height

    @body_height.setter
    def body_height(self, value: int) -> None:
        self._target_body_height = max(0, int(value))
        if self._expanded:
            self.invalidate()

    @property
    def total_height(self) -> int:
        """Current rendered height including header and animated body."""
        return _HEADER_H + int(self._current_body_height)

    def add_child(self, control: UiNode) -> UiNode:
        """Add a child control to the expander body."""
        self._children.append(control)
        control.parent = self
        self.invalidate()
        return control

    def remove_child(self, control: UiNode) -> bool:
        if control in self._children:
            self._children.remove(control)
            control.parent = None
            self.invalidate()
            return True
        return False

    def toggle(self) -> None:
        self.expanded = not self._expanded

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return self.visible and self.enabled

    def reconcile_hover(self, wants_hover: bool) -> None:
        if self._hovered != wants_hover:
            self._hovered = wants_hover
            self.invalidate()

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        self._hovered = False
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        self._hovered = False
        super()._on_visibility_changed(old_visible, new_visible)

    def update(self, dt_seconds: float) -> None:
        target = float(self._target_body_height) if self._expanded else 0.0
        if self._current_body_height == target:
            return
        delta = _EXPAND_SPEED * dt_seconds * 1000.0
        if self._current_body_height < target:
            self._current_body_height = min(target, self._current_body_height + delta)
        else:
            self._current_body_height = max(target, self._current_body_height - delta)
        self.invalidate()
        visible = self._current_body_height > 1.0
        for child in self._children:
            child.visible = visible

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            self._hovered = False
            return False

        fonts = theme.fonts if (theme is not None and hasattr(theme, "fonts")) else None
        header_h = self._header_h(fonts)
        header_rect = Rect(self.rect.left, self.rect.top, self.rect.width, header_h)
        pos = event.pos

        if event.is_mouse_motion() and pos is not None:
            new_hov = header_rect.collidepoint(pos)
            if new_hov != self._hovered:
                self._hovered = new_hov
                self.invalidate()
            return False

        if event.is_mouse_down(1) and pos is not None:
            if header_rect.collidepoint(pos):
                self.toggle()
                return True

        # Forward events to children when expanded
        if self._expanded and int(self._current_body_height) > 0:
            for child in self._children:
                if child.visible and child.enabled:
                    if child.handle_event(event, app, theme):
                        return True

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        r = self.rect
        fonts = theme.fonts
        font_size = fonts.scaled_size(_FONT_SCALE)
        header_h = self._header_h(fonts)
        pad_x = max(4, fonts.scaled_size(_HEADER_PAD_X_RATIO))
        arrow_size = max(6, fonts.scaled_size(_ARROW_RATIO))
        body_h = int(self._current_body_height)

        # Header background
        header_rect = Rect(r.left, r.top, r.width, header_h)
        if not self.enabled:
            hdr_color = theme.dark
        elif self._hovered:
            hdr_color = theme.light
        else:
            hdr_color = theme.medium
        pygame.draw.rect(surface, hdr_color, header_rect)
        pygame.draw.rect(surface, theme.dark, header_rect, 1)

        # Focus ring on header when keyboard-focused
        if self._focused:
            pygame.draw.rect(surface, theme.highlight, header_rect, 2)

        # Disclosure arrow
        arrow_cx = r.left + pad_x + arrow_size // 2
        arrow_cy = r.top + header_h // 2
        arrow_color = theme.dark if not self.enabled else theme.text
        if self._expanded:
            pts = [
                (arrow_cx - arrow_size // 2, arrow_cy - arrow_size // 4),
                (arrow_cx + arrow_size // 2, arrow_cy - arrow_size // 4),
                (arrow_cx, arrow_cy + arrow_size // 2),
            ]
        else:
            pts = [
                (arrow_cx - arrow_size // 4, arrow_cy - arrow_size // 2),
                (arrow_cx + arrow_size // 2, arrow_cy),
                (arrow_cx - arrow_size // 4, arrow_cy + arrow_size // 2),
            ]
        pygame.draw.polygon(surface, arrow_color, pts)

        # Title text
        title_color = theme.dark if not self.enabled else theme.text
        title_surf = theme.render_text(
            self._title, role=self._font_role, shadow=False,
            size=font_size, color=title_color,
        )
        text_x = r.left + pad_x + arrow_size + pad_x // 2
        text_y = r.top + (header_h - title_surf.get_height()) // 2
        surface.blit(title_surf, (text_x, text_y))

        # Body area
        if body_h > 0:
            body_rect = Rect(r.left, r.top + header_h, r.width, body_h)
            bg = theme.dark if not self.enabled else theme.background
            pygame.draw.rect(surface, bg, body_rect)
            pygame.draw.rect(surface, theme.dark, body_rect, 1)
            clip = surface.get_clip()
            surface.set_clip(body_rect)
            for child in self._children:
                if child.visible:
                    child.draw(surface, theme)
            surface.set_clip(clip)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _header_h(self, fonts) -> int:
        """Compute header height from the active font size."""
        if fonts is None:
            return 28  # safe default when no theme
        font_size = fonts.scaled_size(_FONT_SCALE)
        pad = max(2, fonts.scaled_size(_HEADER_PAD_RATIO))
        return font_size + pad * 2
