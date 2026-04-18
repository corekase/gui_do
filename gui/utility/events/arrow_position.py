from __future__ import annotations

from enum import Enum


class ArrowPosition(Enum):
    """Arrow alignment variants for directional widgets and controls."""

    Skip = 'Skip'
    Split = 'Split'
    Near = 'Near'
    Far = 'Far'
