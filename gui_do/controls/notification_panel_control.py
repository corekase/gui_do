"""NotificationPanelControl — overlay panel rendering a NotificationCenter log."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..controls.overlay_panel_control import OverlayPanelControl
from ..core.notification_center import NotificationCenter
from ..core.toast_manager import ToastSeverity
from ._thumb_drag_lock import begin_thumb_drag, captured_pointer_pos, end_thumb_drag

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


_ROW_H = 60
_PAD = 8
_FONT_SIZE = 16
_TITLE_FONT_SIZE = 13
_TS_FONT_SIZE = 12
_SCROLLBAR_W = 10
_HEADER_H = 32

_SEVERITY_COLORS = {
    ToastSeverity.INFO: (100, 150, 255),
    ToastSeverity.SUCCESS: (80, 200, 100),
    ToastSeverity.WARNING: (230, 180, 50),
    ToastSeverity.ERROR: (220, 70, 70),
}


def _c(theme: "ColorTheme", name: str, fallback: tuple) -> tuple:
    v = getattr(theme, name, fallback)
    return v.value if hasattr(v, "value") else v


class NotificationPanelControl(OverlayPanelControl):
    """An overlay panel that renders a :class:`~gui_do.NotificationCenter` log.

    The panel lists notifications in reverse-chronological order (newest first)
    with a coloured severity stripe, title, message, and timestamp.  A "Mark
    all read" button appears in the header when there are unread items.

    Usage::

        nc = NotificationCenter(app.events, max_records=200)
        nc.subscribe("task.done", severity=ToastSeverity.SUCCESS)

        panel = NotificationPanelControl("notif_panel", rect, nc)
        app.overlay.show("notif_panel", panel, dismiss_on_outside_click=True)
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        center: NotificationCenter,
    ) -> None:
        super().__init__(control_id, rect, draw_background=True)
        self._center = center
        self._scroll_offset: int = 0
        self._hovered_row: int = -1
        self._mark_all_rect: Optional[Rect] = None
        self._scrollbar_dragging: bool = False
        self._scrollbar_drag_anchor: int = 0

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible:
            if self._scrollbar_dragging:
                end_thumb_drag(app, self.control_id)
            self._scrollbar_dragging = False
            return False

        event_pointer = event.pos if isinstance(event.pos, tuple) and len(event.pos) == 2 else None
        pointer = event_pointer if event_pointer is not None else app.logical_pointer_pos

        if event.kind == EventType.MOUSE_MOTION and self._scrollbar_dragging:
            pointer_pos = captured_pointer_pos(app, self.control_id, "y")
            if isinstance(pointer_pos, tuple) and len(pointer_pos) == 2:
                handle_rect = self._scrollbar_handle_rect()
                sb_rect = self._scrollbar_rect()
                if handle_rect is not None and sb_rect is not None:
                    top = pointer_pos[1] - self._scrollbar_drag_anchor
                    top = min(max(top, sb_rect.y), sb_rect.bottom - handle_rect.height)
                    self._set_scroll_from_handle_top(top)
                    self.invalidate()
                    return True

        if event.kind == EventType.MOUSE_BUTTON_UP and event.button == 1 and self._scrollbar_dragging:
            self._scrollbar_dragging = False
            end_thumb_drag(app, self.control_id)
            return True

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1 and isinstance(pointer, tuple) and len(pointer) == 2:
            handle_rect = self._scrollbar_handle_rect()
            sb_rect = self._scrollbar_rect()
            if handle_rect is not None and sb_rect is not None and handle_rect.collidepoint(pointer):
                self._scrollbar_dragging = True
                self._scrollbar_drag_anchor = begin_thumb_drag(
                    app,
                    self.control_id,
                    "y",
                    sb_rect,
                    (int(pointer[0]), int(pointer[1])),
                    handle_rect,
                )
                return True

        if event.kind == EventType.MOUSE_WHEEL and isinstance(pointer, tuple) and self.rect.collidepoint(pointer):
            self._scroll_offset -= event.wheel_delta * _ROW_H
            self._clamp_scroll()
            self.invalidate()
            return True

        if event.kind == EventType.MOUSE_MOTION:
            self._hovered_row = self._row_at(pointer)
            self.invalidate()
            return isinstance(pointer, tuple) and self.rect.collidepoint(pointer)

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            # Mark all read button
            if self._mark_all_rect and self._mark_all_rect.collidepoint(event.pos):
                self._center.mark_all_read()
                self.invalidate()
                return True
            row_idx = self._row_at(event.pos)
            if row_idx >= 0:
                records = self._center.all_records
                if 0 <= row_idx < len(records):
                    self._center.mark_read(records[row_idx])
                    self.invalidate()
                return True
            return self.rect.collidepoint(event.pos)

        if event.kind == EventType.KEY_DOWN and event.key == pygame.K_ESCAPE:
            app.overlay.hide(self.control_id)
            return True

        return False

    def _scrollbar_rect(self) -> Optional[Rect]:
        lr = self._list_rect()
        if self._total_height() <= lr.height:
            return None
        return Rect(self.rect.right - _SCROLLBAR_W, lr.y, _SCROLLBAR_W, lr.height)

    def _scrollbar_handle_rect(self) -> Optional[Rect]:
        sb_rect = self._scrollbar_rect()
        if sb_rect is None:
            return None
        lr = self._list_rect()
        total_h = self._total_height()
        handle_h = max(16, int(lr.height * lr.height / max(1, total_h)))
        handle_y = lr.y + int(self._scroll_offset / max(1, total_h - lr.height) * (lr.height - handle_h))
        return Rect(sb_rect.x + 2, handle_y, _SCROLLBAR_W - 4, handle_h)

    def _set_scroll_from_handle_top(self, top: int) -> None:
        sb_rect = self._scrollbar_rect()
        handle_rect = self._scrollbar_handle_rect()
        if sb_rect is None or handle_rect is None:
            return
        lr = self._list_rect()
        total_h = self._total_height()
        max_scroll = max(0, total_h - lr.height)
        travel = max(1, sb_rect.height - handle_rect.height)
        ratio = (int(top) - sb_rect.y) / float(travel)
        ratio = min(max(ratio, 0.0), 1.0)
        self._scroll_offset = int(round(ratio * max_scroll))
        self._clamp_scroll()

    def _row_at(self, pos: tuple) -> int:
        """Return the record index at *pos* within the list area, or -1."""
        list_rect = self._list_rect()
        if not list_rect.collidepoint(pos):
            return -1
        rel_y = pos[1] - list_rect.y + self._scroll_offset
        idx = rel_y // _ROW_H
        return int(idx) if idx >= 0 else -1

    def _list_rect(self) -> Rect:
        """Content area below the header."""
        return Rect(
            self.rect.x,
            self.rect.y + _HEADER_H,
            self.rect.width - _SCROLLBAR_W,
            self.rect.height - _HEADER_H,
        )

    def _total_height(self) -> int:
        return len(self._center.all_records) * _ROW_H

    def _clamp_scroll(self) -> None:
        lr = self._list_rect()
        max_scroll = max(0, self._total_height() - lr.height)
        self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        bg = _c(theme, "panel", (30, 30, 40))
        header_bg = _c(theme, "accent", (0, 60, 120))
        text_col = _c(theme, "text", (220, 220, 220))
        muted_col = _c(theme, "medium", (150, 150, 160))
        border_col = _c(theme, "border", (70, 70, 85))
        unread_bg = _c(theme, "surface", (40, 40, 55))
        hover_bg = _c(theme, "surface", (50, 50, 65))

        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, border_col, self.rect, 1)

        # Header bar
        header_rect = Rect(self.rect.x, self.rect.y, self.rect.width, _HEADER_H)
        pygame.draw.rect(surface, header_bg, header_rect)
        try:
            hf = pygame.font.SysFont(None, _FONT_SIZE + 2)
            ht = hf.render("Notifications", True, text_col)
            surface.blit(ht, (header_rect.x + _PAD, header_rect.y + (header_rect.height - ht.get_height()) // 2))

            # "Mark all read" button text
            if self._center.unread_count.value > 0:
                mf = pygame.font.SysFont(None, _TITLE_FONT_SIZE)
                mt = mf.render("Mark all read", True, (180, 210, 255))
                mx = header_rect.right - mt.get_width() - _PAD
                my = header_rect.y + (header_rect.height - mt.get_height()) // 2
                self._mark_all_rect = Rect(mx, my, mt.get_width(), mt.get_height())
                surface.blit(mt, (mx, my))
            else:
                self._mark_all_rect = None
        except Exception:
            pass

        # Content list — intersect with the caller's clip so this control
        # renders correctly when hosted inside a ScrollViewControl or any
        # other clipped container.
        lr = self._list_rect()
        old_clip = surface.get_clip()
        effective_clip = lr.clip(old_clip) if old_clip else lr
        surface.set_clip(effective_clip)

        try:
            records = self._center.all_records
            try:
                body_font = pygame.font.SysFont(None, _FONT_SIZE)
                title_font = pygame.font.SysFont(None, _TITLE_FONT_SIZE)
                ts_font = pygame.font.SysFont(None, _TS_FONT_SIZE)
            except Exception:
                body_font = title_font = ts_font = None

            for i, rec in enumerate(records):
                row_y = lr.y + i * _ROW_H - self._scroll_offset
                if row_y + _ROW_H < lr.y:
                    continue
                if row_y > lr.bottom:
                    break
                rr = Rect(lr.x, row_y, lr.width, _ROW_H)
                # Row background
                if not rec.read:
                    pygame.draw.rect(surface, unread_bg, rr)
                elif i == self._hovered_row:
                    pygame.draw.rect(surface, hover_bg, rr)
                # Severity stripe
                stripe_col = _SEVERITY_COLORS.get(rec.severity, (100, 150, 255))
                pygame.draw.rect(surface, stripe_col, Rect(rr.x, rr.y, 4, rr.height))
                # Text
                tx = rr.x + 4 + _PAD
                if body_font:
                    if rec.title:
                        ttxt = title_font.render(rec.title, True, text_col)
                        surface.blit(ttxt, (tx, rr.y + _PAD))
                        msg_y = rr.y + _PAD + ttxt.get_height() + 2
                    else:
                        msg_y = rr.y + _PAD
                    # Truncate message to fit
                    msg = rec.message
                    while msg and body_font.size(msg)[0] > rr.width - tx - _PAD * 2:
                        msg = msg[:-1]
                    if msg != rec.message:
                        msg = msg[:-3] + "..."
                    mtxt = body_font.render(msg, True, muted_col if rec.read else text_col)
                    surface.blit(mtxt, (tx, msg_y))
                    # Timestamp
                    ts_txt = ts_font.render(rec.timestamp, True, muted_col)
                    surface.blit(ts_txt, (rr.right - ts_txt.get_width() - _PAD, rr.y + _PAD))
                # Separator
                pygame.draw.line(surface, border_col, (rr.x, rr.bottom - 1), (rr.right, rr.bottom - 1))
        finally:
            surface.set_clip(old_clip)

        # Scrollbar
        sb_rect = self._scrollbar_rect()
        handle_rect = self._scrollbar_handle_rect()
        if sb_rect is not None and handle_rect is not None:
            pygame.draw.rect(surface, _c(theme, "surface", (50, 50, 65)), sb_rect)
            pygame.draw.rect(surface, muted_col, handle_rect)

        # Empty state
        if not self._center.all_records:
            try:
                ef = pygame.font.SysFont(None, _FONT_SIZE)
                et = ef.render("No notifications", True, muted_col)
                surface.blit(et, (
                    lr.x + (lr.width - et.get_width()) // 2,
                    lr.y + (lr.height - et.get_height()) // 2,
                ))
            except Exception:
                pass
