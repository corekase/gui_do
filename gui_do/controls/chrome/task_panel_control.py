from typing import Dict, Tuple
from typing import TYPE_CHECKING

from pygame import Rect

from ...events.gui_event import GuiEvent, EventType
from ..composite.panel_control import PanelControl

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication


class TaskPanelControl(PanelControl):
    """Task panel with optional auto-hide animation and child position parenting."""

    _POINTER_EVENT_KINDS = frozenset((
        EventType.MOUSE_WHEEL,
        EventType.MOUSE_BUTTON_DOWN,
        EventType.MOUSE_BUTTON_UP,
        EventType.MOUSE_MOTION,
    ))

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        auto_hide: bool = True,
        hidden_peek_pixels: int = 4,
        animation_step_px: int = 4,
        dock_bottom: bool = False,
    ) -> None:
        super().__init__(control_id, rect)
        self.auto_hide = bool(auto_hide)
        self.hidden_peek_pixels = max(1, int(hidden_peek_pixels))
        self.animation_step_px = max(1, int(animation_step_px))
        self.dock_bottom = bool(dock_bottom)
        self._shown_y = int(rect.y)
        self._hidden_y = self._compute_hidden_y()
        self._hovered = False
        self._focus_mode_active = False
        self._child_local_offsets: Dict[object, Tuple[int, int]] = {}

    def _compute_hidden_y(self) -> int:
        if self.dock_bottom:
            return int(self._shown_y + self.rect.height - self.hidden_peek_pixels)
        return int(self._shown_y - self.rect.height + self.hidden_peek_pixels)

    def is_task_panel(self) -> bool:
        return True

    def add(self, child):
        added = super().add(child)
        self._child_local_offsets[added] = (added.rect.x - self.rect.x, added.rect.y - self.rect.y)
        return added

    def remove(self, child, *, dispose: bool = False) -> bool:
        removed = super().remove(child, dispose=dispose)
        if removed:
            self._child_local_offsets.pop(child, None)
        return removed

    def _sync_children_to_panel_position(self) -> None:
        live_children = set(self.children)
        for tracked_child in list(self._child_local_offsets):
            if tracked_child not in live_children:
                del self._child_local_offsets[tracked_child]

        for child in self.children:
            offset = self._child_local_offsets.get(child)
            if offset is None:
                offset = (child.rect.x - self.rect.x, child.rect.y - self.rect.y)
                self._child_local_offsets[child] = offset
            child.rect.topleft = (self.rect.x + offset[0], self.rect.y + offset[1])

    def set_auto_hide(self, auto_hide: bool) -> None:
        self.auto_hide = bool(auto_hide)

    def set_hidden_peek_pixels(self, hidden_peek_pixels: int) -> None:
        self.hidden_peek_pixels = max(1, int(hidden_peek_pixels))
        self._hidden_y = self._compute_hidden_y()

    def set_animation_step_px(self, animation_step_px: int) -> None:
        self.animation_step_px = max(1, int(animation_step_px))

    def set_focus_mode(self, active: bool) -> None:
        is_active = bool(active)
        if self._focus_mode_active == is_active:
            if is_active and not self._hovered:
                self._hovered = True
                self.invalidate()
            elif not is_active and self._hovered:
                self._hovered = False
                self.invalidate()
            return
        self._focus_mode_active = is_active
        self._hovered = is_active
        self.invalidate()

    def update(self, _dt_seconds: float) -> None:
        if self.visible and self.auto_hide:
            target = self._shown_y if self._hovered else self._hidden_y
            if self.rect.y < target:
                self.rect.y = min(target, self.rect.y + self.animation_step_px)
            elif self.rect.y > target:
                self.rect.y = max(target, self.rect.y - self.animation_step_px)
        self._sync_children_to_panel_position()
        super().update(0.0)

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        self._sync_children_to_panel_position()
        task_panel_focus = getattr(app, "task_panel_focus", None)
        focus_mode_active = False
        is_active_for = getattr(task_panel_focus, "is_active_for", None)
        if callable(is_active_for):
            focus_mode_active = (is_active_for(self) is True)
        raw = event.pos
        if focus_mode_active:
            self._hovered = True
        elif isinstance(raw, tuple) and len(raw) == 2:
            overlay = getattr(app, "overlay", None)
            has_palette = (
                callable(getattr(overlay, "has_overlay", None))
                and overlay.has_overlay("__command_palette__")
            )
            if not has_palette:
                self._hovered = self.rect.collidepoint(raw)
        result = super().handle_event(event, app)
        if result:
            return True
        if not focus_mode_active or event.kind not in self._POINTER_EVENT_KINDS:
            return False
        pointer = raw if isinstance(raw, tuple) and len(raw) == 2 else getattr(app, "logical_pointer_pos", None)
        if isinstance(pointer, tuple) and len(pointer) == 2 and self.rect.collidepoint(pointer):
            return True
        return False

    def reconcile_hover(self, wants_hover: bool) -> None:
        if self._hovered != wants_hover:
            self._hovered = wants_hover
            self.invalidate()
