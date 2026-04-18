from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import Future
from typing import Callable, Hashable, Optional


@dataclass
class Task:
    id: Hashable
    run_callable: Callable[[], object]
    message_method: Optional[Callable[[object], None]] = None
    future: Optional[Future[object]] = None
    generation: int = 0
