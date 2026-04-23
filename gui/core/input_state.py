from typing import Tuple


class InputState:
    """Normalized pointer state for one frame."""

    def __init__(self) -> None:
        self.pointer_pos: Tuple[int, int] = (0, 0)

    def update_from_event(self, event: object) -> None:
        """Apply event to input state."""
        raw_pos = event.pos
        if isinstance(raw_pos, tuple) and len(raw_pos) == 2:
            self.pointer_pos = raw_pos
