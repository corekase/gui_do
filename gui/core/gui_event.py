from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import Hashable, Optional, Tuple

import pygame


class EventType(Enum):
    PASS = "pass"
    QUIT = "quit"
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    MOUSE_BUTTON_DOWN = "mouse_button_down"
    MOUSE_BUTTON_UP = "mouse_button_up"
    MOUSE_MOTION = "mouse_motion"
    MOUSE_WHEEL = "mouse_wheel"
    TEXT_INPUT = "text_input"
    TEXT_EDITING = "text_editing"
    WIDGET = "widget"
    GROUP = "group"
    TASK = "task"


class EventPhase(Enum):
    CAPTURE = "capture"
    TARGET = "target"
    BUBBLE = "bubble"


_PYGAME_KIND_MAP = {
    pygame.QUIT: EventType.QUIT,
    pygame.KEYDOWN: EventType.KEY_DOWN,
    pygame.KEYUP: EventType.KEY_UP,
    pygame.MOUSEBUTTONDOWN: EventType.MOUSE_BUTTON_DOWN,
    pygame.MOUSEBUTTONUP: EventType.MOUSE_BUTTON_UP,
    pygame.MOUSEMOTION: EventType.MOUSE_MOTION,
    pygame.MOUSEWHEEL: EventType.MOUSE_WHEEL,
    pygame.TEXTINPUT: EventType.TEXT_INPUT,
    pygame.TEXTEDITING: EventType.TEXT_EDITING,
}


@dataclass
class GuiEvent:
    """Normalized GUI event shared across the package event pipeline."""

    kind: EventType
    type: int
    key: Optional[int] = None
    pos: Optional[Tuple[int, int]] = None
    rel: Optional[Tuple[int, int]] = None
    raw_pos: Optional[Tuple[int, int]] = None
    raw_rel: Optional[Tuple[int, int]] = None
    button: Optional[int] = None
    wheel_x: int = 0
    wheel_y: int = 0
    text: Optional[str] = None
    widget_id: Optional[str] = None
    group: Optional[str] = None
    window: Optional[object] = None
    task_panel: bool = False
    task_id: Optional[Hashable] = None
    error: Optional[str] = None
    source_event: Optional[object] = None
    phase: EventPhase = EventPhase.TARGET
    propagation_stopped: bool = False
    default_prevented: bool = False

    def is_kind(self, *kinds: EventType) -> bool:
        return self.kind in kinds

    def with_phase(self, phase: EventPhase) -> "GuiEvent":
        self.phase = phase
        return self

    def stop_propagation(self) -> None:
        self.propagation_stopped = True

    def prevent_default(self) -> None:
        self.default_prevented = True

    def is_quit(self) -> bool:
        """Return True for application-quit events."""
        return self.kind is EventType.QUIT

    def is_key_down(self, key: Optional[int] = None) -> bool:
        if self.kind is not EventType.KEY_DOWN:
            return False
        return key is None or self.key == int(key)

    def is_key_up(self, key: Optional[int] = None) -> bool:
        if self.kind is not EventType.KEY_UP:
            return False
        return key is None or self.key == int(key)

    def is_mouse_down(self, button: Optional[int] = None) -> bool:
        if self.kind is not EventType.MOUSE_BUTTON_DOWN:
            return False
        return button is None or self.button == int(button)

    def is_mouse_up(self, button: Optional[int] = None) -> bool:
        if self.kind is not EventType.MOUSE_BUTTON_UP:
            return False
        return button is None or self.button == int(button)

    def is_mouse_motion(self) -> bool:
        return self.kind is EventType.MOUSE_MOTION

    def is_mouse_wheel(self) -> bool:
        return self.kind is EventType.MOUSE_WHEEL

    def is_left_down(self) -> bool:
        """Return True for a left-button press (equivalent to ``is_mouse_down(1)``)."""
        return self.kind is EventType.MOUSE_BUTTON_DOWN and self.button == 1

    def is_left_up(self) -> bool:
        """Return True for a left-button release (equivalent to ``is_mouse_up(1)``)."""
        return self.kind is EventType.MOUSE_BUTTON_UP and self.button == 1

    def is_right_down(self) -> bool:
        """Return True for a right-button press (equivalent to ``is_mouse_down(3)``)."""
        return self.kind is EventType.MOUSE_BUTTON_DOWN and self.button == 3

    def is_right_up(self) -> bool:
        """Return True for a right-button release (equivalent to ``is_mouse_up(3)``)."""
        return self.kind is EventType.MOUSE_BUTTON_UP and self.button == 3

    def is_middle_down(self) -> bool:
        """Return True for a middle-button press (equivalent to ``is_mouse_down(2)``)."""
        return self.kind is EventType.MOUSE_BUTTON_DOWN and self.button == 2

    def is_middle_up(self) -> bool:
        """Return True for a middle-button release (equivalent to ``is_mouse_up(2)``)."""
        return self.kind is EventType.MOUSE_BUTTON_UP and self.button == 2

    def is_text_event(self) -> bool:
        """Return True for text-input or text-editing events."""
        return self.kind in (EventType.TEXT_INPUT, EventType.TEXT_EDITING)

    def clone(self) -> "GuiEvent":
        """Return a shallow copy of this event with an independent propagation state."""
        return dataclasses.replace(self)

    @property
    def wheel_delta(self) -> int:
        return int(self.wheel_y)

    def collides(self, rect) -> bool:
        return self.pos is not None and rect.collidepoint(self.pos)

    @classmethod
    def from_pygame(cls, event, pointer_pos: Optional[Tuple[int, int]] = None) -> "GuiEvent":
        try:
            event_type = int(event.type)
            payload = event.dict
        except AttributeError as exc:
            raise TypeError("expected pygame event with type and dict fields") from exc
        kind = _PYGAME_KIND_MAP.get(event_type, EventType.PASS)

        pos = payload.get("pos")
        if not (isinstance(pos, tuple) and len(pos) == 2):
            pos = None

        if event_type == pygame.MOUSEWHEEL and pos is None and pointer_pos is not None:
            pos = (int(pointer_pos[0]), int(pointer_pos[1]))

        rel = payload.get("rel")
        if not (isinstance(rel, tuple) and len(rel) == 2):
            rel = None

        key = payload.get("key")
        if key is not None:
            key = int(key)

        button = payload.get("button")
        if button is not None:
            button = int(button)

        wheel_x = int(payload.get("x", 0)) if event_type == pygame.MOUSEWHEEL else 0
        wheel_y = int(payload.get("y", 0)) if event_type == pygame.MOUSEWHEEL else 0
        text = payload.get("text")

        return cls(
            kind=kind,
            type=event_type,
            key=key,
            pos=pos,
            rel=rel,
            button=button,
            wheel_x=wheel_x,
            wheel_y=wheel_y,
            text=text,
            source_event=event,
        )
