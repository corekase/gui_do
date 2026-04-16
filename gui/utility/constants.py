from enum import Enum
from types import MappingProxyType

colours = MappingProxyType({
    'full': (255, 255, 255),
    'light': (0, 200, 200),
    'medium': (0, 150, 150),
    'dark': (0, 100, 100),
    'none': (0, 0, 0),
    'text': (255, 255, 255),
    'highlight': (238, 230, 0),
    'background': (0, 60, 60),
})

class GuiError(Exception):
    pass

class InteractiveState(Enum):
    Idle = 'Idle'
    Hover = 'Hover'
    Armed = 'Armed'

class ContainerKind(Enum):
    Window = 'Window'
    Widget = 'Widget'

class WidgetKind(Enum):
    ArrowBox = 'ArrowBox'
    Button = 'Button'
    ButtonGroup = 'ButtonGroup'
    Canvas = 'Canvas'
    Frame = 'Frame'
    Image = 'Image'
    Label = 'Label'
    Scrollbar = 'Scrollbar'
    Toggle = 'Toggle'

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

class BaseEvent:
    """Base event type for all framework-dispatched events."""
    def __init__(self, event_type: Event) -> None:
        self.type: Event = event_type

class CanvasEvent(Enum):
    MouseWheel = 'MouseWheel'
    MouseMotion = 'MouseMotion'
    MouseButtonDown = 'MouseButtonDown'
    MouseButtonUp = 'MouseButtonUp'
    MousePosition = 'MousePosition'

class ArrowPosition(Enum):
    Skip = 'Skip'
    Split = 'Split'
    Near = 'Near'
    Far = 'Far'

class ButtonStyle(Enum):
    Box = 'Box'
    Round = 'Round'
    Angle = 'Angle'
    Radio = 'Radio'
    Check = 'Check'

class Orientation(Enum):
    Horizontal = 'Horizontal'
    Vertical = 'Vertical'
