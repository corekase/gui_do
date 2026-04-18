from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Dict, Optional
from .constants import Event

if TYPE_CHECKING:
    from .gui_event import GuiEvent


@dataclass
class InputAction:
    """Structured routing outcome consumed by InputEventEmitter."""

    event_type: Optional[Event] = None
    kwargs: Dict[str, object] = field(default_factory=dict)
    builder: Optional[Callable[[], "GuiEvent"]] = None

    @classmethod
    def pass_event(cls) -> "InputAction":
        return cls(event_type=Event.Pass)

    @classmethod
    def emit(cls, event_type: Event, **kwargs: object) -> "InputAction":
        return cls(event_type=event_type, kwargs=kwargs)

    @classmethod
    def from_builder(cls, builder: Callable[[], "GuiEvent"]) -> "InputAction":
        return cls(builder=builder)
