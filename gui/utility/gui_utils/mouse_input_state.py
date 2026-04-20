from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class MouseInputState:
    """Snapshot of pointer coordinates and primary button pressed states."""

    position: Tuple[int, int]
    buttons: Tuple[bool, bool, bool]
