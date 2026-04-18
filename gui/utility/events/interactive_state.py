from __future__ import annotations

from enum import Enum


class InteractiveState(Enum):
    Idle = 'Idle'
    Hover = 'Hover'
    Armed = 'Armed'
