from __future__ import annotations

from enum import Enum


TaskKind = Enum('TaskKind', ['Finished', 'Failed'])
TaskKind.__doc__ = 'Task terminal states represented in scheduler task events.'
