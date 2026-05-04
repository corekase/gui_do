"""OverlayManager — z-ordered transient UI layer above the scene graph."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..events.gui_event import EventType, GuiEvent

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..controls.composite.overlay_panel_control import OverlayPanelControl
    from ..theme.color_theme import ColorTheme


@dataclass
class OverlayRecord:
    owner_id: str
    control: "OverlayPanelControl"
    dismiss_on_outside_click: bool = True
    dismiss_on_escape: bool = True
    consume_unhandled_keys: bool = False
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
        self._record_by_owner: dict[str, OverlayRecord] = {}

    def show(
        self,
        owner_id: str,
        control: "OverlayPanelControl",
        *,
        dismiss_on_outside_click: bool = True,
        dismiss_on_escape: bool = True,
        consume_unhandled_keys: bool = False,
        on_dismiss: Optional[Callable[[], None]] = None,
    ) -> OverlayHandle:
        """Register and show an overlay. Replaces any existing overlay with the same id."""
        self.hide(owner_id)
        record = OverlayRecord(
            owner_id=owner_id,
            control=control,
            dismiss_on_outside_click=dismiss_on_outside_click,
            dismiss_on_escape=dismiss_on_escape,
            consume_unhandled_keys=consume_unhandled_keys,
            on_dismiss=on_dismiss,
        )
        self._records.append(record)
        self._record_by_owner[owner_id] = record
        return OverlayHandle(owner_id, self)

    def hide(self, owner_id: str) -> bool:
        """Dismiss an overlay by id. Returns True if it was open."""
        if owner_id not in self._record_by_owner:
            return False
        self._record_by_owner.pop(owner_id)
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
        self._record_by_owner.clear()
        for rec in records:
            if rec.on_dismiss is not None:
                try:
                    rec.on_dismiss()
                except Exception:
                    pass
        return count

    def has_overlay(self, owner_id: str) -> bool:
        return owner_id in self._record_by_owner

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

        # Left-button MOUSEBUTTONDOWN outside overlays: dismiss dismiss_on_outside_click overlays
        # Important: does NOT consume the event (returns False) so scene can still handle it
        pointer_down = event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1
        pointer_pos = event.pos if isinstance(event.pos, tuple) and len(event.pos) == 2 else None
        await_inside_hit = bool(pointer_down and pointer_pos is not None)
        inside_hit = False
        deferred_records: list[OverlayRecord] = []
        dismissible_owner_ids: list[str] = []
        consume_unhandled_keys = False

        for rec in reversed(self._records):
            if pointer_down and rec.dismiss_on_outside_click:
                dismissible_owner_ids.append(rec.owner_id)
            if not (rec.control.visible and rec.control.enabled):
                continue
            if event.kind in (EventType.KEY_DOWN, EventType.KEY_UP, EventType.TEXT_INPUT, EventType.TEXT_EDITING):
                consume_unhandled_keys = consume_unhandled_keys or rec.consume_unhandled_keys
            if await_inside_hit:
                if rec.control.rect.collidepoint(pointer_pos):
                    inside_hit = True
                    await_inside_hit = False
                    for pending in deferred_records:
                        if pending.control.handle_routed_event(event, app):
                            return True
                    deferred_records.clear()
                    if rec.control.handle_routed_event(event, app):
                        return True
                else:
                    deferred_records.append(rec)
                continue
            if rec.control.handle_routed_event(event, app):
                return True

        if pointer_down and pointer_pos is not None and not inside_hit:
            for owner_id in dismissible_owner_ids:
                self.hide(owner_id)
            return False

        if consume_unhandled_keys:
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
