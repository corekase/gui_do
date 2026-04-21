from __future__ import annotations

from typing import ClassVar, Dict, Optional

from pygame import Rect

from .toggle_control import ToggleControl


class ButtonGroupControl(ToggleControl):
    """Mutually exclusive grouped button based on toggle behavior."""

    _selection_by_group: ClassVar[Dict[str, str]] = {}

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        group: str,
        text: str,
        selected: bool = False,
    ) -> None:
        super().__init__(control_id, rect, text_on=text, text_off=text, pushed=selected, on_toggle=None)
        self.group = group
        if selected:
            ButtonGroupControl._selection_by_group[self.group] = self.control_id

    @property
    def button_id(self) -> str:
        return ButtonGroupControl._selection_by_group.get(self.group, self.control_id)

    def handle_event(self, event, app) -> bool:
        handled = super().handle_event(event, app)
        if not handled or not self.pushed:
            return handled
        previous = ButtonGroupControl._selection_by_group.get(self.group)
        ButtonGroupControl._selection_by_group[self.group] = self.control_id
        if previous == self.control_id:
            return True
        self.pushed = True
        self._clear_peer_selection(app)
        return True

    def _clear_peer_selection(self, app) -> None:
        stack = list(app.scene.nodes)
        while stack:
            node = stack.pop()
            children = getattr(node, "children", None)
            if children:
                stack.extend(children)
            if isinstance(node, ButtonGroupControl) and node.group == self.group and node.control_id != self.control_id:
                node.pushed = False
