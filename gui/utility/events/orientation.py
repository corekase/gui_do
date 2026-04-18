from __future__ import annotations

from enum import Enum


class Orientation(Enum):
    """Layout axis options used by widgets such as scrollbars."""

    Horizontal = 'Horizontal'
    Vertical = 'Vertical'
