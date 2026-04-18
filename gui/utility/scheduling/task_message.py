from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Hashable


@dataclass
class TaskMessage:
    id: Hashable
    callback: Callable[[object], None]
    payload: object
    generation: int
