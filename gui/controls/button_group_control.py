from __future__ import annotations

from typing import Callable, ClassVar, Dict, Optional
from typing import TYPE_CHECKING

import pygame
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
        on_activate: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(control_id, rect, text_on=text, text_off=text, pushed=selected, on_toggle=None, style=style)
        self.group = group
        self.on_activate = on_activate
        if selected:
            ButtonGroupControl._selection_by_group[self.group] = self.control_id
        elif self.group not in ButtonGroupControl._selection_by_group:
            self.pushed = True
            ButtonGroupControl._selection_by_group[self.group] = self.control_id

    def _invoke_activate(self) -> None:
        if self.on_activate is not None:
            self.on_activate()

    def _invoke_click(self) -> None:
        """Keyboard-activation entry point used by the focus manager's armed-visual path."""
        previous = ButtonGroupControl._selection_by_group.get(self.group)
        if previous != self.control_id or not self.pushed:
            self.pushed = True
            ButtonGroupControl._selection_by_group[self.group] = self.control_id
            if self.parent is not None:
                self._clear_peer_selection_from_nodes([self.parent])
        self._invoke_activate()

    def set_on_activate(self, callback: Optional[Callable[[], None]]) -> None:
        """Replace the activation callback at runtime. Pass None to remove it."""
        if callback is not None and not callable(callback):
            raise ValueError("on_activate callback must be callable or None")
        self.on_activate = callback

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
        if _parent is None:
            if self.pushed:
                ButtonGroupControl._selection_by_group[self.group] = self.control_id
            return

        selected_id = ButtonGroupControl._selection_by_group.get(self.group)
        if selected_id is not None and selected_id != self.control_id and not self._group_peer_exists_in_nodes([_parent], selected_id):
            # Ignore stale registry entries from prior scenes/apps.
            ButtonGroupControl._selection_by_group.pop(self.group, None)
            selected_id = None

        if self.pushed:
            ButtonGroupControl._selection_by_group[self.group] = self.control_id
            self._clear_peer_selection_from_nodes([_parent])
            return

        if selected_id is None:
            self.pushed = True
            ButtonGroupControl._selection_by_group[self.group] = self.control_id
            return

        if selected_id == self.control_id:
            self.pushed = True

    def on_unmount(self, _parent) -> None:
        if ButtonGroupControl._selection_by_group.get(self.group) != self.control_id:
            return

        replacement = self._first_group_peer_from_nodes([_parent] if _parent is not None else [])
        if replacement is None:
            ButtonGroupControl._selection_by_group.pop(self.group, None)
            return
        replacement.pushed = True
        ButtonGroupControl._selection_by_group[self.group] = replacement.control_id
        replacement._clear_peer_selection_from_nodes([_parent])

    @property
    def button_id(self) -> str:
        return ButtonGroupControl._selection_by_group.get(self.group, self.control_id)

    def _activate(self, app: "GuiApplication") -> bool:
        previous = ButtonGroupControl._selection_by_group.get(self.group)
        if previous != self.control_id or not self.pushed:
            self.pushed = True
            ButtonGroupControl._selection_by_group[self.group] = self.control_id
            self._clear_peer_selection(app)
        self._invoke_activate()
        return True

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
        return self._activate(app)

    @staticmethod
    def _walk_nodes(nodes) -> list:
        queue = [node for node in nodes if node is not None]
        visited = []
        while queue:
            node = queue.pop(0)
            visited.append(node)
            queue.extend(node.children)
        return visited

    def _first_group_peer_from_nodes(self, nodes):
        for node in self._walk_nodes(nodes):
            if isinstance(node, ButtonGroupControl) and node.group == self.group and node.control_id != self.control_id:
                return node
        return None

    def _group_peer_exists_in_nodes(self, nodes, control_id: str) -> bool:
        for node in self._walk_nodes(nodes):
            if isinstance(node, ButtonGroupControl) and node.group == self.group and node.control_id == control_id:
                return True
        return False

    def _clear_peer_selection_from_nodes(self, nodes) -> None:
        for node in self._walk_nodes(nodes):
            if isinstance(node, ButtonGroupControl) and node.group == self.group and node.control_id != self.control_id:
                node.pushed = False

    def _clear_peer_selection(self, app) -> None:
        self._clear_peer_selection_from_nodes(app.scene.nodes)
