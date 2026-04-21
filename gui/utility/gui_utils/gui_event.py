from __future__ import annotations

from typing import Optional, Tuple

from ..events import BaseEvent, Event, GuiError
from ...widgets.window import Window


class GuiEvent(BaseEvent):
    """Framework event envelope with normalized optional payload fields.

    Incoming event kwargs can originate from external systems and tests with
    varying types. This class performs strict type normalization so dispatch
    layers can rely on stable, typed attributes.
    """

    def __init__(
        self,
        event_type: Event,
        *,
        key: Optional[int] = None,
        pos: Optional[Tuple[int, int]] = None,
        rel: Optional[Tuple[int, int]] = None,
        button: Optional[int] = None,
        widget_id: Optional[str] = None,
        group: Optional[str] = None,
        window: Optional[Window] = None,
        task_panel: bool = False,
    ) -> None:
        """Create an event with explicit payload fields."""
        if key is not None and type(key) is not int:
            raise GuiError(f'event key must be int when provided, got: {key!r}')
        if pos is not None and (not isinstance(pos, tuple) or len(pos) != 2 or type(pos[0]) is not int or type(pos[1]) is not int):
            raise GuiError(f'event pos must be a tuple of two ints when provided, got: {pos!r}')
        if rel is not None and (not isinstance(rel, tuple) or len(rel) != 2 or type(rel[0]) is not int or type(rel[1]) is not int):
            raise GuiError(f'event rel must be a tuple of two ints when provided, got: {rel!r}')
        if button is not None and type(button) is not int:
            raise GuiError(f'event button must be int when provided, got: {button!r}')
        if widget_id is not None and not isinstance(widget_id, str):
            raise GuiError(f'event widget_id must be str when provided, got: {widget_id!r}')
        if group is not None and not isinstance(group, str):
            raise GuiError(f'event group must be str when provided, got: {group!r}')
        if window is not None and not isinstance(window, Window):
            raise GuiError(f'event window must be a Window when provided, got: {window!r}')
        if not isinstance(task_panel, bool):
            raise GuiError(f'event task_panel must be bool when provided, got: {task_panel!r}')
        super().__init__(event_type)
        self.key: Optional[int] = key
        self.pos: Optional[Tuple[int, int]] = pos
        self.rel: Optional[Tuple[int, int]] = rel
        self.button: Optional[int] = button
        self.widget_id: Optional[str] = widget_id
        self.group: Optional[str] = group
        self.window: Optional[Window] = window
        self.task_panel: bool = task_panel
