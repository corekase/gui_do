from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass
from typing import Hashable


@dataclass
class TaskCompletion:
    id: Hashable
    generation: int
    future: Future[object]
