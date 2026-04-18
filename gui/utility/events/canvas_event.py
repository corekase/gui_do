from enum import Enum


class CanvasEvent(Enum):
    MouseWheel = 'MouseWheel'
    MouseMotion = 'MouseMotion'
    MouseButtonDown = 'MouseButtonDown'
    MouseButtonUp = 'MouseButtonUp'
    MousePosition = 'MousePosition'
