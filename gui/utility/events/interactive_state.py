from __future__ import annotations

from enum import Enum


class InteractiveState(Enum):
    """Common state-machine states for interactive widgets."""

    Idle = 'Idle'
    Hover = 'Hover'
    Armed = 'Armed'
