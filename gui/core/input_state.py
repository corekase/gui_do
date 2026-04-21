from typing import Optional, Tuple
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL


class InputState:
    """Normalized pointer and wheel state for one frame."""

    def __init__(self) -> None:
        self.pointer_pos: Tuple[int, int] = (0, 0)
        self.wheel_delta: int = 0
        self.left_down: bool = False

    def begin_frame(self) -> None:
        """Reset transient frame fields."""
        self.wheel_delta = 0

    def update_from_event(self, event: object) -> Optional[Tuple[int, int]]:
        """Apply event to input state and return raw event position when present."""
        raw_pos = getattr(event, "pos", None)
        if isinstance(raw_pos, tuple) and len(raw_pos) == 2:
            self.pointer_pos = raw_pos

        if event.type == MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            self.left_down = True
        elif event.type == MOUSEBUTTONUP and getattr(event, "button", None) == 1:
            self.left_down = False
        elif event.type == MOUSEWHEEL:
            self.wheel_delta = int(getattr(event, "y", 0))

        if event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION):
            if isinstance(raw_pos, tuple) and len(raw_pos) == 2:
                return raw_pos
        return None
