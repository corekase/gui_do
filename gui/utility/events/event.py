from enum import Enum


class Event(Enum):
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
