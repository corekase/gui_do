"""PropertyInspectorPanel — scrollable UI control that renders a PropertyInspectorModel."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional

import pygame
from pygame import Rect

from ...events.gui_event import EventType, GuiEvent
from ..base.ui_node import UiNode
from ...introspection.property_inspector import InspectedProperty, PropertyInspectorModel
from ..base._thumb_drag_lock import begin_thumb_drag, captured_pointer_pos, end_thumb_drag

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme


_HEADER_HEIGHT = 22
_ROW_HEIGHT = 24
_SCROLLBAR_WIDTH = 12
_LABEL_FRACTION = 0.45  # portion of content width reserved for property label


class _InspectorRow:
    """Flattened render unit: either a group header or a property row."""

    __slots__ = ("is_header", "group_name", "prop")

    def __init__(
        self,
        *,
        is_header: bool,
        group_name: str = "",
        prop: Optional[InspectedProperty] = None,
    ) -> None:
        self.is_header = is_header
        self.group_name = group_name
        self.prop = prop


class PropertyInspectorPanel(UiNode):
    """Scrollable panel that renders the groups and properties of a
    :class:`~gui_do.core.property_inspector.PropertyInspectorModel`.

    Each group is shown as a coloured section header row followed by one row
    per property (label on the left, current value string on the right).
    The panel is read-only by default; call :meth:`set_editable` to allow the
    user to click a value row and edit it (requires the application's overlay
    for a text-input popup — not yet wired; reserved for a future pass).

    Usage::

        from gui_do import PropertyInspectorPanel, PropertyInspectorModel

        model = PropertyInspectorModel(my_control)
        panel = PropertyInspectorPanel("props", Rect(0, 0, 300, 400), model)
        app.add(panel)

    Refresh the display after changing target properties with::

        panel.refresh()
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        model: Optional[PropertyInspectorModel] = None,
        *,
        header_height: int = _HEADER_HEIGHT,
        row_height: int = _ROW_HEIGHT,
        show_scrollbar: bool = True,
        font_role: str = "body",
        on_select: Optional[Callable[[InspectedProperty], None]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self._model: Optional[PropertyInspectorModel] = model
        self._header_height: int = max(8, int(header_height))
        self._row_height: int = max(8, int(row_height))
        self._show_scrollbar: bool = bool(show_scrollbar)
        self._font_role: str = font_role
        self._on_select: Optional[Callable[[InspectedProperty], None]] = on_select

        self._rows: List[_InspectorRow] = []
        self._scroll_offset: int = 0
        self._selected_prop: Optional[InspectedProperty] = None
        self._scrollbar_dragging: bool = False
        self._scrollbar_drag_anchor: int = 0

        self._rebuild()
        self.tab_index = 0
        self._draw_font_role: str = "property_inspector.row"

    _FONT_SCALE: float = 1.0   # 16/16 — body-size property labels

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def model(self) -> Optional[PropertyInspectorModel]:
        return self._model

    @property
    def scroll_offset(self) -> int:
        return self._scroll_offset

    @property
    def selected_property(self) -> Optional[InspectedProperty]:
        return self._selected_prop

    def set_model(self, model: Optional[PropertyInspectorModel]) -> None:
        """Replace the inspected model and refresh the display."""
        self._model = model
        self._selected_prop = None
        self._scroll_offset = 0
        self._rebuild()
        self.invalidate()

    def refresh(self) -> None:
        """Re-read property values from the target and redraw."""
        self._rebuild()
        self.invalidate()

    # ------------------------------------------------------------------
    # Internal layout
    # ------------------------------------------------------------------

    def _rebuild(self) -> None:
        self._rows = []
        if self._model is None:
            return
        grouped: Dict[str, List[InspectedProperty]] = self._model.grouped()
        for group_name, props in grouped.items():
            self._rows.append(_InspectorRow(is_header=True, group_name=group_name))
            for prop in props:
                self._rows.append(_InspectorRow(is_header=False, prop=prop))

    def _total_height(self) -> int:
        return sum(
            self._header_height if row.is_header else self._row_height
            for row in self._rows
        )

    def _viewport_height(self) -> int:
        return max(1, self.rect.height)

    def _scrollbar_rect(self) -> Optional[Rect]:
        if not self._show_scrollbar or self._total_height() <= self._viewport_height():
            return None
        return Rect(
            self.rect.right - _SCROLLBAR_WIDTH,
            self.rect.y,
            _SCROLLBAR_WIDTH,
            self.rect.height,
        )

    def _scrollbar_handle_rect(self) -> Optional[Rect]:
        sb = self._scrollbar_rect()
        if sb is None:
            return None
        total = max(1, self._total_height())
        vh = self._viewport_height()
        ratio = min(1.0, vh / total)
        handle_h = max(16, int(sb.height * ratio))
        scroll_range = sb.height - handle_h
        offset_ratio = self._scroll_offset / max(1, total - vh)
        handle_y = sb.y + int(scroll_range * offset_ratio)
        return Rect(sb.x, handle_y, sb.width, handle_h)

    def _clamp_scroll(self) -> None:
        total = self._total_height()
        vh = self._viewport_height()
        max_scroll = max(0, total - vh)
        self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))

    def _prop_at_y(self, pixel_y: int) -> Optional[InspectedProperty]:
        y = self.rect.y - self._scroll_offset
        for row in self._rows:
            h = self._header_height if row.is_header else self._row_height
            if y <= pixel_y < y + h:
                if not row.is_header and row.prop is not None:
                    return row.prop
                return None
            y += h
        return None

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self.visible or not self.enabled:
            return False

        if self._scrollbar_dragging and event.kind == EventType.MOUSE_BUTTON_UP and event.button == 1:
            self._scrollbar_dragging = False
            end_thumb_drag(app, self.control_id)
            return True

        if self._scrollbar_dragging and event.kind == EventType.MOUSE_MOTION:
            pointer_pos = captured_pointer_pos(app, self.control_id, "y")
            if isinstance(pointer_pos, tuple):
                sb = self._scrollbar_rect()
                handle = self._scrollbar_handle_rect()
                if sb is not None and handle is not None:
                    top = pointer_pos[1] - self._scrollbar_drag_anchor
                    top = max(sb.y, min(top, sb.bottom - handle.height))
                    total = max(1, self._total_height())
                    vh = self._viewport_height()
                    ratio = (top - sb.y) / max(1, sb.height - handle.height)
                    self._scroll_offset = int(ratio * max(0, total - vh))
                    self._clamp_scroll()
                    self.invalidate()
            return True

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            sb = self._scrollbar_rect()
            handle = self._scrollbar_handle_rect()
            pos = event.pos
            if handle is not None and sb is not None and handle.collidepoint(pos):
                self._scrollbar_dragging = True
                self._scrollbar_drag_anchor = begin_thumb_drag(
                    app, self.control_id, "y", sb, (int(pos[0]), int(pos[1])), handle
                )
                return True
            if self.rect.collidepoint(pos):
                prop = self._prop_at_y(pos[1])
                self._selected_prop = prop
                if prop is not None and self._on_select is not None:
                    try:
                        self._on_select(prop)
                    except Exception:
                        pass
                self.invalidate()
                return True

        if event.kind == EventType.MOUSE_WHEEL and self.rect.collidepoint(event.pos):
            self._scroll_offset -= event.wheel_delta * self._row_height
            self._clamp_scroll()
            self.invalidate()
            return True

        return False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        r = self.rect

        # Background
        bg = getattr(theme, "background", (28, 28, 30))
        pygame.draw.rect(surface, bg, r)

        if not self._rows:
            return

        font = theme.fonts.font_instance(self._draw_font_role, size=theme.fonts.scaled_size(self._FONT_SCALE))

        # Resolve colors
        text_color = theme.text
        header_bg = getattr(theme, "panel", (50, 52, 60))
        header_text = getattr(theme, "accent", (160, 200, 255))
        row_alt = getattr(theme, "row_alt", (35, 35, 38))
        sel_color = theme.highlight
        val_color = getattr(theme, "text_secondary", (160, 165, 175))

        sb_rect = self._scrollbar_rect()
        content_w = r.width - ((_SCROLLBAR_WIDTH) if sb_rect is not None else 0)
        content_rect = Rect(r.x, r.y, max(1, content_w), r.height)

        clip = surface.get_clip()
        surface.set_clip(content_rect.clip(clip) if clip else content_rect)

        y = r.y - self._scroll_offset
        alt = False
        label_w = int(content_w * _LABEL_FRACTION)
        val_x = r.x + label_w

        for row in self._rows:
            h = self._header_height if row.is_header else self._row_height
            row_rect = Rect(r.x, y, content_w, h)

            if y + h >= r.y and y <= r.bottom:
                if row.is_header:
                    pygame.draw.rect(surface, header_bg, row_rect)
                    surf = font.render(row.group_name, True, header_text)
                    surface.blit(surf, (row_rect.x + 6, row_rect.y + (h - surf.get_height()) // 2))
                else:
                    if row.prop is not None:
                        is_selected = (self._selected_prop is not None and row.prop is self._selected_prop)
                        row_bg = sel_color if is_selected else (row_alt if alt else bg)
                        pygame.draw.rect(surface, row_bg, row_rect)
                        # Label (left side)
                        lbl = row.prop.descriptor.label or row.prop.descriptor.name
                        lbl_surf = font.render(lbl, True, text_color)
                        surface.blit(lbl_surf, (row_rect.x + 4, row_rect.y + (h - lbl_surf.get_height()) // 2))
                        # Value (right side)
                        try:
                            val_str = str(row.prop.value)
                        except Exception:
                            val_str = "—"
                        vc = text_color if is_selected else val_color
                        val_surf = font.render(val_str, True, vc)
                        surface.blit(val_surf, (val_x + 4, row_rect.y + (h - val_surf.get_height()) // 2))
                        alt = not alt

            y += h

        surface.set_clip(clip)

        # Scrollbar
        if sb_rect is not None:
            pygame.draw.rect(surface, theme.dark, sb_rect)
            handle = self._scrollbar_handle_rect()
            if handle is not None:
                pygame.draw.rect(surface, theme.medium, handle, border_radius=2)
