from typing import Optional

from pygame import Rect
from pygame.event import Event as PygameEvent


class UiNode:
    """Base node for all controls in the rebased package."""

    def __init__(self, control_id: str, rect: Rect) -> None:
        self.control_id = control_id
        self.rect = Rect(rect)
        self.enabled = True
        self.visible = True
        self.parent: Optional["UiNode"] = None

    def update(self, _dt_seconds: float) -> None:
        """Per-frame state update."""

    def handle_event(self, _event: PygameEvent, _app: "GuiApplication") -> bool:
        """Handle one pygame event and return whether consumed."""
        return False

    def draw(self, _surface, _theme) -> None:
        """Draw control onto target surface."""
