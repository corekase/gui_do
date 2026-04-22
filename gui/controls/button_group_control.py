from __future__ import annotations

from typing import ClassVar, Dict, Optional
from typing import TYPE_CHECKING

from pygame import Rect

from ..core.gui_event import GuiEvent
from .toggle_control import ToggleControl

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication


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
        style: str = "box",
    ) -> None:
        super().__init__(control_id, rect, text_on=text, text_off=text, pushed=selected, on_toggle=None, style=style)
        self.group = group
        if selected:
            ButtonGroupControl._selection_by_group[self.group] = self.control_id

    @classmethod
    def clear_group_registry(cls, group: str | None = None) -> None:
        """Remove stale group selection entries.

        When *group* is given, only that group's entry is cleared.
        When *group* is ``None``, the entire class-level registry is cleared.
        This is primarily for test isolation between independent app instances.
        """
        if group is None:
            cls._selection_by_group.clear()
        else:
            cls._selection_by_group.pop(group, None)

    def on_mount(self, _parent) -> None:
        if self.pushed:
            ButtonGroupControl._selection_by_group[self.group] = self.control_id

    def on_unmount(self, _parent) -> None:
        if ButtonGroupControl._selection_by_group.get(self.group) == self.control_id:
            del ButtonGroupControl._selection_by_group[self.group]

    @property
    def button_id(self) -> str:
        return ButtonGroupControl._selection_by_group.get(self.group, self.control_id)

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            self.hovered = False
            return False

        raw = event.pos
        if isinstance(raw, tuple) and len(raw) == 2:
            self.hovered = self.rect.collidepoint(raw)
        if not event.is_mouse_down(1):
            return False
        if not (isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw)):
            return False

        previous = ButtonGroupControl._selection_by_group.get(self.group)
        if previous == self.control_id and self.pushed:
            return True

        self.pushed = True
        ButtonGroupControl._selection_by_group[self.group] = self.control_id
        self._clear_peer_selection(app)
        return True

    def _clear_peer_selection(self, app) -> None:
        stack = list(app.scene.nodes)
        while stack:
            node = stack.pop()
            stack.extend(node.children)
            if isinstance(node, ButtonGroupControl) and node.group == self.group and node.control_id != self.control_id:
                node.pushed = False
