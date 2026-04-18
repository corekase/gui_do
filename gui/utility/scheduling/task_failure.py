from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable


@dataclass
class TaskFailure:
    """Failure envelope emitted when task execution raises an exception."""

    id: Hashable
    generation: int
    error: str
