from __future__ import annotations

from enum import Enum


class Event(Enum):
    """Top-level event categories routed by the GUI dispatcher."""

    Pass = 'Pass'
    Quit = 'Quit'
    KeyDown = 'KeyDown'
    KeyUp = 'KeyUp'
    MouseButtonDown = 'MouseButtonDown'
    MouseButtonUp = 'MouseButtonUp'
    MouseMotion = 'MouseMotion'
    Widget = 'Widget'
    Group = 'Group'
    Task = 'Task'
