"""OverlayPanelControl — PanelControl subclass that renders as an overlay."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pygame import Rect

from ..controls.panel_control import PanelControl

if TYPE_CHECKING:
    from ..layout.constraint_layout import ConstraintLayout


class OverlayPanelControl(PanelControl):
    """A panel intended for use as an overlay (rendered by OverlayManager)."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        *,
        draw_background: bool = True,
        constraints: "Optional[ConstraintLayout]" = None,
    ) -> None:
        super().__init__(control_id, rect, draw_background=draw_background, constraints=constraints)

    def is_overlay(self) -> bool:
        return True
