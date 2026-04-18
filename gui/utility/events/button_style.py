from __future__ import annotations

from enum import Enum


class ButtonStyle(Enum):
    """Supported button rendering style strategies."""

    Box = 'Box'
    Round = 'Round'
    Angle = 'Angle'
    Radio = 'Radio'
    Check = 'Check'
