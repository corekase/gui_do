from typing import Optional, Tuple

from pygame import Rect


class PointerCapture:
    """Capture and clamp pointer coordinates during drag operations."""

    def __init__(self) -> None:
        self.owner_id: Optional[str] = None
        self.lock_rect: Optional[Rect] = None

    @property
    def is_active(self) -> bool:
        """Return True when pointer capture is currently owned by any owner."""
        return self.owner_id is not None

    def begin(self, owner_id: str, lock_rect: Rect) -> None:
        """Begin pointer capture for one owner within lock rect bounds."""
        self.owner_id = owner_id
        self.lock_rect = Rect(lock_rect)

    def end(self, owner_id: str) -> None:
        """End pointer capture for owner if currently active."""
        if self.owner_id != owner_id:
            return
        self.owner_id = None
        self.lock_rect = None

    def force_release(self) -> Optional[str]:
        """Release pointer capture unconditionally regardless of owner.

        Returns the previous owner id, or ``None`` if capture was already idle.
        """
        previous = self.owner_id
        self.owner_id = None
        self.lock_rect = None
        return previous

    def is_owned_by(self, owner_id: str) -> bool:
        """Return whether capture is currently owned by the supplied id."""
        return self.owner_id == owner_id

    def clamp(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """Clamp point to active lock area when capture is active."""
        if self.lock_rect is None:
            return pos
        x = min(max(pos[0], self.lock_rect.left), self.lock_rect.right - 1)
        y = min(max(pos[1], self.lock_rect.top), self.lock_rect.bottom - 1)
        return (x, y)
