from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import Future
from typing import Callable, Hashable, Optional


@dataclass
class Task:
    """Work item tracked by the scheduler.

    Attributes:
        id: Hashable task identifier.
        run_callable: Work function submitted to the executor.
        message_method: Optional callback used for progress/message delivery.
        future: Optional future associated with submitted execution.
        generation: Lifecycle generation used to drop stale notifications.
    """

    id: Hashable
    run_callable: Callable[[], object]
    message_method: Optional[Callable[[object], None]] = None
    future: Optional[Future[object]] = None
    generation: int = 0
