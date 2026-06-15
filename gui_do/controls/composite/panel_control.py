from typing import Optional, List
from typing import TYPE_CHECKING

from pygame import Rect

from ...events.gui_event import GuiEvent, EventType
from ..base.ui_node import UiNode

if TYPE_CHECKING:
    import pygame
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme
    from ..layout.constraint_layout import ConstraintLayout


class PanelControl(UiNode):
    """Container control that owns child controls."""

    def __init__(self, control_id: str, rect: Rect, draw_background: bool = True, constraints: "Optional[ConstraintLayout]" = None) -> None:
        super().__init__(control_id, rect)
        self.children: List[UiNode] = []
        self.draw_background = bool(draw_background)
        self.constraints: "Optional[ConstraintLayout]" = constraints
        self._constraints_dirty = constraints is not None
        self._visuals = None
        self._drag_window = None
        self._drag_last_pos = None
        self._drag_offset = None
        self._active_window: Optional[UiNode] = None
        self._pending_capture_release_owner_id = None
        self._visual_size = None
        self._drag_pointer_sync_pending = False
        self._drag_blocked_last = False
        self._drag_shear_gutter_px = 5

    def end_window_drag(self, app: "GuiApplication | None" = None, *, release_pos=None) -> bool:
        """End active title-bar dragging and release pointer capture when owned."""
        if self._drag_window is None:
            return False
        dragged_window = self._drag_window
        drag_end_pos = release_pos if release_pos is not None else self._drag_last_pos
        if hasattr(self._drag_window, "on_titlebar_drag_end"):
            self._drag_window.on_titlebar_drag_end(drag_end_pos, blocked=self._drag_blocked_last)
        if app is not None and hasattr(app, "pointer_capture"):
            if app.pointer_capture.is_owned_by(self._drag_window.control_id):
                app.pointer_capture.end(self._drag_window.control_id)
        self._drag_window = None
        self._drag_last_pos = None
        self._drag_offset = None
        self._drag_pointer_sync_pending = False
        self._drag_blocked_last = False

        # Re-apply window layout from post-drag positions.
        if app is not None:
            tile_windows = getattr(app, "tile_windows", None)
            is_window_layout_enabled = getattr(app, "is_window_layout_enabled", None)
            if not callable(is_window_layout_enabled):
                is_window_layout_enabled = getattr(app, "is_window_tiling_enabled", None)
            auto_layout_enabled = True
            if callable(is_window_layout_enabled):
                auto_layout_enabled = bool(is_window_layout_enabled())
            if auto_layout_enabled:
                window_tiling = getattr(app, "window_tiling", None)
                arrange_drop = getattr(window_tiling, "arrange_windows_for_drop", None)
                if callable(arrange_drop):
                    try:
                        arrange_drop(dragged_window, drag_end_pos, promoted_windows=(dragged_window,))
                    except TypeError:
                        arrange_drop(dragged_window, drag_end_pos)
                elif callable(tile_windows):
                    tile_windows()
        return True

    def _window_drag_limits(self, window: UiNode, app: "GuiApplication") -> Optional[tuple[int, int, int, int]]:
        bounded_area_rect = getattr(app, "bounded_area_rect", None)
        if not callable(bounded_area_rect):
            return None

        allowed_rect = Rect(bounded_area_rect())
        min_left = int(allowed_rect.left)
        max_left = int(allowed_rect.right - window.rect.width)

        top_limit = int(allowed_rect.top)
        max_top = int(allowed_rect.bottom - window.rect.height)
        return (min_left, max_left, top_limit, max_top)

    def _clamp_window_drag_target(self, window: UiNode, target_x: int, target_y: int, app: "GuiApplication") -> tuple[int, int]:
        limits = self._window_drag_limits(window, app)
        if limits is None:
            return (int(target_x), int(target_y))

        min_left, max_left, top_limit, max_top = limits
        bottom_limit = int(max_top + window.rect.height)
        proposed_rect = Rect(window.rect)
        proposed_rect.topleft = (int(target_x), int(target_y))

        if max_left < min_left:
            proposed_rect.left = min_left
        else:
            proposed_rect.left = max(min_left, min(int(proposed_rect.left), max_left))

        if max_top < top_limit:
            proposed_rect.top = top_limit
        elif proposed_rect.top < top_limit:
            proposed_rect.top = top_limit
        elif proposed_rect.top > max_top:
            proposed_rect.top = max_top

        return (int(proposed_rect.left), int(proposed_rect.top))

    def _should_suppress_drag_shear(
        self,
        window: UiNode,
        app: "GuiApplication",
        *,
        attempted_dx: int,
        attempted_dy: int,
        drag_blocked: bool,
    ) -> bool:
        limits = self._window_drag_limits(window, app)
        if limits is None:
            return bool(drag_blocked)

        min_left, max_left, top_limit, max_top = limits
        gutter = max(1, int(self._drag_shear_gutter_px))

        left = int(window.rect.left)
        top = int(window.rect.top)
        at_left = left <= (int(min_left) + gutter)
        at_right = left >= (int(max_left) - gutter)
        at_top = top <= (int(top_limit) + gutter)
        at_bottom = top >= (int(max_top) - gutter)

        # Left/right gutters intentionally hard-disable shear to avoid visual
        # jitter at horizontal clamp boundaries.
        if at_left or at_right:
            return True

        push_x = (at_left and attempted_dx < 0) or (at_right and attempted_dx > 0)
        push_y = (at_top and attempted_dy < 0) or (at_bottom and attempted_dy > 0)

        if push_x:
            # Preserve shear while moving along an edge; only suppress when
            # pressure into the edge dominates tangential motion.
            push_mag_x = abs(int(attempted_dx))
            tangent_mag_x = abs(int(attempted_dy))
            if push_mag_x >= tangent_mag_x:
                return True

        if push_y:
            push_mag_y = abs(int(attempted_dy))
            tangent_mag_y = abs(int(attempted_dx))
            if push_mag_y >= tangent_mag_y:
                return True

        return False

    def _set_drag_logical_pointer(self, app: "GuiApplication", pointer_pos: tuple[int, int]) -> None:
        if not (hasattr(app, "set_logical_pointer_position") and callable(app.set_logical_pointer_position)):
            return
        app.set_logical_pointer_position((int(pointer_pos[0]), int(pointer_pos[1])), apply_constraints=False)
        self._drag_pointer_sync_pending = True

    def _cancel_window_tiling_motion(self, window: UiNode, app: "GuiApplication") -> None:
        """Stop per-window tiling animation so drag stays mouse-anchored."""
        tweens = getattr(app, "tweens", None)
        cancel_for_tag = getattr(tweens, "cancel_all_for_tag", None)
        if callable(cancel_for_tag):
            try:
                cancel_for_tag(f"window_tiling:{id(window)}")
            except Exception:
                pass
        setattr(window, "_window_tiling_animating", False)
        rect = Rect(getattr(window, "rect", Rect(0, 0, 0, 0)))
        setattr(
            window,
            "_window_tiling_target_rect",
            Rect(int(rect.x), int(rect.y), int(rect.width), int(rect.height)),
        )

    def _preview_window_tiling_during_drag(self, window: UiNode, pointer_pos, app: "GuiApplication") -> None:
        """Live-reflow the non-dragged windows toward the drop slot under the pointer."""
        if app is None or window is None or not (isinstance(pointer_pos, tuple) and len(pointer_pos) == 2):
            return
        is_window_layout_enabled = getattr(app, "is_window_layout_enabled", None)
        if not callable(is_window_layout_enabled):
            is_window_layout_enabled = getattr(app, "is_window_tiling_enabled", None)
        if callable(is_window_layout_enabled) and not bool(is_window_layout_enabled()):
            return
        window_tiling = getattr(app, "window_tiling", None)
        arrange_during_drag = getattr(window_tiling, "arrange_windows_during_drag", None)
        if not callable(arrange_during_drag):
            return
        try:
            arrange_during_drag(window, (int(pointer_pos[0]), int(pointer_pos[1])))
        except Exception:
            pass

    def _mark_constraints_dirty(self) -> None:
        self._constraints_dirty = self.constraints is not None

    def _apply_constraints_if_dirty(self) -> None:
        if not self._constraints_dirty or self.constraints is None:
            return
        self.constraints.apply(self.rect)
        self._constraints_dirty = False

    def _is_window_like(self, child: UiNode) -> bool:
        return child.is_window()

    def _set_window_active_state(self, window: UiNode, is_active: bool) -> None:
        window.set_active(bool(is_active))
        if is_active:
            self._active_window = window
        elif self._active_window is window:
            self._active_window = None

    def _top_window_at(self, pos) -> Optional[UiNode]:
        for child in reversed(self.children):
            if child.visible and child.enabled and self._is_window_like(child) and child.rect.collidepoint(pos):
                return child
        return None

    def _top_task_panel_at(self, pos) -> Optional[UiNode]:
        for child in reversed(self.children):
            if not (child.visible and child.enabled and child.is_task_panel()):
                continue
            blocks_pointer_at = getattr(child, "blocks_pointer_at", None)
            if callable(blocks_pointer_at):
                if blocks_pointer_at(pos):
                    return child
                continue
            if child.rect.collidepoint(pos):
                return child
        return None

    def _clear_window_lower_control_hovers(self) -> None:
        for child in self.children:
            if not self._is_window_like(child):
                continue
            clear_hover = getattr(child, "clear_lower_control_hover", None)
            if callable(clear_hover):
                clear_hover()

    def _clear_occluded_window_hovers_for_pointer(self, pointer_pos) -> bool:
        if not (isinstance(pointer_pos, tuple) and len(pointer_pos) == 2):
            return False
        if self._top_task_panel_at(pointer_pos) is None:
            return False
        self._clear_window_lower_control_hovers()
        return True

    def _consume_pointer_for_top_task_panel(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        raw = event.pos
        if not (isinstance(raw, tuple) and len(raw) == 2):
            return False
        if event.kind not in {
            EventType.MOUSE_MOTION,
            EventType.MOUSE_BUTTON_DOWN,
            EventType.MOUSE_BUTTON_UP,
            EventType.MOUSE_WHEEL,
        }:
            return False
        top_task_panel = self._top_task_panel_at(raw)
        if top_task_panel is None:
            return False
        self._clear_occluded_window_hovers_for_pointer(raw)
        consumed = bool(top_task_panel.handle_routed_event(event, app, theme=theme))
        if consumed or event.propagation_stopped or event.default_prevented:
            return True
        event.prevent_default()
        event.stop_propagation()
        return True

    def _dispatch_lower_control_event(self, window: UiNode, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        handle = getattr(window, "handle_lower_control_event", None)
        if not callable(handle):
            return False
        consumed = bool(handle(event, app, theme))
        for request in self._consume_window_titlebar_control_requests(window):
            if self._dispatch_window_titlebar_control_action(window, request, app):
                consumed = True
        if consumed:
            event.prevent_default()
            event.stop_propagation()
        return consumed

    @staticmethod
    def _consume_window_titlebar_control_requests(window: UiNode) -> tuple[str, ...]:
        consume_requests = getattr(window, "consume_titlebar_control_requests", None)
        if callable(consume_requests):
            requests = consume_requests()
            if isinstance(requests, tuple):
                return requests
            if isinstance(requests, list):
                return tuple(requests)
            return ()

        requests: list[str] = []
        consume_hide_click = getattr(window, "consume_hide_control_click_request", None)
        if callable(consume_hide_click) and bool(consume_hide_click()):
            requests.append("hide")
        consume_click = getattr(window, "consume_lower_control_click_request", None)
        if callable(consume_click) and bool(consume_click()):
            requests.append("lower")
        return tuple(requests)

    def _dispatch_window_titlebar_control_action(self, window: UiNode, request: str, app: "GuiApplication") -> bool:
        if request == "hide":
            if not self._set_window_visible_state(window, False, app):
                lower_window = getattr(app, "lower_window", None) if app is not None else None
                if callable(lower_window):
                    lower_window(window, relayout=False)
                window.visible = False
                tile_windows = getattr(app, "tile_windows", None) if app is not None else None
                if callable(tile_windows):
                    try:
                        tile_windows(as_visibility_event=True, force=True)
                    except TypeError:
                        tile_windows()
            return True
        if request == "lower":
            lower_window = getattr(app, "lower_window", None) if app is not None else None
            if callable(lower_window) and bool(lower_window(window)):
                return True

            self._lower_window(window)
            new_top = self._top_visible_window()
            if new_top is None:
                self._clear_active_windows()
            else:
                self._set_active_window(new_top)

            # Legacy fallback for callers that do not yet expose the app-level
            # lower_window helper. The new app API handles the enabled path.
            window_tiling = getattr(app, "window_tiling", None) if app is not None else None
            arrange_drop = getattr(window_tiling, "arrange_windows_for_drop", None) if window_tiling is not None else None
            tile_windows = getattr(app, "tile_windows", None) if app is not None else None
            is_window_layout_enabled = getattr(app, "is_window_layout_enabled", None) if app is not None else None
            if not callable(is_window_layout_enabled):
                is_window_layout_enabled = getattr(app, "is_window_tiling_enabled", None) if app is not None else None
            auto_layout_enabled = True
            if callable(is_window_layout_enabled):
                auto_layout_enabled = bool(is_window_layout_enabled())
            if auto_layout_enabled:
                used_drop_relayout = False
                if callable(arrange_drop):
                    bounded_area_rect = getattr(app, "bounded_area_rect", None) if app is not None else None
                    if callable(bounded_area_rect):
                        bounds = Rect(bounded_area_rect())
                    else:
                        surface = getattr(app, "surface", None) if app is not None else None
                        bounds = Rect(surface.get_rect()) if surface is not None else Rect(0, 0, 0, 0)
                    gap = int(getattr(window_tiling, "gap", 16)) if window_tiling is not None else 16
                    drop_point = (int(window.rect.centerx), int(bounds.bottom + max(4, gap * 2)))
                    try:
                        arrange_drop(window, drop_point, force=True, demoted_windows=(window,))
                        used_drop_relayout = True
                    except TypeError:
                        try:
                            arrange_drop(window, drop_point, force=True)
                            used_drop_relayout = True
                        except TypeError:
                            try:
                                arrange_drop(window, drop_point, demoted_windows=(window,))
                                used_drop_relayout = True
                            except Exception:
                                used_drop_relayout = False
                        except Exception:
                            used_drop_relayout = False
                    except Exception:
                        try:
                            arrange_drop(window, drop_point)
                            used_drop_relayout = True
                        except Exception:
                            used_drop_relayout = False

                if not used_drop_relayout and callable(tile_windows):
                    try:
                        tile_windows(as_visibility_event=True, force=True)
                    except TypeError:
                        tile_windows()
            return True
        return False

    @staticmethod
    def _set_window_visible_state(window: UiNode, next_visible: bool, app: "GuiApplication") -> bool:
        for presentation in PanelControl._iter_window_presentations(app):
            handle_window_toggle = getattr(presentation, "handle_window_toggle", None)
            if callable(handle_window_toggle) and bool(handle_window_toggle(window, bool(next_visible))):
                return True
        setter = PanelControl._resolve_window_visibility_setter(app, window)
        if callable(setter):
            setter(bool(next_visible))
            return True
        return False

    @staticmethod
    def _iter_window_presentations(app: "GuiApplication"):
        app_presentation = getattr(app, "window_presentation", None)
        if app_presentation is not None:
            yield app_presentation
        features = getattr(app, "features", None)
        feature_hosts = getattr(features, "_feature_hosts", None)
        if isinstance(feature_hosts, dict):
            for host in feature_hosts.values():
                host_presentation = getattr(host, "window_presentation", None)
                if host_presentation is not None and host_presentation is not app_presentation:
                    yield host_presentation

    @staticmethod
    def _resolve_window_visibility_setter(app: "GuiApplication", window: UiNode):
        control_id = str(getattr(window, "control_id", "")).strip()
        if not control_id.endswith("_window"):
            return None
        window_key = control_id[: -len("_window")]
        if not window_key:
            return None
        method_name = f"set_{window_key}_window_visible"

        app_method = getattr(app, method_name, None)
        if callable(app_method):
            return app_method

        features = getattr(app, "features", None)
        feature_hosts = getattr(features, "_feature_hosts", None)
        if isinstance(feature_hosts, dict):
            for host in feature_hosts.values():
                host_method = getattr(host, method_name, None)
                if callable(host_method):
                    return host_method
        return None

    def _set_active_window(self, window: UiNode) -> None:
        is_valid_target = (
            window in self.children and self._is_window_like(window) and window.visible and window.enabled
        )
        target = window if is_valid_target else self._next_top_visible_window(excluding=window)
        if target is None:
            self._clear_active_windows()
            return
        for candidate in self.children:
            if self._is_window_like(candidate):
                self._set_window_active_state(candidate, candidate is target)

    def _clear_active_windows(self) -> None:
        active_window = self._active_window
        if active_window is not None and active_window in self.children and self._is_window_like(active_window):
            self._set_window_active_state(active_window, False)
            return
        for candidate in self.children:
            if self._is_window_like(candidate) and candidate.active:
                self._set_window_active_state(candidate, False)

    def _next_top_visible_window(self, excluding: Optional[UiNode] = None) -> Optional[UiNode]:
        for child in reversed(self.children):
            if child is excluding:
                continue
            if child.visible and child.enabled and self._is_window_like(child):
                return child
        return None

    def _top_visible_window(self) -> Optional[UiNode]:
        for child in reversed(self.children):
            if child.visible and child.enabled and self._is_window_like(child):
                return child
        return None

    def _on_window_visibility_changed(self, window: UiNode, old_visible: bool, new_visible: bool) -> None:
        if old_visible == new_visible:
            return
        if new_visible:
            self._raise_window(window)
            if window.enabled:
                self._set_active_window(window)
            else:
                self._set_window_active_state(window, False)
                next_window = self._next_top_visible_window(excluding=window)
                if next_window is None:
                    self._clear_active_windows()
                else:
                    self._set_active_window(next_window)
            return
        if self._drag_window is window:
            self._pending_capture_release_owner_id = window.control_id
            self._drag_window = None
            self._drag_last_pos = None
            self._drag_offset = None
            self._drag_blocked_last = False
        self._set_window_active_state(window, False)
        next_window = self._next_top_visible_window(excluding=window)
        if next_window is None:
            self._clear_active_windows()
            return
        self._set_active_window(next_window)

    def _on_window_enabled_changed(self, window: UiNode, old_enabled: bool, new_enabled: bool) -> None:
        if old_enabled == new_enabled:
            return
        if not window.visible:
            if self._drag_window is window:
                self._pending_capture_release_owner_id = window.control_id
                self._drag_window = None
                self._drag_last_pos = None
                self._drag_offset = None
                self._drag_blocked_last = False
            self._set_window_active_state(window, False)
            return
        if not new_enabled:
            was_active = bool(window.active)
            if self._drag_window is window:
                self._pending_capture_release_owner_id = window.control_id
                self._drag_window = None
                self._drag_last_pos = None
                self._drag_offset = None
                self._drag_blocked_last = False
            self._set_window_active_state(window, False)
            if not was_active:
                return
            next_window = self._next_top_visible_window(excluding=window)
            if next_window is None:
                self._clear_active_windows()
            else:
                self._set_active_window(next_window)
            return
        active_window = self._active_window
        if active_window is not None:
            if active_window not in self.children:
                active_window = None
            elif not (active_window.visible and active_window.enabled and self._is_window_like(active_window)):
                active_window = None
        if active_window is None:
            self._set_active_window(window)

    def _raise_window(self, window: UiNode) -> None:
        if window in self.children:
            self.children.remove(window)
            self.children.append(window)
        if window.visible and window.enabled:
            self._set_active_window(window)
            return
        active_window = self._top_visible_window()
        if active_window is None:
            self._clear_active_windows()
            return
        self._set_active_window(active_window)

    def _lower_window(self, window: UiNode) -> None:
        if window not in self.children:
            return
        self.children.remove(window)
        first_window_idx = None
        for idx, child in enumerate(self.children):
            if self._is_window_like(child):
                first_window_idx = idx
                break
        if first_window_idx is None:
            self.children.append(window)
        else:
            self.children.insert(first_window_idx, window)

        active_window = self._top_visible_window()
        if active_window is None:
            self._clear_active_windows()
            return
        self._set_active_window(active_window)

    def add(self, child: UiNode) -> UiNode:
        """Attach one child control and return it."""
        return self.add_child(child)

    def add_child(self, child: UiNode) -> UiNode:
        added = super().add_child(child)
        self._mark_constraints_dirty()
        self._apply_constraints_if_dirty()
        return added

    def add_at(self, child: UiNode, rel_x: int = 0, rel_y: int = 0) -> UiNode:
        """Attach *child* at a position relative to this panel's top-left corner.

        The child's rect dimensions are preserved; only its position is adjusted
        so that ``(0, 0)`` maps to this panel's ``rect.topleft``.  This is the
        preferred way to add children whose layout is expressed in panel-local
        coordinates rather than screen-space coordinates.

        Example::

            overlay.add_at(label, rel_x=8, rel_y=6)
        """
        offset_x = int(rel_x)
        offset_y = int(rel_y)
        # Track panel-local offsets so these children stay anchored if the panel moves.
        setattr(child, "_panel_local_offset", (offset_x, offset_y))
        child.rect.left = self.rect.left + offset_x
        child.rect.top = self.rect.top + offset_y
        return self.add(child)

    def set_rect(self, rect: Rect) -> None:
        old_rect = Rect(self.rect)
        super().set_rect(rect)
        if self.rect.topleft == old_rect.topleft:
            if self.rect.size != old_rect.size:
                self._mark_constraints_dirty()
                self._apply_constraints_if_dirty()
            return
        for child in self.children:
            local_offset = getattr(child, "_panel_local_offset", None)
            if (
                isinstance(local_offset, tuple)
                and len(local_offset) == 2
                and isinstance(local_offset[0], int)
                and isinstance(local_offset[1], int)
            ):
                child.set_pos(self.rect.left + local_offset[0], self.rect.top + local_offset[1])
        self._mark_constraints_dirty()
        self._apply_constraints_if_dirty()

    def set_pos(self, x: int, y: int) -> None:
        old_topleft = self.rect.topleft
        super().set_pos(x, y)
        if self.rect.topleft != old_topleft:
            for child in self.children:
                local_offset = getattr(child, "_panel_local_offset", None)
                if (
                    isinstance(local_offset, tuple)
                    and len(local_offset) == 2
                    and isinstance(local_offset[0], int)
                    and isinstance(local_offset[1], int)
                ):
                    child.set_pos(self.rect.left + local_offset[0], self.rect.top + local_offset[1])
            self._mark_constraints_dirty()
            self._apply_constraints_if_dirty()

    def resize(self, width: int, height: int) -> None:
        old_size = self.rect.size
        super().resize(width, height)
        if self.rect.size != old_size:
            self._mark_constraints_dirty()
            self._apply_constraints_if_dirty()

    @property
    def child_count(self) -> int:
        """Return the number of direct children."""
        return len(self.children)

    def has_child(self, child: UiNode) -> bool:
        """Return True when *child* is a direct child of this panel."""
        return child in self.children

    def window_count(self) -> int:
        """Return the number of direct children that are window-type nodes."""
        return sum(1 for c in self.children if self._is_window_like(c))

    def clear_children(self, *, dispose: bool = False) -> int:
        """Remove all direct children and return the count removed.

        Calls ``remove()`` for each child so that window management hooks
        (activation, drag-cancel) run correctly. Pass ``dispose=True`` to
        also call ``dispose()`` on every removed child.
        """
        count = 0
        for child in list(self.children):
            if self.remove(child, dispose=dispose):
                count += 1
        return count

    def remove(self, child: UiNode, *, dispose: bool = False) -> bool:
        if child not in self.children:
            return False

        was_window = self._is_window_like(child)
        was_active_window = bool(was_window and child.active)

        if self._drag_window is child:
            self._pending_capture_release_owner_id = child.control_id
            self._drag_window = None
            self._drag_last_pos = None
            self._drag_offset = None

        if was_window:
            self._set_window_active_state(child, False)

        if not self.remove_child(child, dispose=dispose):
            return False

        if was_active_window:
            next_window = self._top_visible_window()
            if next_window is None:
                self._clear_active_windows()
            else:
                self._set_active_window(next_window)
        self._mark_constraints_dirty()
        self._apply_constraints_if_dirty()
        return True

    def set_constraints(self, constraints: "Optional[ConstraintLayout]") -> None:
        self.constraints = constraints
        self._mark_constraints_dirty()
        self._apply_constraints_if_dirty()

    def _reapply_constraints(self) -> None:
        self._apply_constraints_if_dirty()

    def update(self, dt_seconds: float) -> None:
        self._reapply_constraints()
        for child in self.children:
            if child.visible or bool(getattr(child, "is_visibility_transition_active", lambda: False)()):
                child.update(dt_seconds)

    def on_event_capture(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        # Release pointer capture if needed
        if self._pending_capture_release_owner_id is not None:
            owner_id = self._pending_capture_release_owner_id
            if app.pointer_capture.is_owned_by(owner_id):
                app.pointer_capture.end(owner_id)
            self._pending_capture_release_owner_id = None

        # Cancel drag if window is no longer valid
        if self._drag_window is not None:
            invalid_drag_window = (
                self._drag_window not in self.children
                or not self._drag_window.visible
                or not self._drag_window.enabled
            )
            if invalid_drag_window:
                if app.pointer_capture.is_owned_by(self._drag_window.control_id):
                    app.pointer_capture.end(self._drag_window.control_id)
                self._drag_window = None
                self._drag_last_pos = None
                self._drag_offset = None

        raw = event.pos

        drag_pointer_event = bool(
            self._drag_window is not None
            and (event.is_mouse_motion() or event.is_mouse_up(1))
        )
        if not drag_pointer_event and self._consume_pointer_for_top_task_panel(event, app, theme=theme):
            return True

        if self._drag_window is None and (event.is_mouse_motion() or event.is_mouse_down(1) or event.is_mouse_up(1)):
            pressed_window = None
            for candidate in reversed(self.children):
                if not self._is_window_like(candidate):
                    continue
                is_pressed = getattr(candidate, "is_lower_control_pressed", None)
                if callable(is_pressed) and bool(is_pressed()):
                    pressed_window = candidate
                    break
            if pressed_window is not None:
                if self._dispatch_lower_control_event(pressed_window, event, app, theme):
                    return True

            if isinstance(raw, tuple) and len(raw) == 2:
                top_window = self._top_window_at(raw)
                if top_window is not None and top_window is not pressed_window:
                    if self._dispatch_lower_control_event(top_window, event, app, theme):
                        return True

                if event.is_mouse_motion():
                    for candidate in self.children:
                        if candidate is top_window:
                            continue
                        if not self._is_window_like(candidate):
                            continue
                        is_pressed = getattr(candidate, "is_lower_control_pressed", None)
                        if callable(is_pressed) and bool(is_pressed()):
                            continue
                        clear_hover = getattr(candidate, "clear_lower_control_hover", None)
                        if callable(clear_hover):
                            clear_hover()

        # --- Handle window chrome events before children ---
        # Mouse motion: dragging window
        if event.is_mouse_motion() and self._drag_window is not None:
            drag_pointer = raw if isinstance(raw, tuple) and len(raw) == 2 else self._drag_last_pos
            drag_blocked = False
            attempted_dx = 0
            attempted_dy = 0
            if isinstance(raw, tuple) and len(raw) == 2:
                if self._drag_offset is None:
                    self._drag_offset = (
                        int(raw[0] - self._drag_window.rect.left),
                        int(raw[1] - self._drag_window.rect.top),
                    )
                current_left = int(self._drag_window.rect.left)
                current_top = int(self._drag_window.rect.top)
                target_x = int(raw[0] - self._drag_offset[0])
                target_y = int(raw[1] - self._drag_offset[1])
                attempted_dx = int(target_x - current_left)
                attempted_dy = int(target_y - current_top)
                clamped_x, clamped_y = self._clamp_window_drag_target(self._drag_window, target_x, target_y, app)
                drag_blocked = (clamped_x != target_x) or (clamped_y != target_y)
                dx = int(clamped_x - current_left)
                dy = int(clamped_y - current_top)
                self._drag_window.move_by(dx, dy)
                if self._drag_offset is not None:
                    drag_pointer = (
                        int(self._drag_window.rect.left + self._drag_offset[0]),
                        int(self._drag_window.rect.top + self._drag_offset[1]),
                    )
            else:
                rel = event.rel
                if isinstance(rel, tuple) and len(rel) == 2:
                    dx, dy = int(rel[0]), int(rel[1])
                elif self._drag_last_pos is not None:
                    dx = int(raw[0] - self._drag_last_pos[0])
                    dy = int(raw[1] - self._drag_last_pos[1])
                else:
                    return False
                attempted_dx = int(dx)
                attempted_dy = int(dy)
                target_x = int(self._drag_window.rect.left + dx)
                target_y = int(self._drag_window.rect.top + dy)
                clamped_x, clamped_y = self._clamp_window_drag_target(self._drag_window, target_x, target_y, app)
                drag_blocked = (clamped_x != target_x) or (clamped_y != target_y)
                applied_dx = int(clamped_x - self._drag_window.rect.left)
                applied_dy = int(clamped_y - self._drag_window.rect.top)
                self._drag_window.move_by(applied_dx, applied_dy)
                if self._drag_offset is not None:
                    drag_pointer = (
                        int(self._drag_window.rect.left + self._drag_offset[0]),
                        int(self._drag_window.rect.top + self._drag_offset[1]),
                    )
                elif self._drag_last_pos is not None:
                    drag_pointer = (
                        int(self._drag_last_pos[0] + applied_dx),
                        int(self._drag_last_pos[1] + applied_dy),
                    )
            if isinstance(raw, tuple) and len(raw) == 2 and isinstance(drag_pointer, tuple) and len(drag_pointer) == 2:
                if (int(drag_pointer[0]), int(drag_pointer[1])) != (int(raw[0]), int(raw[1])):
                    self._set_drag_logical_pointer(app, (int(drag_pointer[0]), int(drag_pointer[1])))

            shear_suppressed = self._should_suppress_drag_shear(
                self._drag_window,
                app,
                attempted_dx=attempted_dx,
                attempted_dy=attempted_dy,
                drag_blocked=drag_blocked,
            )

            self._drag_last_pos = drag_pointer
            self._drag_blocked_last = shear_suppressed
            if hasattr(self._drag_window, "on_titlebar_drag_update"):
                self._drag_window.on_titlebar_drag_update(drag_pointer, blocked=shear_suppressed)
            self._preview_window_tiling_during_drag(self._drag_window, drag_pointer, app)
            event.prevent_default()
            event.stop_propagation()
            return True

        # Mouse up: end drag
        if event.is_mouse_up(1) and self._drag_window is not None:
            pointer_capture_owned = app.pointer_capture.is_owned_by(self._drag_window.control_id)
            was_relative_capture = bool(pointer_capture_owned and app.pointer_capture.use_relative_motion)
            self.end_window_drag(app, release_pos=raw)
            if was_relative_capture:
                logical_pointer = getattr(app, "logical_pointer_pos", None)
                raw_pointer = event.raw_pos if isinstance(event.raw_pos, tuple) and len(event.raw_pos) == 2 else raw
                if (
                    self._drag_pointer_sync_pending
                    or not (isinstance(logical_pointer, tuple) and len(logical_pointer) == 2)
                    or not (isinstance(raw_pointer, tuple) and len(raw_pointer) == 2)
                    or (int(logical_pointer[0]), int(logical_pointer[1])) != (int(raw_pointer[0]), int(raw_pointer[1]))
                ):
                    if hasattr(app, "sync_pointer_to_logical_position") and callable(app.sync_pointer_to_logical_position):
                        app.sync_pointer_to_logical_position(logical_pointer)
            event.prevent_default()
            event.stop_propagation()
            return True

        # Mouse down: check window chrome (titlebar/lower control)
        if event.is_mouse_down(1) and isinstance(raw, tuple) and len(raw) == 2:
            # Check all windows, topmost first
            for window in reversed(self.children):
                if not self._is_window_like(window) or not window.visible or not window.enabled:
                    continue
                if window.rect.collidepoint(raw):
                    self._set_active_window(window)
                    # Titlebar drag detection (assume y < titlebar_height is titlebar, or use a method if available)
                    titlebar_height = getattr(window, "titlebar_height", 32)
                    in_titlebar = False
                    if hasattr(window, "is_in_titlebar"):
                        in_titlebar = window.is_in_titlebar(raw)
                    else:
                        in_titlebar = (raw[1] - window.rect.top) < titlebar_height
                    window_tiling = getattr(app, "window_tiling", None)
                    is_top_z = getattr(window_tiling, "is_top_z_order_for_group", None)
                    if in_titlebar:
                        # Raise window on drag start WITHOUT layout solve
                        raise_window = getattr(app, "raise_window", None)
                        if callable(raise_window):
                            raise_window(window, relayout=False)
                        else:
                            self._raise_window(window)
                        self._drag_window = window
                        self._drag_last_pos = raw
                        self._drag_offset = (
                            int(raw[0] - window.rect.left),
                            int(raw[1] - window.rect.top),
                        )
                        self._drag_blocked_last = False
                        self._cancel_window_tiling_motion(window, app)
                        if getattr(window, "window_effects", {}).get("shear_enabled", True):
                            focus_manager = getattr(app, "focus", None)
                            if focus_manager is not None and hasattr(focus_manager, "clear_focus"):
                                focus_manager.clear_focus()
                        if hasattr(window, "on_titlebar_drag_start"):
                            window.on_titlebar_drag_start(raw, app.surface)
                        app.pointer_capture.begin(window.control_id, app.surface.get_rect(), use_relative_motion=True)
                        self._drag_pointer_sync_pending = False
                        event.prevent_default()
                        event.stop_propagation()
                        return True
                    else:
                        # Not a drag: only raise if not already top z-order for group
                        if callable(is_top_z) and is_top_z(window):
                            # Already top, just set active, do NOT consume event
                            self._set_active_window(window)
                            # Let event propagate to children (controls)
                            return self._dispatch_children(event, app, reverse=False, theme=theme)
                        else:
                            raise_window = getattr(app, "raise_window", None)
                            if callable(raise_window):
                                raise_window(window)
                            else:
                                self._raise_window(window)
                            # Do not consume event, let it propagate
                            return self._dispatch_children(event, app, reverse=False, theme=theme)
                    break

        # --- End window chrome handling ---

        # End drag if command palette is open or window cycle event
        if hasattr(app, "overlay") and callable(getattr(app.overlay, "has_overlay", None)):
            if app.overlay.has_overlay("__command_palette__"):
                self.end_window_drag(app)

        # Fallback: dispatch to children
        return self._dispatch_children(event, app, reverse=False, theme=theme)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if self._consume_pointer_for_top_task_panel(event, app, theme=theme):
            return True
        return self._dispatch_children(event, app, reverse=True, theme=theme)

    def on_event_bubble(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if self._consume_pointer_for_top_task_panel(event, app, theme=theme):
            return True
        return self._dispatch_children(event, app, reverse=True, theme=theme)

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        self.draw_screen_phase(surface, theme)
        self.draw_window_phase(surface, theme)

    def draw_screen_phase(self, surface: "pygame.Surface", theme: "ColorTheme", app: "GuiApplication | None" = None) -> None:
        """Draw panel background and non-window children (screen lifecycle layer).

        The focused control is drawn last so that any content it draws outside its
        assigned rect stays on top of other controls.
        """
        if self.draw_background:
            factory = theme.graphics_factory
            visual_size = (self.rect.width, self.rect.height)
            if self._visuals is None or self._visual_size != visual_size:
                self._visuals = factory.build_frame_visuals(self.rect)
                self._visual_size = visual_size
            selected = factory.resolve_visual_state(
                self._visuals,
                visible=self.visible,
                enabled=self.enabled,
                armed=False,
                hovered=False,
            )
            surface.blit(selected, self.rect)

        # Identify the focused child (if any) to draw it last
        focused_child = None
        if app is not None and hasattr(app, 'focus') and app.focus is not None:
            focused_node = app.focus.focused_node
            if focused_node is not None and focused_node in self.children and not self._is_window_like(focused_node):
                focused_child = focused_node

        # Draw non-focused, non-window children
        for child in self.children:
            if self._is_window_like(child):
                continue
            if child is focused_child:
                # Skip focused child for now; draw it last
                continue
            if child.visible:
                child.draw(surface, theme)

        # Draw the focused child last so its extra rendering stays on top
        if focused_child is not None and focused_child.visible:
            focused_child.draw(surface, theme)

    def draw_window_phase(self, surface: "pygame.Surface", theme: "ColorTheme", app: "GuiApplication | None" = None) -> None:
        """Draw window children (window lifecycle layer), optionally with per-window hints.

        Window draw order follows child z-order strictly so visual layering
        matches input hit-testing and window-management ordering.
        """
        def _is_actively_shear_dragging(window: UiNode) -> bool:
            if not self._is_window_like(window):
                return False
            controller = getattr(window, "shear_controller", None)
            return bool(getattr(controller, "dragging", False))

        def _is_transition_renderable(window: UiNode) -> bool:
            return bool(getattr(window, "is_visibility_transition_renderable", lambda: False)())

        def _should_draw_window(window: UiNode) -> bool:
            return bool(window.visible or _is_transition_renderable(window))

        def _has_higher_z_transition_window_than(window: UiNode) -> bool:
            seen = False
            for candidate in self.children:
                if candidate is window:
                    seen = True
                    continue
                if not seen:
                    continue
                if not self._is_window_like(candidate):
                    continue
                if _is_transition_renderable(candidate):
                    return True
            return False

        if app is not None:
            self._clear_occluded_window_hovers_for_pointer(getattr(app, "logical_pointer_pos", None))

        hint_window = None
        if app is not None and hasattr(app, "focus_visualizer"):
            resolve_hint_window = getattr(app.focus_visualizer, "focused_hint_window", None)
            if callable(resolve_hint_window):
                hint_window = resolve_hint_window()

        # Draw window children strictly in child z-order.
        for child in self.children:
            if not self._is_window_like(child):
                continue
            if not _should_draw_window(child):
                continue
            child.draw(surface, theme)
            if app is not None and child.visible:
                if hint_window is None or child is hint_window:
                    app.focus_visualizer.draw_hint_for_window(surface, theme, child)
