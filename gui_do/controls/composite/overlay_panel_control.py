"""OverlayPanelControl — PanelControl subclass that renders as an overlay."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from .panel_control import PanelControl
from ...events.gui_event import EventType, GuiEvent

if TYPE_CHECKING:
    from ..layout.constraint_layout import ConstraintLayout
    from ...app.gui_application import GuiApplication


class OverlayPanelControl(PanelControl):
    """A panel intended for use as an overlay (rendered by OverlayManager).

    Automatically consumes mouse input within the overlay bounds to prevent
    input fall-through to controls or areas underneath the overlay.
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        *,
        draw_background: bool = True,
        constraints: "Optional[ConstraintLayout]" = None,
    ) -> None:
        super().__init__(control_id, rect, draw_background=draw_background, constraints=constraints)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        """Handle events with input consumption for mouse clicks within overlay bounds."""
        # Consume mouse clicks within overlay bounds to prevent fall-through
        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            if isinstance(event.pos, tuple) and len(event.pos) == 2:
                if self.rect.collidepoint(event.pos):
                    # Dispatch to children and consume input regardless of child response
                    self._dispatch_children(event, app, reverse=True, theme=theme)
                    return True

        # Default behavior: dispatch to children
        return self._dispatch_children(event, app, reverse=True, theme=theme)

    def is_overlay(self) -> bool:
        return True
