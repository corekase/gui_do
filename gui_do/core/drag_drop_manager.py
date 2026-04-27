"""DragDropManager — drag-and-drop session management."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..core.scene import Scene
    from ..theme.color_theme import ColorTheme
    from ..core.ui_node import UiNode


@dataclass
class DragPayload:
    drag_id: str
    data: Any = None
    ghost_surface: "Optional[pygame.Surface]" = None
    ghost_offset: Tuple[int, int] = (0, 0)


@dataclass
class _DragSession:
    source: "UiNode"
    payload: DragPayload
    start_pos: Tuple[int, int]
    current_pos: Tuple[int, int]
    current_target: "Optional[UiNode]" = None
    drag_threshold_met: bool = False

    DRAG_THRESHOLD: int = 6


class DragDropManager:
    """Manages drag-and-drop sessions within a scene."""

    def __init__(self, drag_threshold: int = 6) -> None:
        self._session: Optional[_DragSession] = None
        self._drag_threshold: int = drag_threshold

    @property
    def is_active(self) -> bool:
        return self._session is not None and self._session.drag_threshold_met

    @property
    def active_payload(self) -> Optional[DragPayload]:
        if self._session is not None and self._session.drag_threshold_met:
            return self._session.payload
        return None

    def route_event(self, event: GuiEvent, scene: "Scene", app: "GuiApplication") -> bool:
        """Process mouse events for drag-and-drop. Returns True if consumed."""
        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            pos = event.pos
            node = self._find_draggable(scene, pos)
            if node is not None:
                payload = node.on_drag_start(event)
                if payload is not None:
                    self._session = _DragSession(
                        source=node,
                        payload=payload,
                        start_pos=pos,
                        current_pos=pos,
                    )
                    return True  # consumed — prevent scene from processing it
            return False

        if event.kind == EventType.MOUSE_MOTION and self._session is not None:
            pos = event.pos
            self._session.current_pos = pos
            if not self._session.drag_threshold_met:
                dx = pos[0] - self._session.start_pos[0]
                dy = pos[1] - self._session.start_pos[1]
                if math.hypot(dx, dy) >= self._drag_threshold:
                    self._session.drag_threshold_met = True
            if self._session.drag_threshold_met:
                new_target = self._find_drop_target(scene, pos, self._session.payload)
                old_target = self._session.current_target
                if new_target is not old_target:
                    if old_target is not None:
                        try:
                            old_target.on_drag_leave(self._session.payload)
                        except Exception:
                            pass
                    if new_target is not None:
                        try:
                            new_target.on_drag_enter(self._session.payload)
                        except Exception:
                            pass
                    self._session.current_target = new_target
                app.invalidation.invalidate_all()
            return self._session.drag_threshold_met

        if event.kind == EventType.MOUSE_BUTTON_UP and event.button == 1:
            if self._session is None:
                return False
            session = self._session
            self._session = None
            if not session.drag_threshold_met:
                return False
            pos = event.pos
            target = self._find_drop_target(scene, pos, session.payload)
            accepted = False
            if target is not None:
                try:
                    accepted = bool(target.on_drop(session.payload, pos))
                except Exception:
                    pass
            try:
                session.source.on_drag_end(accepted)
            except Exception:
                pass
            app.invalidation.invalidate_all()
            return True

        return False

    def cancel(self, app: "GuiApplication") -> None:
        if self._session is None:
            return
        session = self._session
        self._session = None
        if session.current_target is not None:
            try:
                session.current_target.on_drag_leave(session.payload)
            except Exception:
                pass
        try:
            session.source.on_drag_end(False)
        except Exception:
            pass
        app.invalidation.invalidate_all()

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.is_active or self._session is None:
            return
        payload = self._session.payload
        pos = self._session.current_pos
        if payload.ghost_surface is not None:
            ox, oy = payload.ghost_offset
            surface.blit(payload.ghost_surface, (pos[0] - ox, pos[1] - oy))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_draggable(self, scene: "Scene", pos: Tuple[int, int]) -> "Optional[UiNode]":
        """Walk scene nodes and find first that accepts drag-start at pos."""
        for node in reversed(list(scene._nodes)):
            found = self._find_draggable_in_node(node, pos)
            if found is not None:
                return found
        return None

    def _find_draggable_in_node(self, node: "UiNode", pos: Tuple[int, int]) -> "Optional[UiNode]":
        if not node.visible or not node.enabled:
            return None
        # Check children first (depth-first)
        children = getattr(node, "children", [])
        for child in reversed(children):
            found = self._find_draggable_in_node(child, pos)
            if found is not None:
                return found
        if node.rect.collidepoint(pos):
            payload = node.on_drag_start.__func__ if hasattr(node.on_drag_start, "__func__") else None
            # Just attempt the call to check overriding — we rely on on_drag_start returning None by default
            try:
                test_result = node.on_drag_start(GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=pos, button=1))
                if test_result is not None:
                    return node
            except Exception:
                pass
        return None

    def _find_drop_target(self, scene: "Scene", pos: Tuple[int, int], payload: DragPayload) -> "Optional[UiNode]":
        for node in reversed(list(scene._nodes)):
            found = self._find_drop_target_in_node(node, pos, payload)
            if found is not None:
                return found
        return None

    def _find_drop_target_in_node(self, node: "UiNode", pos: Tuple[int, int], payload: DragPayload) -> "Optional[UiNode]":
        if not node.visible or not node.enabled:
            return None
        children = getattr(node, "children", [])
        for child in reversed(children):
            found = self._find_drop_target_in_node(child, pos, payload)
            if found is not None:
                return found
        if node.rect.collidepoint(pos) and node.accepts_drop(payload):
            return node
        return None
