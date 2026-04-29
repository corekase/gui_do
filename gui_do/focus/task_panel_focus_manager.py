from __future__ import annotations

from typing import Dict, Optional, TYPE_CHECKING

from ..events.gui_event import EventType
from ..controls.base.ui_node import UiNode

if TYPE_CHECKING:
    from ..controls.chrome.task_panel_control import TaskPanelControl


class TaskPanelFocusManager:
    """Own keyboard-only focus cycling for the scene task panel."""

    _POINTER_EVENT_KINDS = frozenset((
        EventType.MOUSE_BUTTON_DOWN,
        EventType.MOUSE_BUTTON_UP,
        EventType.MOUSE_MOTION,
        EventType.MOUSE_WHEEL,
    ))

    def __init__(self) -> None:
        self._active_panel = None
        self._remembered_control_id_by_scope: Dict[str, str] = {}
        self._saved_focus_node = None

    @property
    def active_panel(self):
        return self._active_panel

    @property
    def is_active(self) -> bool:
        return self._active_panel is not None

    def is_active_for(self, panel) -> bool:
        return self._active_panel is panel

    def toggle(self, scene, app) -> bool:
        if self._active_panel is not None:
            return self.exit(scene, app)
        return self.enter(scene, app)

    def enter(self, scene, app) -> bool:
        panel = self._find_task_panel(scene)
        if panel is None:
            return False

        candidates = self._candidate_controls(panel)
        if not candidates:
            return False

        self._saved_focus_node = getattr(app.focus, "focused_node", None)
        self._active_panel = panel
        panel.set_focus_mode(True)

        target = self._remembered_control(scene, panel, candidates)
        if target is None:
            target = candidates[0]
        app.focus.set_focus(target, via_keyboard=True)
        self._remember_selection(scene, panel, target)
        return True

    def exit(self, scene, app) -> bool:
        panel = self._active_panel
        if panel is None:
            return False

        current = getattr(app.focus, "focused_node", None)
        candidates = self._candidate_controls(panel)
        if current in candidates:
            self._remember_selection(scene, panel, current)

        panel.set_focus_mode(False)
        self._active_panel = None

        previous = self._saved_focus_node
        self._saved_focus_node = None
        if self._is_focus_target_valid(scene, previous, app):
            app.focus.set_focus(previous)
        else:
            app.focus.clear_focus()
        return True

    def cycle(self, scene, app, *, forward: bool = True) -> bool:
        panel = self._active_panel
        if panel is None:
            return False

        candidates = self._candidate_controls(panel)
        if not candidates:
            return self.exit(scene, app)

        current = getattr(app.focus, "focused_node", None)
        if current not in candidates:
            target = self._remembered_control(scene, panel, candidates)
            if target is None:
                target = candidates[0]
            app.focus.set_focus(target, via_keyboard=True)
            self._remember_selection(scene, panel, target)
            return True

        # Match normal Tab traversal semantics: after the focus hint times out,
        # first Tab only re-shows the hint and does not move focus.
        if not app.focus.should_draw_focus_hint():
            app.focus.show_keyboard_hint_for_current_focus()
            return True

        current_index = next((i for i, node in enumerate(candidates) if node is current), 0)
        offset = 1 if forward else -1
        next_index = (current_index + offset) % len(candidates)
        target = candidates[next_index]
        app.focus.set_focus(target, via_keyboard=True)
        self._remember_selection(scene, panel, target)
        return True

    def revalidate(self, scene, app) -> None:
        panel = self._active_panel
        if panel is None:
            return
        if not self._is_panel_valid(scene, panel):
            self.exit(scene, app)
            return

        candidates = self._candidate_controls(panel)
        if not candidates:
            self.exit(scene, app)
            return

        current = getattr(app.focus, "focused_node", None)
        if current in candidates:
            return

        target = self._remembered_control(scene, panel, candidates)
        if target is None:
            target = candidates[0]
        app.focus.set_focus(target, via_keyboard=True)
        self._remember_selection(scene, panel, target)

    def should_exit_for_pointer_event(self, event, app) -> bool:
        panel = self._active_panel
        if panel is None:
            return False
        if getattr(event, "kind", None) not in self._POINTER_EVENT_KINDS:
            return False
        pointer = event.pos if isinstance(event.pos, tuple) and len(event.pos) == 2 else getattr(app, "logical_pointer_pos", None)
        if not (isinstance(pointer, tuple) and len(pointer) == 2):
            return False
        return not panel.rect.collidepoint(pointer)

    def _find_task_panel(self, scene) -> Optional["TaskPanelControl"]:
        for node in scene._walk_nodes():
            if node.is_task_panel() and node.visible and node.enabled:
                return node
        return None

    def _candidate_controls(self, panel) -> list:
        candidates = []
        seen_object_ids = set()
        seen_control_ids = set()
        ordered_nodes = panel.find_descendants(lambda candidate: True)
        read_focus_controls = getattr(panel, "task_panel_focus_controls", None)
        if callable(read_focus_controls):
            ordered_nodes = list(read_focus_controls())
        for node in ordered_nodes:
            object_id = id(node)
            if object_id in seen_object_ids:
                continue
            if node.control_id in seen_control_ids:
                continue
            if not self._is_descendant_focusable(node, panel):
                continue
            if not self._is_task_panel_focus_candidate(node):
                continue
            seen_object_ids.add(object_id)
            seen_control_ids.add(node.control_id)
            candidates.append(node)
        return candidates

    @staticmethod
    def _is_task_panel_focus_candidate(node) -> bool:
        # Built-in task panel mode owns its own focus list, independent from
        # normal scene Tab order. Include standard focusable controls and
        # key-activatable actionable controls even when tab_index is -1.
        if bool(node.accepts_focus()):
            return True
        invokes_click = getattr(type(node), "_invoke_click", None) is not UiNode._invoke_click
        arms_focus_visual = (
            getattr(type(node), "should_arm_focus_activation_for_event", None)
            is not UiNode.should_arm_focus_activation_for_event
        )
        if not (invokes_click or arms_focus_visual):
            return False
        return bool(getattr(node, "key_activatable", True))

    @staticmethod
    def _is_descendant_focusable(node, panel) -> bool:
        current = node
        while current is not None:
            if not current.visible or not current.enabled:
                return False
            if current is panel:
                return True
            current = current.parent
        return False

    def _remembered_control(self, scene, panel, candidates):
        remembered_id = self._remembered_control_id_by_scope.get(self._scope_key(scene, panel))
        if not remembered_id:
            return None
        for candidate in candidates:
            if candidate.control_id == remembered_id:
                return candidate
        return None

    def _remember_selection(self, scene, panel, node) -> None:
        self._remembered_control_id_by_scope[self._scope_key(scene, panel)] = str(node.control_id)

    @staticmethod
    def _scope_key(scene, panel) -> str:
        return f"{id(scene)}::{getattr(panel, 'control_id', '')}"

    @staticmethod
    def _is_panel_valid(scene, panel) -> bool:
        if panel is None or not panel.visible or not panel.enabled:
            return False
        contains = getattr(scene, "contains", None)
        if callable(contains):
            return bool(contains(panel))
        return True

    @staticmethod
    def _is_focus_target_valid(scene, node, app) -> bool:
        if node is None:
            return False
        contains = getattr(scene, "contains", None)
        if callable(contains) and not contains(node):
            return False
        if not node.visible or not node.enabled:
            return False
        return bool(app.focus._is_focus_window_context_valid(node))
