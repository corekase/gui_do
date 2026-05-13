"""StatusBarControl — thin persistent strip at the bottom of a scene for structured status slots."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from ..base.ui_node import UiNode

if TYPE_CHECKING:
    from ...theme.color_theme import ColorTheme

# Ratios relative to the default font size so text stays legible at any scale.
# Status bars conventionally use slightly smaller text than body copy.
_FONT_SCALE: float = 0.875          # 14/16 — small but readable status text
_SLOT_PAD_X_RATIO: float = 0.5     # horizontal text padding per slot
_SEP_W: int = 1                      # separator line width (px)


@dataclass
class StatusSlot:
    """A named slot in a StatusBarControl.

    ``width`` may be ``None`` to auto-size to text content.
    ``align`` is ``"left"``, ``"center"``, or ``"right"``.
    """
    slot_id: str
    text: str = ""
    width: Optional[int] = None
    align: str = "left"
    separator_after: bool = True


class StatusBarControl(UiNode):
    """Thin horizontal status bar with labeled slots.

    Distinct from :class:`~gui_do.NotificationPanelControl` (which is an
    overlay with a notification history); the status bar is a persistent,
    non-scrolling strip typically docked at the bottom of a scene root.

    Usage::

        bar = StatusBarControl(
            "status_bar", Rect(0, 740, 1280, 24),
            slots=[
                StatusSlot("mode", text="Normal", width=80),
                StatusSlot("coords", text="0, 0", width=100),
                StatusSlot("msg", text="Ready"),
            ],
        )
        # Runtime update:
        bar.set_slot_text("mode", "Insert")
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        slots: Optional[List[StatusSlot]] = None,
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect)
        self._slots: List[StatusSlot] = list(slots or [])
        self._font_role = font_role
        self.tab_index = -1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def slots(self) -> List[StatusSlot]:
        return self._slots

    def set_slot_text(self, slot_id: str, text: str) -> bool:
        """Update the text of a slot by id.  Returns True if found."""
        for slot in self._slots:
            if slot.slot_id == slot_id:
                slot.text = str(text)
                self.invalidate()
                return True
        return False

    def get_slot_text(self, slot_id: str) -> Optional[str]:
        for slot in self._slots:
            if slot.slot_id == slot_id:
                return slot.text
        return None

    def set_slots(self, slots: List[StatusSlot]) -> None:
        self._slots = list(slots)
        self.invalidate()

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def accepts_focus(self) -> bool:
        return False

    def accepts_mouse_focus(self) -> bool:
        return False

    def handle_event(self, event, app, theme=None) -> bool:
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        r = self.rect
        fonts = theme.fonts
        font_size = fonts.scaled_size(_FONT_SCALE)
        pad_x = max(4, fonts.scaled_size(_SLOT_PAD_X_RATIO))

        bg = theme.medium if self.enabled else theme.dark
        pygame.draw.rect(surface, bg, r)
        # Top border line
        pygame.draw.line(surface, theme.dark, (r.left, r.top), (r.right - 1, r.top))

        x = r.left + 2
        text_color = theme.text if self.enabled else theme.dark

        for slot in self._slots:
            label_surf = theme.render_text(
                slot.text, role=self._font_role, shadow=False,
                size=font_size, color=text_color,
            )
            text_w, text_h = label_surf.get_size()
            slot_w = slot.width if slot.width is not None else (text_w + pad_x * 2)

            if slot.align == "center":
                text_x = x + (slot_w - text_w) // 2
            elif slot.align == "right":
                text_x = x + slot_w - text_w - pad_x
            else:
                text_x = x + pad_x
            text_y = r.top + (r.height - text_h) // 2
            surface.blit(label_surf, (text_x, text_y))

            x += slot_w

            if slot.separator_after:
                sep_color = theme.dark if self.enabled else theme.medium
                pygame.draw.line(surface, sep_color, (x, r.top + 2), (x, r.bottom - 3))
                x += _SEP_W + 2
