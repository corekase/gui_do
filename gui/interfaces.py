"""
Abstract interfaces and protocols for the GUI framework.

Defines contracts for widgets and other components to improve type safety
and make architectural requirements explicit.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Protocol, Callable
from pygame import Rect, event as pygame_event


class IEventResponse(ABC):
    """Interface representing the result of event handling."""

    @property
    @abstractmethod
    def consumed(self) -> bool:
        """Whether the event was handled and should not propagate."""
        pass


class EventResponse(IEventResponse):
    """Standard event response types."""

    class Consumed(IEventResponse):
        """Event was handled by widget."""
        @property
        def consumed(self) -> bool:
            return True

        def __repr__(self):
            return "EventResponse.Consumed"

    class Unhandled(IEventResponse):
        """Widget did not handle the event."""
        @property
        def consumed(self) -> bool:
            return False

        def __repr__(self):
            return "EventResponse.Unhandled"

    class Activated(IEventResponse):
        """Widget was activated (state changed)."""
        def __init__(self, widget_id: Any):
            self.widget_id = widget_id

        @property
        def consumed(self) -> bool:
            return True

        def __repr__(self):
            return f"EventResponse.Activated({self.widget_id})"

    # Singleton instances
    CONSUMED = Consumed()
    UNHANDLED = Unhandled()


class ITimerService(ABC):
    """Service interface for managing timers."""

    @abstractmethod
    def add_timer(self, id: Any, duration: float, callback: Callable) -> None:
        """Add a timer that calls callback after duration milliseconds."""
        pass

    @abstractmethod
    def remove_timer(self, id: Any) -> None:
        """Remove timer with given id."""
        pass

    @abstractmethod
    def update(self, now_time: float) -> None:
        """Update all timers. Called once per frame."""
        pass


class ILayoutManager(ABC):
    """Service interface for widget layout."""

    @abstractmethod
    def calculate_position(self, widget_index: int, parent_rect: Rect) -> Rect:
        """Calculate position for widget at given index."""
        pass

    @abstractmethod
    def get_total_size(self) -> tuple[int, int]:
        """Get total size needed for all widgets in layout."""
        pass


class IWindow(Protocol):
    """Protocol for window-like containers."""

    x: int
    y: int
    width: int
    height: int
    surface: Any  # pygame.Surface
    visible: bool
    widgets: list

    def get_visible(self) -> bool:
        """Check if window is visible."""
        ...

    def get_window_rect(self) -> Rect:
        """Get total window rectangle including title bar."""
        ...


class IWidget(ABC):
    """Interface that all widgets must implement."""

    # Identifier and state
    id: Any
    visible: bool

    # Rendering
    draw_rect: Rect
    hit_rect: Optional[Rect]

    @abstractmethod
    def draw(self) -> None:
        """Render widget to surface."""
        pass

    @abstractmethod
    def handle_event(self, event: pygame_event.event, window: Optional[IWindow]) -> IEventResponse:
        """
        Handle pygame event.

        Args:
            event: pygame event to handle
            window: Parent window if widget is in a window, else None

        Returns:
            IEventResponse indicating how event was handled
        """
        pass

    @abstractmethod
    def set_visible(self, visible: bool) -> None:
        """Set widget visibility."""
        pass

    @abstractmethod
    def get_visible(self) -> bool:
        """Get widget visibility."""
        pass

    @abstractmethod
    def get_collide(self, window: Optional[IWindow] = None) -> bool:
        """Check if mouse is colliding with widget."""
        pass

    @abstractmethod
    def leave(self) -> None:
        """Called when widget loses focus."""
        pass


class IButton(IWidget):
    """Interface for button widgets."""

    @property
    @abstractmethod
    def state(self) -> Any:  # InteractiveState
        """Current button state (Idle, Hover, Armed)."""
        pass

    def on_click(self, callback: Callable) -> None:
        """Register callback for button click."""
        pass


class IToggle(IWidget):
    """Interface for toggle/checkbox widgets."""

    @property
    @abstractmethod
    def toggled(self) -> bool:
        """Whether toggle is in toggled state."""
        pass

    @abstractmethod
    def set_toggled(self, value: bool) -> None:
        """Set toggle state."""
        pass


class ITextInput(IWidget):
    """Interface for text input widgets."""

    @property
    @abstractmethod
    def text(self) -> str:
        """Current text value."""
        pass

    @abstractmethod
    def set_text(self, value: str) -> None:
        """Set text value."""
        pass


class ICanvas(IWidget):
    """Interface for custom drawing canvas."""

    @abstractmethod
    def get_surface(self) -> Any:  # pygame.Surface
        """Get canvas surface for drawing on."""
        pass

    @abstractmethod
    def restore_pristine(self, area: Optional[Rect] = None) -> None:
        """Restore area to pristine state."""
        pass


# Usage example in widget implementations:
#
# class Button(IButton):
#     def handle_event(self, event: pygame_event.event, window: Optional[IWindow]) -> IEventResponse:
#         if not self.get_collide(window):
#             return EventResponse.UNHANDLED
#
#         if event.type == MOUSEBUTTONDOWN:
#             if event.button == 1:
#                 self.state = InteractiveState.Armed
#                 return EventResponse.Activated(self.id)
#
#         return EventResponse.UNHANDLED
