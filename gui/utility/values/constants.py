from enum import Enum

# named colour values, in one location to change everywhere
colours = {'full': (255, 255, 255), 'light': (0, 200, 200), 'medium': (0, 150, 150), 'dark': (0, 100, 100), 'none': (0, 0, 0),
           'text': (255, 255, 255), 'highlight': (238, 230, 0), 'background': (0, 60, 60)}

# ============================================================================
# Enumerations - Standardized Naming Conventions
# ============================================================================
# EventKind: GUI event types (system and widget events)
Event = Enum('Event', ['Pass', 'Quit', 'KeyDown', 'KeyUp', 'MouseButtonDown',
                       'MouseButtonUp', 'MouseMotion', 'Widget', 'Group', 'Task'])

# WidgetKind: Types of widgets in the GUI framework
WidgetKind = Enum('WidgetKind', ['ArrowBox', 'Button', 'ButtonGroup', 'Canvas', 'Frame', 'Image',
                                 'Label', 'Scrollbar', 'Slider', 'Toggle'])

# ContainerKind: Types of containers (windows vs widgets on screen/in windows)
ContainerKind = Enum('ContainerKind', ['Window', 'Widget'])

# InteractiveState: State for interactive widgets (button, toggle, etc.)
InteractiveState = Enum('InteractiveState', ['Idle', 'Hover', 'Armed'])

# CanvasEvent: Types of canvas-specific events
CanvasEvent = Enum('CanvasEvent', ['MouseWheel', 'MouseMotion', 'MouseButtonDown', 'MouseButtonUp', 'MousePosition'])

# Orientation: Horizontal or vertical
Orientation = Enum('Orientation', ['Horizontal', 'Vertical'])

# ScrollbarArrowPosition: Whether scrollbar arrows skip, split, near, or far of the scrollable area
ArrowPosition = Enum('ArrowPosition', ['Skip', 'Split', 'Near', 'Far'])

# ButtonStyle: Visual style for buttons (box, rounded, angled, radio, checkbox)
ButtonStyle = Enum('ButtonStyle', ['Box', 'Round', 'Angle', 'Radio', 'Check'])
