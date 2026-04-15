"""
Base widget class for all GUI widgets.

Provides common functionality for drawing, event handling, and state management.
"""

from pygame import Rect
from typing import Optional, Callable, Any, TYPE_CHECKING
from .constants import ContainerKind

if TYPE_CHECKING:
    from .guimanager import GuiManager
    from ..widgets.window import Window

# Widget base class for all GUI widgets

class Widget:
    """
    Base class for all GUI widgets.

    Attributes:
        gui: Reference to the GUI manager
        GType: Type of widget (button, label, etc.)
        ctype: Container type (Widget or Window)
        id: Unique identifier for the widget
        draw_rect: Rectangle defining widget position and size
        hit_rect: Rectangle for collision detection (if different from draw_rect)
        visible: Whether the widget is currently visible
        callback: Optional callback function when widget is activated
    """

    def __init__(self, gui: "GuiManager", id: str, rect: Rect) -> None:
        # gui reference
        self.gui: "GuiManager" = gui
        # widget type
        self.WidgetKind: Optional[Any] = None
        # container type (Widget or Window)
        self.ContainerKind: ContainerKind = ContainerKind.Widget
        # surface to draw the widget on
        self.surface: Optional[Any] = None
        # window widget may be attached to
        self.window: Optional["Window"] = None
        # identifier for widget, can be any kind like int or string
        self.id: Any = id
        # rect for widget drawing position and size on the surface
        self.draw_rect: Rect = Rect(rect)
        # rect for mouse collision
        self.hit_rect: Optional[Rect] = None
        # before widget is first drawn, save what was there in this bitmap
        self.pristine: Optional[Any] = None
        # whether or not the widget is visible
        self._visible: bool = True
        # callback of the widget
        self.callback: Optional[Callable] = None
        # if this is true then if the widget calls the superclass draw defined in this
        # class then this class will restore the pristine image, return, and subclasses
        # continue drawing
        self.auto_restore_pristine: bool = False

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    def get_collide(self, window: Optional["Window"] = None) -> bool:
        """Check if mouse is colliding with this widget."""
        if self.hit_rect is None:
            return self.draw_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), window))
        return self.hit_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), window))

    def handle_event(self, _, _a) -> bool:
        """
        Handle pygame event. Override in subclasses.

        Returns:
            bool: True if event was handled, False otherwise
        """
        # implement in subclasses
        pass

    def get_rect(self) -> Rect:
        """Get rect that the guimanager uses for buffering."""
        return Rect(self.draw_rect)

    def get_size(self) -> Rect:
        """Get widget size without position offset."""
        _, _, w, h = self.draw_rect
        return Rect(0, 0, w, h)

    def draw(self) -> None:
        """Draw the widget. Override in subclasses. May restore pristine bitmap."""
        # if auto restore flag then restore the pristine bitmap
        if self.auto_restore_pristine:
            self.gui.restore_pristine(self.draw_rect, self.window)

    def leave(self) -> None:
        """Called when widget loses focus. Override in subclasses."""
        # what to do when a widget loses focus
        pass
