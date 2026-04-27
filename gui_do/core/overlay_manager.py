"""OverlayManager — z-ordered transient UI layer above the scene graph."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from .gui_event import EventType, GuiEvent

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..controls.overlay_panel_control import OverlayPanelControl
    from ..theme.color_theme import ColorTheme


@dataclass
class OverlayRecord:
    owner_id: str
    control: "OverlayPanelControl"
    dismiss_on_outside_click: bool = True
    dismiss_on_escape: bool = True
    on_dismiss: Optional[Callable[[], None]] = None


@dataclass
class OverlayHandle:
    owner_id: str
    _manager: "OverlayManager"

    def dismiss(self) -> None:
        self._manager.hide(self.owner_id)

    @property
    def is_open(self) -> bool:
        return self._manager.has_overlay(self.owner_id)


class OverlayManager:
    """Manages transient overlay controls drawn above the scene graph."""

    def __init__(self) -> None:
        self._records: List[OverlayRecord] = []

    def show(
        self,
        owner_id: str,
        control: "OverlayPanelControl",
        *,
        dismiss_on_outside_click: bool = True,
        dismiss_on_escape: bool = True,
        on_dismiss: Optional[Callable[[], None]] = None,
    ) -> OverlayHandle:
        """Register and show an overlay. Replaces any existing overlay with the same id."""
        self.hide(owner_id)
        record = OverlayRecord(
            owner_id=owner_id,
            control=control,
            dismiss_on_outside_click=dismiss_on_outside_click,
            dismiss_on_escape=dismiss_on_escape,
            on_dismiss=on_dismiss,
        )
        self._records.append(record)
        return OverlayHandle(owner_id, self)

    def hide(self, owner_id: str) -> bool:
        """Dismiss an overlay by id. Returns True if it was open."""
        for i, rec in enumerate(self._records):
            if rec.owner_id == owner_id:
                self._records.pop(i)
                if rec.on_dismiss is not None:
                    try:
                        rec.on_dismiss()
                    except Exception:
                        pass
                return True
        return False

    def hide_all(self) -> int:
        """Dismiss all overlays. Returns count dismissed."""
        count = len(self._records)
        records = list(self._records)
        self._records.clear()
        for rec in records:
            if rec.on_dismiss is not None:
                try:
                    rec.on_dismiss()
                except Exception:
                    pass
        return count

    def has_overlay(self, owner_id: str) -> bool:
        return any(r.owner_id == owner_id for r in self._records)

    def overlay_count(self) -> int:
        return len(self._records)

    def point_in_any_overlay(self, pos: tuple) -> bool:
        """Return True if pos is inside any registered overlay control's rect."""
        for rec in self._records:
            if rec.control.rect.collidepoint(pos):
                return True
        return False

    def route_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        """Route an event to overlays. Returns True only if event was consumed."""
        if not self._records:
            return False

        # ESCAPE: dismiss topmost dismiss_on_escape overlay
        if event.kind == EventType.KEY_DOWN and event.key == pygame.K_ESCAPE:
            for i in range(len(self._records) - 1, -1, -1):
                rec = self._records[i]
                if rec.dismiss_on_escape:
                    owner_id = rec.owner_id
                    self.hide(owner_id)
                    return True
            return False

        # MOUSEBUTTONDOWN outside overlays: dismiss dismiss_on_outside_click overlays
        # Important: does NOT consume the event (returns False) so scene can still handle it
        if event.kind == EventType.MOUSE_BUTTON_DOWN:
            pos = event.pos
            if isinstance(pos, tuple) and len(pos) == 2:
                if not self.point_in_any_overlay(pos):
                    # Dismiss all outside-click dismissible overlays
                    to_dismiss = [r.owner_id for r in self._records if r.dismiss_on_outside_click]
                    for owner_id in to_dismiss:
                        self.hide(owner_id)
                    return False  # scene still processes the click

        # Route events to overlay controls (top to bottom)
        for rec in reversed(self._records):
            if rec.control.visible and rec.control.enabled:
                consumed = rec.control.handle_routed_event(event, app)
                if consumed:
                    return True

        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        """Draw all overlay controls in registration order (bottom to top)."""
        for rec in self._records:
            if rec.control.visible:
                rec.control.draw(surface, theme)

    @staticmethod
    def anchor_position(
        control_size: Tuple[int, int],
        target_rect: Rect,
        *,
        side: str = "below",
        align: str = "left",
        screen_rect: Optional[Rect] = None,
    ) -> Tuple[int, int]:
        """Compute overlay top-left position anchored to target_rect.

        side: "below" | "above" | "right" | "left"
        align: "left" | "right" | "center" (for below/above)
                "top" | "bottom" | "center" (for right/left)
        """
        cw, ch = int(control_size[0]), int(control_size[1])

        if side == "below":
            y = target_rect.bottom
            if align == "left":
                x = target_rect.left
            elif align == "right":
                x = target_rect.right - cw
            else:  # center
                x = target_rect.centerx - cw // 2
        elif side == "above":
            y = target_rect.top - ch
            if align == "left":
                x = target_rect.left
            elif align == "right":
                x = target_rect.right - cw
            else:
                x = target_rect.centerx - cw // 2
        elif side == "right":
            x = target_rect.right
            if align == "top":
                y = target_rect.top
            elif align == "bottom":
                y = target_rect.bottom - ch
            else:
                y = target_rect.centery - ch // 2
        else:  # left
            x = target_rect.left - cw
            if align == "top":
                y = target_rect.top
            elif align == "bottom":
                y = target_rect.bottom - ch
            else:
                y = target_rect.centery - ch // 2

        if screen_rect is not None:
            x = max(screen_rect.left, min(x, screen_rect.right - cw))
            y = max(screen_rect.top, min(y, screen_rect.bottom - ch))

        return (x, y)
