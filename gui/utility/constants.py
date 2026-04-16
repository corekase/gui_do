from enum import Enum
from types import MappingProxyType

# named colour values (read-only mapping)
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
    # State for interactive widgets (button, toggle, etc.)
    Idle = 'Idle'
    Hover = 'Hover'
    Armed = 'Armed'


class ContainerKind(Enum):
    # Types of containers (windows vs widgets on screen/in windows)
    Window = 'Window'
    Widget = 'Widget'


class WidgetKind(Enum):
    # Types of widgets in the GUI framework
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
    # GUI event types (system and widget events)
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
    # Types of canvas-specific events
    MouseWheel = 'MouseWheel'
    MouseMotion = 'MouseMotion'
    MouseButtonDown = 'MouseButtonDown'
    MouseButtonUp = 'MouseButtonUp'
    MousePosition = 'MousePosition'


class ArrowPosition(Enum):
    # Whether scrollbar arrows skip, split, near, or far of the scrollable area
    Skip = 'Skip'
    Split = 'Split'
    Near = 'Near'
    Far = 'Far'


class ButtonStyle(Enum):
    # Visual style for buttons (box, rounded, angled, radio, checkbox)
    Box = 'Box'
    Round = 'Round'
    Angle = 'Angle'
    Radio = 'Radio'
    Check = 'Check'


class Orientation(Enum):
    # Horizontal or vertical
    Horizontal = 'Horizontal'
    Vertical = 'Vertical'
