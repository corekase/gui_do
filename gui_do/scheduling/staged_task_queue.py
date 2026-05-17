"""
Generalized staged/async task queue for scheduling.
User code only enqueues tasks; draining and rate-limiting is automatic.
"""
from collections import deque
from typing import Callable

class StagedTaskQueue:
    def __init__(self):
        self._queue = deque()

    def enqueue(self, task: Callable):
        self._queue.append(task)

    def clear(self):
        self._queue.clear()

    def __len__(self):
        return len(self._queue)

    def drain(self, max_tasks: int = None):
        count = 0
        while self._queue and (max_tasks is None or count < max_tasks):
            task = self._queue.popleft()
            task()
            count += 1
