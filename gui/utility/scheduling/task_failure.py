from dataclasses import dataclass
from typing import Hashable


@dataclass
class TaskFailure:
    id: Hashable
    generation: int
    error: str
