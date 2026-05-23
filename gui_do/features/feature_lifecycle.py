from __future__ import annotations
# ---------------------------------------------------------------------------
# Type checking imports for static analysis only
# ---------------------------------------------------------------------------
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence
from collections.abc import Mapping
from .font_role_setup import setup_standard_font_roles as setup_standard_font_roles
from .lifecycle_models import FrameTimer as FrameTimer, PlacedControl
from .lifecycle_layout_helpers import calculate_grid_layout as _calculate_grid_layout

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Deque
    from typing import Any, Optional, Dict, List

def calculate_grid_layout(anchor, cols, rows, gap, label_height, label_gap):
    """
    Return a list of (x, y, w, h) tuples for a grid layout anchored at (x, y).
    """
    return _calculate_grid_layout(anchor, cols, rows, gap, label_height, label_gap)

from ..controls.chrome.menu_bar_control import (
    ContextMenuItem,
    MenuEntry,
    MenuStripControl,
    SceneMenuOptions,
    WindowMenuOptions,
)
from ..app.error_handling import logical_error, report_nonfatal_error
from time import perf_counter
import inspect
from ..telemetry.telemetry import telemetry_collector
from collections import deque, OrderedDict
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ControlPlacementSpec:
    """Declarative placement metadata for a single control."""

    name: str
    control: object
    control_rect: object
    focusable: bool | None = None
    labeled: bool = True
    label_text: str = ""
    label_font_role: str = "body"
    control_font_role: str = "body"
    accessibility_role: str | None = None
    accessibility_label: str | None = None
    column_index: int = 0
    row_index: int = 0


from ..controls.display.label_control import LabelControl
def place_control(
    container,
    name: str,
    label_text: str,
    control,
    control_rect,
    *,
    label_font_role: str = "body",
    control_font_role: str = "body",
    focusable: bool | None = None,
    accessibility_role: str | None = None,
    accessibility_label: str | None = None,
    column_index: int = 0,
    row_index: int = 0,
    placed_controls: list = None,
    control_labels: list = None,
    focus_controls: list = None,
    controls: list = None,
):
    """
    Place a labeled control in a container, creating and positioning the label and control.
    Optionally tracks placed controls, labels, and focusable controls.
    """

    from pygame import Rect as _Rect
    label_rect = _Rect(control_rect.left, control_rect.top, control_rect.width, 18)
    control_top = control_rect.top + 18 + 4
    control_height = max(1, control_rect.height - 18 - 4)
    actual_control_rect = _Rect(control_rect.left, control_top, control_rect.width, control_height)
    label = None
    if label_text:
        label = LabelControl(f"label_{name}", label_rect, label_text, align="left")
        label.font_role = label_font_role
    register_placed_control(
        container,
        name,
        control,
        actual_control_rect,
        label,
        control_font_role=control_font_role,
        focusable=focusable,
        accessibility_role=accessibility_role,
        accessibility_label=accessibility_label,
        column_index=column_index,
        row_index=row_index,
        placed_controls=placed_controls,
        control_labels=control_labels,
        focus_controls=focus_controls,
        controls=controls,
    )


def place_control_specs(
    container,
    specs,
    *,
    placed_controls: list | None = None,
    control_labels: list | None = None,
    focus_controls: list | None = None,
    controls: list | None = None,
):
    """Place a sequence of ``ControlPlacementSpec`` entries."""

    for spec in specs:
        if bool(getattr(spec, "labeled", True)):
            place_control(
                container,
                str(spec.name),
                str(getattr(spec, "label_text", "")),
                spec.control,
                spec.control_rect,
                label_font_role=str(getattr(spec, "label_font_role", "body")),
                control_font_role=str(getattr(spec, "control_font_role", "body")),
                focusable=getattr(spec, "focusable", None),
                accessibility_role=getattr(spec, "accessibility_role", None),
                accessibility_label=getattr(spec, "accessibility_label", None),
                column_index=int(getattr(spec, "column_index", 0)),
                row_index=int(getattr(spec, "row_index", 0)),
                placed_controls=placed_controls,
                control_labels=control_labels,
                focus_controls=focus_controls,
                controls=controls,
            )
            continue
        place_control_unlabeled(
            container,
            str(spec.name),
            spec.control,
            spec.control_rect,
            control_font_role=str(getattr(spec, "control_font_role", "body")),
            focusable=getattr(spec, "focusable", None),
            accessibility_role=getattr(spec, "accessibility_role", None),
            accessibility_label=getattr(spec, "accessibility_label", None),
            column_index=int(getattr(spec, "column_index", 0)),
            row_index=int(getattr(spec, "row_index", 0)),
            placed_controls=placed_controls,
            control_labels=control_labels,
            focus_controls=focus_controls,
            controls=controls,
        )

def place_control_unlabeled(
    container,
    name: str,
    control,
    control_rect,
    *,
    control_font_role: str = "body",
    focusable: bool | None = None,
    accessibility_role: str | None = None,
    accessibility_label: str | None = None,
    column_index: int = 0,
    row_index: int = 0,
    placed_controls: list = None,
    control_labels: list = None,
    focus_controls: list = None,
    controls: list = None,
):
    """
    Place an unlabeled control in a container.
    Optionally tracks placed controls and focusable controls.
    """
    from pygame import Rect as _Rect
    register_placed_control(
        container,
        name,
        control,
        _Rect(control_rect),
        None,
        control_font_role=control_font_role,
        focusable=focusable,
        accessibility_role=accessibility_role,
        accessibility_label=accessibility_label,
        column_index=column_index,
        row_index=row_index,
        placed_controls=placed_controls,
        control_labels=control_labels,
        focus_controls=focus_controls,
        controls=controls,
    )

def register_placed_control(
    container,
    name: str,
    control,
    actual_control_rect,
    label,
    *,
    control_font_role: str = "body",
    focusable: bool | None = None,
    accessibility_role: str | None,
    accessibility_label: str | None,
    column_index: int = 0,
    row_index: int = 0,
    placed_controls: list = None,
    control_labels: list = None,
    focus_controls: list = None,
    controls: list = None,
):
    """
    Register a control (and optional label) in a container, set geometry, accessibility, and focus.
    Optionally tracks placed controls, labels, and focusable controls.
    """
    if label is not None:
        container.add(label)
        if control_labels is not None:
            control_labels.append(label)
    control.set_rect(actual_control_rect)
    control.enabled = True
    if hasattr(control, "font_role"):
        try:
            control.font_role = control_font_role
        except Exception:
            pass
    if accessibility_role is not None and accessibility_label is not None:
        control.set_accessibility(role=accessibility_role, label=accessibility_label)
    if focusable is None:
        inferred_focusable = False
        accepts_focus = getattr(control, "accepts_focus", None)
        if callable(accepts_focus):
            try:
                inferred_focusable = bool(accepts_focus())
            except Exception:
                inferred_focusable = False
        else:
            inferred_focusable = int(getattr(control, "tab_index", -1)) >= 0
        focusable = inferred_focusable
    if focusable:
        # Controls default to tab_index=-1; promote to default focusable index
        # unless the control already opted into a specific non-negative index.
        if int(getattr(control, "tab_index", -1)) < 0:
            control.set_tab_index(0)
        if focus_controls is not None:
            focus_controls.append(control)
    else:
        control.set_tab_index(-1)
    container.add(control)
    if controls is not None:
        controls.append(control)
    if placed_controls is not None:
        placed_controls.append(PlacedControl(
            control=control,
            label=label,
            name=name,
            column_index=column_index,
            row_index=row_index,
        ))

def apply_category_visibility(
    *,
    active_key: str,
    placed_controls: list,
    control_labels: list,
    category_fn,
) -> None:
    """Show controls whose category matches *active_key*, hide all others.

    Args:
        active_key: The category key that should be visible.
        placed_controls: Sequence of :class:`PlacedControl` records.  Each
            record's ``row_index`` is passed to *category_fn* to determine its
            category.
        control_labels: All label controls tracked by the registry.  Labels
            belonging to the active category are shown via the *placed_controls*
            loop; the remainder are explicitly hidden here.
        category_fn: Callable ``(row_index: int) -> str`` that maps a control's
            row index to its category key.
    """
    active_label_set: set = set()
    for placed in placed_controls:
        show = category_fn(int(placed.row_index)) == active_key
        placed.control.visible = show
        placed.control.enabled = show
        if placed.label is not None:
            placed.label.visible = show
            placed.label.enabled = show
            if show:
                active_label_set.add(placed.label)
    for label in control_labels:
        if label not in active_label_set:
            label.visible = False
            label.enabled = False


def make_labeled_slot_height_fn(label_height: int, label_gap: int):
    """Return a ``(control_height: int) -> int`` callable for labeled slot heights.

    Captures *label_height* and *label_gap* so callers avoid repeating those
    constants on every slot-height call::

        slot_h = make_labeled_slot_height_fn(LABEL_HEIGHT, LABEL_GAP)
        h = slot_h(34)
    """
    from .layout_geometry import labeled_slot_height

    lh = int(label_height)
    lg = int(label_gap)
    return lambda h: labeled_slot_height(int(h), label_height=lh, label_gap=lg)


class ControlRegistry:
    """Accumulates control placement specs and tracking lists for a single container.

    Simplifies feature ``build()`` methods by managing the three standard
    tracking lists (``controls``, ``control_labels``, ``placed_controls``) and
    providing a single :meth:`register` call for :class:`ControlPlacementSpec`
    sequences::

        registry = ControlRegistry(host.root)
        registry.register(build_some_specs(...))
        registry.add_label(my_section_label)   # adds to container + tracks
        registry.add_control(my_tab_control)   # adds to container + tracks

        # Access tracking lists via properties:
        prewarm_targets = [*registry.control_labels, *registry.controls]
    """

    def __init__(self, container) -> None:
        self._container = container
        self._controls: list = []
        self._control_labels: list = []
        self._placed_controls: list = []

    @property
    def controls(self) -> list:
        """All tracked controls (placed via register or add_control)."""
        return self._controls

    @property
    def control_labels(self) -> list:
        """All tracked label controls (placed via register or add_label)."""
        return self._control_labels

    @property
    def placed_controls(self) -> list:
        """All :class:`PlacedControl` records created by :meth:`register`."""
        return self._placed_controls

    def register(self, specs) -> None:
        """Place a sequence of :class:`ControlPlacementSpec` entries in the container."""
        place_control_specs(
            self._container,
            specs,
            placed_controls=self._placed_controls,
            control_labels=self._control_labels,
            controls=self._controls,
        )

    def add_label(self, label) -> None:
        """Add *label* to the container and track it in ``control_labels``."""
        self._container.add(label)
        self._control_labels.append(label)

    def add_control(self, control) -> None:
        """Add *control* to the container and track it in ``controls``."""
        self._container.add(control)
        self._controls.append(control)


def add_group_label(container, name: str, text: str, group_rect, *, label_font_role: str = "body", control_labels: list = None):
    """
    Add a group label to a container and optionally track it.
    """
    from pygame import Rect as _Rect
    label = LabelControl(
        f"group_label_{name}",
        _Rect(group_rect.left, group_rect.top, group_rect.width, 18),
        text,
        align="left",
    )
    label.font_role = label_font_role
    container.add(label)
    if control_labels is not None:
        control_labels.append(label)

class WindowRelativeRect:
    """A rect that resolves to absolute screen coordinates relative to a live window.

    Controls that are children of a ``WindowControl`` are positioned at
    absolute screen coordinates at build time.  When the window is later moved
    (e.g. by ``tile_windows``), any stored absolute rect becomes stale.

    ``WindowRelativeRect`` records the *offset* from the window's origin at
    registration time and recomputes the absolute rect on demand from the
    window's *current* position.  This prevents child controls from appearing
    at wrong positions after the window moves.

    Usage::

        # At build time (window position may change later):
        area = WindowRelativeRect(window, Rect(x, y, w, h))

        # Later (e.g. in _flow_apply_layout), always up-to-date:
        current_abs = area.resolve()

    The *window* argument must have a ``.rect`` attribute (``UiNode`` /
    ``WindowControl``).
    """

    def __init__(self, window, rect) -> None:
        """
        Parameters
        ----------
        window:
            The ``WindowControl`` (or any node with a ``.rect``) that *rect* is
            a child of.
        rect:
            The absolute rect at the moment of registration.  The relative
            offset is computed from ``window.rect`` immediately.
        """
        self._window = window
        wr = window.rect
        self._rel_x: int = rect.x - wr.x
        self._rel_y: int = rect.y - wr.y
        self._w: int = rect.width
        self._h: int = rect.height

    def resolve(self):
        """Return a ``pygame.Rect`` in current absolute screen coordinates."""
        from pygame import Rect as _Rect
        wr = self._window.rect
        return _Rect(wr.x + self._rel_x, wr.y + self._rel_y, self._w, self._h)

    @property
    def width(self) -> int:
        return self._w

    @property
    def height(self) -> int:
        return self._h

    @property
    def rel_x(self) -> int:
        return self._rel_x

    @property
    def rel_y(self) -> int:
        return self._rel_y


# ---------------------------------------------------------------------------
# TabPanelManager
# ---------------------------------------------------------------------------

class TabPanelManager:
    """Manages the mapping of tab keys to lists of child controls for a
    ``TabControl``.

    Calling :meth:`activate` hides all controls except those belonging to the
    specified tab, eliminating the hand-written ``_on_tab_change`` loop that
    every tabbed feature duplicates.

    Optional per-tab callbacks can be registered via :meth:`on_activate` to
    run arbitrary feature logic when a tab becomes visible.

    Usage::

        class MyFeature(Feature):
            def __init__(self):
                self._tabs = TabPanelManager()

            def build(self, host):
                self._tabs.register("cursor", self._build_cursor_tab(host, rect))
                self._tabs.register("filter", self._build_filter_tab(host, rect))
                self._tabs.on_activate("locale", lambda: setattr(self, "_dirty", True))
                self._tabs.activate("cursor")

            # Wire to TabControl on_change:
            tab_ctrl = TabControl(..., on_change=self._tabs.activate)
    """

    def __init__(self) -> None:
        self._panels: Dict[str, List] = {}
        self._callbacks: Dict[str, List[Callable[[], None]]] = {}
        self._active: Optional[str] = None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, key: str, controls) -> None:
        """Register a list (or single control) of controls for *key*.

        Controls are hidden immediately upon registration (they will be shown
        when :meth:`activate` is called for their key).
        """
        key = str(key)
        lst = list(controls) if not isinstance(controls, list) else controls
        self._panels[key] = lst
        should_be_visible = self._active == key if self._active is not None else False
        for ctrl in lst:
            ctrl.visible = should_be_visible

    def on_activate(self, key: str, callback: Callable[[], None]) -> None:
        """Register *callback* to be called when tab *key* is activated."""
        self._callbacks.setdefault(key, []).append(callback)

    # ------------------------------------------------------------------
    # Activation
    # ------------------------------------------------------------------

    def activate(self, key: str) -> None:
        """Show controls for *key*, hide controls for all other tabs, and fire
        any registered callbacks for *key*."""
        key = str(key)
        if key not in self._panels:
            # Preserve pre-registration selection semantics.
            if not self._panels:
                self._active = key
            return
        self._active = key
        parents_by_id = {}
        for tab_key, controls in self._panels.items():
            visible = tab_key == key
            for ctrl in controls:
                ctrl.visible = visible
                parent = getattr(ctrl, "parent", None)
                if parent is not None:
                    parents_by_id[id(parent)] = parent
        # Force redraw on the panel parent even when controls were already dirty.
        for parent in parents_by_id.values():
            tracker = getattr(parent, "_invalidation_tracker", None)
            if tracker is not None:
                tracker.invalidate_rect(parent.rect)
            elif hasattr(parent, "invalidate"):
                parent.invalidate()
        for cb in self._callbacks.get(key, []):
            cb()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    @property
    def active_key(self) -> Optional[str]:
        """The currently active tab key, or ``None`` if none activated yet."""
        return self._active

    def controls_for(self, key: str) -> List:
        """Return the control list registered for *key* (empty list if unknown)."""
        return list(self._panels.get(key, []))

    def append_to(self, key: str, control) -> None:
        """Append *control* to an existing panel and set its visibility to match
        the current active tab."""
        if key not in self._panels:
            self._panels[key] = []
        self._panels[key].append(control)
        control.visible = self._active == key

    def remove_from(self, key: str, control) -> None:
        """Remove *control* from panel *key* and hide it."""
        panel = self._panels.get(key)
        if panel is not None and control in panel:
            panel.remove(control)
        control.visible = False

    def keys(self):
        """Return the registered tab keys."""
        return list(self._panels.keys())


# ---------------------------------------------------------------------------
# Feature utility helpers
# ---------------------------------------------------------------------------

def resolve_scene_selection_callback(host) -> Callable[[str], None]:
    """Resolve scene-selection callback from host transitions, with app fallback."""
    scene_transitions = getattr(host, "scene_transitions", None)
    if scene_transitions is not None and hasattr(scene_transitions, "go"):
        return scene_transitions.go
    app = getattr(host, "app", None)
    if app is not None and hasattr(app, "switch_scene"):
        return app.switch_scene
    return lambda _scene_name: None


def minimize_window_menu_entries(
    on_minimize: Callable[[], None],
    *,
    menu_label: str = "WIndow",
    item_label: str = "Minimize",
) -> list[MenuEntry]:
    """Return a standard minimize-only menu entry list for MenuStripControl."""
    return [
        MenuEntry(
            str(menu_label),
            [
                ContextMenuItem(str(item_label), action=on_minimize),
            ],
        )
    ]


def _default_window_effects() -> dict[str, bool]:
    return {
        "shear_enabled": True,
        "hide_show_enabled": False,
        "grow_shrink_enabled": False,
    }


@dataclass(frozen=True)
class WindowEffectsSpec:
    """Declarative per-window visual effects configuration."""

    shear_enabled: bool = True
    hide_show_enabled: bool = False
    grow_shrink_enabled: bool = False


def normalize_window_effects_spec(window_effects, *, operation: str) -> dict[str, bool]:
    defaults = _default_window_effects()
    if window_effects is None:
        raw = {}
    elif isinstance(window_effects, Mapping):
        raw = dict(window_effects)
    else:
        raw = {
            "shear_enabled": getattr(window_effects, "shear_enabled", None),
            "hide_show_enabled": getattr(window_effects, "hide_show_enabled", None),
            "grow_shrink_enabled": getattr(window_effects, "grow_shrink_enabled", None),
        }

    normalized = {
        "shear_enabled": defaults["shear_enabled"] if raw.get("shear_enabled") is None else bool(raw.get("shear_enabled")),
        "hide_show_enabled": defaults["hide_show_enabled"] if raw.get("hide_show_enabled") is None else bool(raw.get("hide_show_enabled")),
        "grow_shrink_enabled": defaults["grow_shrink_enabled"] if raw.get("grow_shrink_enabled") is None else bool(raw.get("grow_shrink_enabled")),
    }
    if normalized["hide_show_enabled"] and normalized["grow_shrink_enabled"]:
        raise logical_error(
            "window visibility transition must enable at most one of hide_show_enabled or grow_shrink_enabled",
            subsystem="gui.features",
            operation=str(operation),
            details={"window_effects": normalized},
            source_skip_frames=1,
        )
    return normalized


def set_window_visible_state(
    window,
    visible: bool,
    *,
    toggle=None,
    from_toggle: bool = False,
    tile_windows: Optional[Callable[[], None]] = None,
    host=None,
    host_setter_name: str = None,
    app=None,
    binding=None,
) -> None:
    """Apply canonical window/toggle visibility synchronization used by demo hosts. Calls host setter if provided."""
    is_visible = bool(visible)
    was_visible = bool(window is not None and getattr(window, "visible", False))
    becoming_visible = bool(window is not None and is_visible and not was_visible)
    if app is None and host is not None:
        app = getattr(host, "app", None)
    if tile_windows is None and app is not None:
        app_tile_windows = getattr(app, "tile_windows", None)
        if callable(app_tile_windows):
            tile_windows = app_tile_windows

    tile_windows_supports_immediate_windows = False
    if callable(tile_windows):
        try:
            params = inspect.signature(tile_windows).parameters.values()
            tile_windows_supports_immediate_windows = any(
                (p.kind == inspect.Parameter.VAR_KEYWORD) or (p.name == "immediate_windows")
                for p in params
            )
        except (TypeError, ValueError):
            tile_windows_supports_immediate_windows = False

    transition_show_immediate_window = False

    def _transition_tiling_kwargs() -> dict[str, tuple[object, ...]]:
        if transition_show_immediate_window and tile_windows_supports_immediate_windows and window is not None:
            return {"immediate_windows": (window,)}
        return {}

    tiling_enabled: bool | None = None
    if app is not None:
        is_window_tiling_enabled = getattr(app, "is_window_tiling_enabled", None)
        if callable(is_window_tiling_enabled):
            try:
                tiling_enabled = bool(is_window_tiling_enabled())
            except Exception:
                tiling_enabled = None

    def _center_single_window_without_tiling() -> bool:
        if app is None or window is None:
            return False

        window_tiling = getattr(app, "window_tiling", None)
        center_windows = getattr(window_tiling, "center_windows", None)
        if callable(center_windows):
            try:
                center_windows((window,))
                return True
            except Exception:
                return False

        surface = getattr(app, "surface", None)
        get_rect = getattr(surface, "get_rect", None)
        move_by = getattr(window, "move_by", None)
        if not callable(get_rect) or not callable(move_by):
            return False
        try:
            bounds = get_rect()
            current = getattr(window, "rect", None)
            if current is None:
                return False
            target_x = int(bounds.centerx - (int(current.width) // 2))
            target_y = int(bounds.centery - (int(current.height) // 2))
            dx = int(target_x - int(current.x))
            dy = int(target_y - int(current.y))
            if dx != 0 or dy != 0:
                move_by(dx, dy)
            return True
        except Exception:
            return False

    def _cancel_window_tiling_motion() -> None:
        if window is None:
            return
        setattr(window, "_window_tiling_animating", False)
        if app is None:
            return
        tweens = getattr(app, "tweens", None)
        cancel_for_tag = getattr(tweens, "cancel_all_for_tag", None)
        if not callable(cancel_for_tag):
            return
        try:
            cancel_for_tag(f"window_tiling:{id(window)}")
        except Exception:
            return

    window_effects = normalize_window_effects_spec(
        getattr(window, "window_effects", None),
        operation="set_window_visible_state",
    ) if window is not None else _default_window_effects()
    use_transition = bool(
        window is not None
        and (window_effects["hide_show_enabled"] or window_effects["grow_shrink_enabled"])
        and hasattr(window, "begin_visibility_transition")
    )
    transition_show_immediate_window = bool(use_transition and is_visible)
    if use_transition and hasattr(window, "ensure_visibility_transition_controller"):
        window.ensure_visibility_transition_controller()
    if becoming_visible and window is not None and app is not None:
        ensure_chrome_layout = getattr(window, "ensure_chrome_layout", None)
        theme = getattr(app, "theme", None)
        if callable(ensure_chrome_layout) and theme is not None:
            try:
                ensure_chrome_layout(theme)
            except Exception:
                pass
    if window is not None and is_visible != was_visible:
        _cancel_window_tiling_motion()
    if becoming_visible:
        raise_window_in_parent(window)
    if window is not None and is_visible:
        window.visible = True
    if not from_toggle and toggle is not None and hasattr(toggle, "pushed"):
        toggle.pushed = is_visible
    if tile_windows is not None:
        if is_visible and window is not None:
            if tiling_enabled is False:
                if from_toggle:
                    try:
                        if becoming_visible:
                            tile_windows(
                                newly_visible=(window,),
                                raised_windows=(window,),
                                as_visibility_event=True,
                                force=True,
                                **_transition_tiling_kwargs(),
                            )
                        else:
                            tile_windows(
                                newly_visible=(window,),
                                as_visibility_event=True,
                                force=True,
                                **_transition_tiling_kwargs(),
                            )
                    except TypeError:
                        try:
                            tile_windows(newly_visible=(window,), as_visibility_event=True)
                        except TypeError:
                            tile_windows()
                elif not _center_single_window_without_tiling():
                    try:
                        tile_windows(newly_visible=(window,), as_visibility_event=True)
                    except TypeError:
                        tile_windows()
            else:
                try:
                    if becoming_visible:
                        tile_windows(
                            newly_visible=(window,),
                            raised_windows=(window,),
                            as_visibility_event=True,
                            **_transition_tiling_kwargs(),
                        )
                    else:
                        tile_windows(
                            newly_visible=(window,),
                            as_visibility_event=True,
                            **_transition_tiling_kwargs(),
                        )
                except TypeError:
                    tile_windows()
        else:
            if window is not None:
                window.visible = False
            if tiling_enabled is not False:
                tile_windows()
    elif window is not None:
        window.visible = is_visible

    if use_transition:
        window.begin_visibility_transition(is_visible, app=app, binding=binding)
    elif window is not None:
        window.visible = is_visible
    # Call host setter if provided
    if host is not None and host_setter_name:
        setter = getattr(host, host_setter_name, None)
        if callable(setter):
            setter(is_visible)


def raise_window_in_parent(window) -> bool:
    if window is None:
        return False
    parent = getattr(window, "parent", None)
    raise_window = getattr(parent, "_raise_window", None)
    if not callable(raise_window):
        return False
    raise_window(window)
    return True


@dataclass(frozen=True)
class FeatureWindowBinding:
    """Declarative presentation metadata for a feature-owned demo window."""

    key: str
    feature_attribute_name: str
    toggle_attribute_name: str | None = None
    action_name: str | None = None
    action_label: str | None = None
    task_panel_toggle_button_id: str | None = None
    task_panel_label: str | None = None
    task_panel_style: str = "round"
    task_panel_slot_index: int | None = None
    accessibility_label: str | None = None
    window_effects: dict = field(default_factory=_default_window_effects)
    titlebar_controls: dict = field(default_factory=dict)
    startup_visible: bool = False


class FeatureWindowPresentationModel:
    """Resolve feature-owned windows and keep demo presentation state in sync."""

    def __init__(self, host, *, tile_windows: Optional[Callable[[], None]] = None) -> None:
        self.host = host
        self._tile_windows = tile_windows
        self._bindings: "OrderedDict[str, FeatureWindowBinding]" = OrderedDict()
        self._bindings_by_control_id: dict[str, str] = {}
        self._bindings_by_window_object: dict[object, str] = {}
        self._window_object_by_key: dict[str, object] = {}

    @staticmethod
    def _normalize_titlebar_controls(spec) -> dict:
        if spec is None:
            return {
                "include_window_lower_button": True,
                "include_window_hide_image_button": True,
                "menus_enabled": True,
            }
        if isinstance(spec, dict):
            raw = spec
        else:
            raw = {
                "include_window_lower_button": getattr(spec, "include_window_lower_button", None),
                "include_window_hide_image_button": getattr(spec, "include_window_hide_image_button", None),
                "menus_enabled": getattr(spec, "menus_enabled", None),
            }
        lower_value = raw.get("include_window_lower_button")
        hide_value = raw.get("include_window_hide_image_button")
        menus_enabled_value = raw.get("menus_enabled")
        return {
            "include_window_lower_button": True if lower_value is None else bool(lower_value),
            "include_window_hide_image_button": True if hide_value is None else bool(hide_value),
            "menus_enabled": True if menus_enabled_value is None else bool(menus_enabled_value),
        }

    @staticmethod
    def _window_binding_sort_key(binding: "FeatureWindowBinding") -> tuple[int, str]:
        slot_index = getattr(binding, "task_panel_slot_index", None)
        if slot_index is None:
            return (10_000, str(getattr(binding, "key", "")))
        return (int(slot_index), str(getattr(binding, "key", "")))

    def _resolve_scene_name(self, scene_name: str | None = None) -> str | None:
        if scene_name is not None:
            resolved = str(scene_name).strip()
            return resolved or None
        app = getattr(self.host, "app", None)
        active_scene_name = str(getattr(app, "active_scene_name", "") or "").strip()
        return active_scene_name or None

    def _binding_scene_name(self, binding: "FeatureWindowBinding") -> str | None:
        feature = getattr(self.host, binding.feature_attribute_name, None)
        if feature is None:
            return None
        scene_name = str(getattr(feature, "scene_name", "") or "").strip()
        if scene_name:
            return scene_name
        window = getattr(feature, "window", None)
        if window is None:
            return None
        window_scene_name = str(getattr(window, "scene_name", "") or "").strip()
        return window_scene_name or None

    def ordered_bindings(self, *, scene_name: str | None = None) -> tuple[FeatureWindowBinding, ...]:
        """Return bindings in canonical order, optionally scoped to one scene."""
        target_scene = self._resolve_scene_name(scene_name)
        bindings = tuple(self._bindings.values())
        if target_scene is not None:
            filtered: list[FeatureWindowBinding] = []
            for binding in bindings:
                binding_scene = self._binding_scene_name(binding)
                if binding_scene is None or binding_scene == target_scene:
                    filtered.append(binding)
            bindings = tuple(filtered)
        with_slots = [b for b in bindings if getattr(b, "task_panel_slot_index", None) is not None]
        without_slots = [b for b in bindings if getattr(b, "task_panel_slot_index", None) is None]
        with_slots.sort(key=self._window_binding_sort_key)
        return tuple([*with_slots, *without_slots])

    def _scene_contains_window(self, scene_name: str, window: object) -> bool:
        app = getattr(self.host, "app", None)
        if app is None:
            return False

        target_scene = None
        if str(getattr(app, "active_scene_name", "") or "") == str(scene_name):
            target_scene = getattr(app, "scene", None)
        if target_scene is None:
            runtimes = getattr(app, "_scenes", None)
            if isinstance(runtimes, dict):
                runtime = runtimes.get(str(scene_name))
                if runtime is not None:
                    target_scene = getattr(runtime, "scene", None)
        if target_scene is None:
            return False

        walk_nodes = getattr(target_scene, "_walk_nodes", None)
        if not callable(walk_nodes):
            return False
        for node in walk_nodes():
            if node is window:
                return True
        return False

    def _window_matches_scene(self, window: object, scene_name: str | None) -> bool:
        if scene_name is None:
            return True
        window_scene = str(getattr(window, "scene_name", "") or "").strip()
        if window_scene:
            return window_scene == scene_name
        return self._scene_contains_window(scene_name, window)

    @staticmethod
    def _binding_menus_enabled(binding: "FeatureWindowBinding") -> bool:
        titlebar_controls = getattr(binding, "titlebar_controls", {})
        if not isinstance(titlebar_controls, dict):
            return True
        return bool(titlebar_controls.get("menus_enabled", True))

    def menu_windows(self, *, scene_name: str | None = None) -> tuple[tuple[FeatureWindowBinding, object], ...]:
        """Return canonical, menu-eligible (binding, window) pairs for shared window menus."""
        target_scene = self._resolve_scene_name(scene_name)
        ordered: list[tuple[FeatureWindowBinding, object]] = []
        for binding in self.ordered_bindings(scene_name=target_scene):
            if not self._binding_menus_enabled(binding):
                continue
            window = self.get_window(binding.key)
            if window is None:
                continue
            if not self._window_matches_scene(window, target_scene):
                continue
            ordered.append((binding, window))
        return tuple(ordered)

    def register_feature_window(
        self,
        key: str,
        *,
        feature_attribute_name: str,
        toggle_attribute_name: str | None = None,
        action_name: str | None = None,
        action_label: str | None = None,
        task_panel_toggle_button_id: str | None = None,
        task_panel_label: str | None = None,
        task_panel_style: str = "round",
        task_panel_slot_index: int | None = None,
        accessibility_label: str | None = None,
        window_effects: object | None = None,
        titlebar_controls: dict | None = None,
        startup_visible: bool = False,
    ) -> FeatureWindowBinding:
        binding = FeatureWindowBinding(
            key=str(key),
            feature_attribute_name=str(feature_attribute_name),
            toggle_attribute_name=None if toggle_attribute_name is None else str(toggle_attribute_name),
            action_name=None if action_name is None else str(action_name),
            action_label=None if action_label is None else str(action_label),
            task_panel_toggle_button_id=None if task_panel_toggle_button_id is None else str(task_panel_toggle_button_id),
            task_panel_label=None if task_panel_label is None else str(task_panel_label),
            task_panel_style=str(task_panel_style),
            task_panel_slot_index=None if task_panel_slot_index is None else int(task_panel_slot_index),
            accessibility_label=None if accessibility_label is None else str(accessibility_label),
            window_effects=normalize_window_effects_spec(
                window_effects,
                operation="FeatureWindowPresentationModel.register_feature_window",
            ),
            titlebar_controls=self._normalize_titlebar_controls(titlebar_controls),
            startup_visible=bool(startup_visible),
        )
        self._bindings[binding.key] = binding
        return binding

    def bindings(self) -> tuple[FeatureWindowBinding, ...]:
        return tuple(self._bindings.values())

    def get_binding(self, key: str) -> FeatureWindowBinding:
        return self._bindings[str(key)]

    def get_window(self, key: str):
        binding = self.get_binding(key)
        feature = getattr(self.host, binding.feature_attribute_name, None)
        if feature is None:
            return None
        window = getattr(feature, "window", None)
        if window is None:
            return None
        # Keep per-window effects synchronized from declarative binding metadata.
        try:
            window.window_effects = normalize_window_effects_spec(
                binding.window_effects,
                operation="FeatureWindowPresentationModel.get_window",
            )
        except Exception:
            pass
        try:
            set_titlebar_controls = getattr(window, "set_titlebar_controls", None)
            if callable(set_titlebar_controls):
                set_titlebar_controls(dict(binding.titlebar_controls))
            else:
                window.titlebar_controls = dict(binding.titlebar_controls)
        except Exception:
            pass
        previous_window = self._window_object_by_key.get(binding.key)
        if previous_window is not None and previous_window is not window:
            self._bindings_by_window_object.pop(previous_window, None)
        control_id = getattr(window, "control_id", None)
        if control_id:
            self._bindings_by_control_id[str(control_id)] = binding.key
        self._bindings_by_window_object[window] = binding.key
        self._window_object_by_key[binding.key] = window
        return window

    def get_toggle(self, key: str):
        binding = self.get_binding(key)
        if binding.toggle_attribute_name is None:
            return None
        return getattr(self.host, binding.toggle_attribute_name, None)

    def set_visible(self, key: str, visible: bool, *, from_toggle: bool = False) -> None:
        binding = self.get_binding(key)
        set_window_visible_state(
            self.get_window(key),
            visible,
            toggle=self.get_toggle(key),
            from_toggle=from_toggle,
            tile_windows=self._tile_windows,
            host=self.host,
            app=getattr(self.host, "app", None),
            binding=binding,
        )

    def show(self, key: str) -> None:
        window = self.get_window(key)
        if window is not None and getattr(window, "visible", False):
            raise_window_in_parent(window)
            return
        self.set_visible(key, True)

    def toggle(self, key: str, *, from_toggle: bool = False) -> bool:
        window = self.get_window(key)
        next_visible = not bool(window is not None and getattr(window, "visible", False))
        self.set_visible(key, next_visible, from_toggle=from_toggle)
        return next_visible

    def sync_initial_visibility(self, *, visible: bool | None = None) -> None:
        for key in self._bindings:
            binding = self.get_binding(key)
            self.set_visible(key, binding.startup_visible if visible is None else bool(visible))

    def toggle_window(self, window) -> bool:
        """Toggle a window by object reference, routing through the presentation model.

        Looks up the registered key for *window* by control_id so that the task
        panel toggle button and tile_windows are updated in sync.  Returns
        ``True`` if the window was found and toggled, ``False`` otherwise.
        """
        if window is None:
            return False
        key = self._bindings_by_window_object.get(window)
        if key is None:
            control_id = str(getattr(window, "control_id", "")).strip()
            key = self._bindings_by_control_id.get(control_id)
        if key is None:
            for candidate_key in self._bindings:
                w = self.get_window(candidate_key)
                if w is window:
                    key = candidate_key
                    break
        if key is None:
            return False
        self.toggle(key)
        return True

    def handle_window_toggle(self, window, next_visible: bool) -> bool:
        if window is None:
            return False
        key = self._bindings_by_window_object.get(window)
        if key is None:
            control_id = str(getattr(window, "control_id", "")).strip()
            key = self._bindings_by_control_id.get(control_id)
        if key is None:
            for candidate_key in self._bindings:
                candidate_window = self.get_window(candidate_key)
                if candidate_window is window:
                    key = candidate_key
                    break
        if key is None:
            return False
        self.set_visible(key, bool(next_visible))
        return True

    def action_callbacks(self) -> dict[str, Callable[[], None]]:
        callbacks: dict[str, Callable[[], None]] = {}
        for binding in self._bindings.values():
            if not binding.action_name:
                continue
            callbacks[binding.action_name] = lambda _key=binding.key: self.toggle(_key)
        return callbacks

    def declare_actions(self, action_registry, *, category: str = "Windows") -> None:
        if action_registry is None:
            return
        for binding in self._bindings.values():
            if not binding.action_name or not binding.action_label:
                continue
            action_registry.declare(
                binding.action_name,
                binding.action_label,
                lambda _ctx, _ev, _key=binding.key: (self.show(_key) or True),
                category=category,
            )


class ScenePresentationModel:
    """Own scene roots and per-scene task panel provisioning for demo hosts."""

    def __init__(self, host) -> None:
        self.host = host
        self._roots: "OrderedDict[str, object]" = OrderedDict()
        self._task_panels: "OrderedDict[str, object]" = OrderedDict()

    def ensure_scene_root(
        self,
        scene_name: str,
        *,
        control_id: str,
        draw_background: bool = False,
    ):
        key = str(scene_name)
        root = self._roots.get(key)
        if root is not None:
            return root
        from pygame import Rect
        from ..controls.composite.panel_control import PanelControl

        screen_rect = getattr(self.host, "screen_rect", None)
        if screen_rect is None:
            screen = getattr(self.host, "screen", None)
            if screen is not None:
                screen_rect = screen.get_rect()
        if screen_rect is None:
            screen_rect = self.host.app.screen.get_rect()

        root = self.host.app.add(
            PanelControl(
                str(control_id),
                Rect(0, 0, int(screen_rect.width), int(screen_rect.height)),
                draw_background=bool(draw_background),
            ),
            scene_name=key,
        )
        self._roots[key] = root
        return root

    def get_scene_root(self, scene_name: str):
        return self._roots.get(str(scene_name))

    def register_scene_root(self, scene_name: str, root) -> None:
        self._roots[str(scene_name)] = root

    def ensure_scene_task_panel(
        self,
        scene_name: str,
        *,
        control_id: str,
        height: int = 50,
        hidden_peek_pixels: int = 6,
        animation_step_px: int = 8,
        dock_bottom: bool = True,
        auto_hide: bool = True,
    ):
        key = str(scene_name)
        panel = self._task_panels.get(key)
        if panel is not None:
            return panel
        from pygame import Rect
        from ..controls.chrome.task_panel_control import TaskPanelControl

        screen_rect = getattr(self.host, "screen_rect", None)
        if screen_rect is None:
            screen = getattr(self.host, "screen", None)
            if screen is not None:
                screen_rect = screen.get_rect()
        if screen_rect is None:
            screen_rect = self.host.app.screen.get_rect()

        panel = self.host.app.add(
            TaskPanelControl(
                str(control_id),
                Rect(
                    0,
                    int(screen_rect.height) - int(height),
                    int(screen_rect.width),
                    int(height),
                ),
                auto_hide=bool(auto_hide),
                hidden_peek_pixels=int(hidden_peek_pixels),
                animation_step_px=int(animation_step_px),
                dock_bottom=bool(dock_bottom),
            ),
            scene_name=key,
        )
        self._task_panels[key] = panel
        return panel

    def register_scene_task_panel(self, scene_name: str, panel) -> None:
        self._task_panels[str(scene_name)] = panel

    def get_scene_task_panel(self, scene_name: str):
        return self._task_panels.get(str(scene_name))


@dataclass(frozen=True)
class SceneSetupSpec:
    """Declarative scene bootstrap settings for demo or app hosts."""

    name: str
    pretty_name: str | None = None
    transition_style: object | None = None
    transition_duration: float | None = None
    tiling_enabled: bool = True
    tiling_gap: int | None = 16
    tiling_padding: int | None = 16
    tiling_avoid_task_panel: bool | None = True
    tiling_center_on_failure: bool | None = True
    tiling_relayout: bool = False
    make_initial: bool = False


def apply_scene_setup_specs(app, scene_specs, *, scene_transitions=None):
    """Create scenes from specs and apply transition/tiling defaults in one pass."""
    initial_scene_name: str | None = None
    ordered_specs = list(scene_specs)

    for spec in ordered_specs:
        app.create_scene(str(spec.name), pretty_name=spec.pretty_name)

        app.configure_window_tiling(
            gap=spec.tiling_gap,
            padding=spec.tiling_padding,
            avoid_task_panel=spec.tiling_avoid_task_panel,
            center_on_failure=spec.tiling_center_on_failure,
            relayout=bool(spec.tiling_relayout),
            scene_name=str(spec.name),
        )
        app.set_window_tiling_enabled(
            bool(spec.tiling_enabled),
            relayout=bool(spec.tiling_relayout),
            scene_name=str(spec.name),
        )

        if scene_transitions is not None and spec.transition_style is not None:
            scene_transitions.set_style(
                str(spec.name),
                spec.transition_style,
                duration=spec.transition_duration,
            )

        if spec.make_initial:
            initial_scene_name = str(spec.name)

    if initial_scene_name is None and ordered_specs:
        initial_scene_name = str(ordered_specs[0].name)
    if initial_scene_name is not None:
        app.switch_scene(initial_scene_name)
    return initial_scene_name


def toggle_window_visibility(
    window,
    *,
    host=None,
    host_setter_name: Optional[str] = None,
    host_toggle_attr_name: Optional[str] = None,
) -> bool:
    """Toggle a window and sync host toggles using either host setter or toggle attr."""
    next_visible = not bool(window is not None and window.visible)
    if window is not None:
        window.visible = next_visible

    if host is None:
        return next_visible

    if host_setter_name:
        setter = getattr(host, host_setter_name, None)
        if callable(setter):
            setter(next_visible)
            return next_visible

    if host_toggle_attr_name:
        toggle = getattr(host, host_toggle_attr_name, None)
        if toggle is not None and hasattr(toggle, "pushed"):
            toggle.pushed = next_visible

    return next_visible


def create_anchored_feature_window(
    host,
    *,
    window_control_cls,
    control_id: str,
    title: str,
    size: tuple[int, int],
    anchor: str,
    margin: tuple[int, int],
    title_font_role: Optional[str] = None,
    use_frame_backdrop: bool = True,
    titlebar_controls: dict | object | None = None,
):
    """Create and attach a window anchored by layout.anchored to the host root."""
    # Only pass size to WindowControl; position is managed by tiler/layout, not constructor.
    kwargs: Dict[str, Any] = {
        "use_frame_backdrop": bool(use_frame_backdrop),
    }
    if title_font_role is not None:
        resolved_title_role = str(title_font_role).strip()
        if resolved_title_role:
            kwargs["title_font_role"] = resolved_title_role
    if titlebar_controls is not None:
        kwargs["titlebar_controls"] = FeatureWindowPresentationModel._normalize_titlebar_controls(titlebar_controls)
    window = window_control_cls(
        str(control_id),
        size,
        str(title),
        **kwargs,
    )
    return host.root.add(window)


def add_window_menu_strip(
    window,
    host,
    *,
    control_id: str,
    scene_name: str,
    on_minimize: Callable[[], None],
    scenes_shown: bool = False,
    windows_shown: bool = False,
    scene_menu_label: str = "Scene",
    window_menu_label: str = "Window",
    scene_menu_insert_index: int = 0,
    window_menu_insert_index: int = 1,
    scene_menu_mode: str = "add_all",
    scene_menu_opt_in_scene_names: Sequence[str] = (),
    scene_menu_include_current_scene: bool = False,
    scene_items_provider=None,
    window_items_provider=None,
    static_entries: Sequence[MenuEntry] = (),
):
    """Attach a MenuStripControl to a window using standard scene fallback wiring."""
    entries = list(static_entries) if static_entries else minimize_window_menu_entries(on_minimize)
    # Window presentation is optional; when available, enables window opt-in filtering
    window_presentation = getattr(host, "window_presentation", None)
    return window.add(
        MenuStripControl(
            str(control_id),
            entries,
            app=host.app,
            scene_name=str(scene_name),
            scene_menu=SceneMenuOptions(
                label=str(scene_menu_label),
                insert_index=int(scene_menu_insert_index),
                mode=str(scene_menu_mode),
                opt_in_scene_names=tuple(scene_menu_opt_in_scene_names),
                include_current_scene=bool(scene_menu_include_current_scene),
                shown=bool(scenes_shown),
            ),
            window_menu=WindowMenuOptions(
                label=str(window_menu_label),
                insert_index=int(window_menu_insert_index),
                shown=bool(windows_shown),
            ),
            scene_items_provider=scene_items_provider,
            window_items_provider=window_items_provider,
            on_scene_selected=resolve_scene_selection_callback(host),
            window_presentation=window_presentation,
        )
    )

@dataclass(slots=True)
class FeatureMessage:
    """Structured message envelope used for inter-feature transport."""

    sender: str
    target: str
    payload: Dict[str, Any]

    @classmethod
    def from_payload(cls, sender: str, target: str, payload: Mapping[str, Any]) -> "FeatureMessage":
        return cls(sender=str(sender), target=str(target), payload=dict(payload))

    def __getitem__(self, key: str) -> Any:
        return self.payload[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default)

    @property
    def topic(self) -> Optional[str]:
        value = self.payload.get("topic")
        return value if isinstance(value, str) else None

    @property
    def command(self) -> Optional[str]:
        value = self.payload.get("command")
        return value if isinstance(value, str) else None

    @property
    def event(self) -> Optional[str]:
        value = self.payload.get("event")
        return value if isinstance(value, str) else None


class Feature:
    """Base unit for managed GUI lifecycle composition."""

    HOST_REQUIREMENTS: Dict[str, tuple[str, ...]] = {}

    def __init__(self, name: str, *, scene_name: Optional[str] = None) -> None:
        normalized = str(name).strip()
        if not normalized:
            raise logical_error(
                "feature name must be a non-empty string",
                subsystem="feature_lifecycle",
                operation="Feature.__init__",
                exc_type=ValueError,
                details={"name": name},
                source_skip_frames=1,
            )
        self.name = normalized
        if scene_name is None:
            self.scene_name = None
        else:
            normalized_scene_name = str(scene_name).strip()
            if not normalized_scene_name:
                raise logical_error(
                    "scene_name must be a non-empty string when provided",
                    subsystem="feature_lifecycle",
                    operation="Feature.__init__",
                    exc_type=ValueError,
                    details={"scene_name": scene_name},
                    source_skip_frames=1,
                )
            self.scene_name = normalized_scene_name
        self._feature_manager = None
        self._message_queue: Deque[FeatureMessage] = deque()
        self._font_roles: Dict[str, str] = {}
        self._runtime_subscriptions = []

    def _track_runtime_subscription(self, unsubscribe):
        if unsubscribe is None or not callable(unsubscribe):
            return unsubscribe
        runtime_scope = getattr(self, "runtime_scope", None)
        add_cleanup = getattr(runtime_scope, "add_cleanup", None)
        if callable(add_cleanup):
            add_cleanup(unsubscribe)
            return unsubscribe
        self._runtime_subscriptions.append(unsubscribe)
        return unsubscribe

    def _release_runtime_subscriptions(self) -> None:
        subscriptions = self._runtime_subscriptions
        if not subscriptions:
            return
        for unsubscribe in reversed(subscriptions):
            try:
                unsubscribe()
            except Exception:
                pass
        subscriptions.clear()

    def on_register(self, host) -> None:
        return None

    def on_unregister(self, host) -> None:
        return None

    def build(self, host) -> None:
        return None

    def bind_runtime(self, host) -> None:
        return None

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        return int(tab_index_start)

    def shutdown_runtime(self, host) -> None:
        return None

    def handle_event(self, host, event) -> bool:
        return False

    def on_update(self, host) -> None:
        return None

    def draw(self, host, surface, theme) -> None:
        return None

    def prewarm(self, host, surface, theme) -> None:
        return None

    def save_state(self) -> dict:
        """Return a JSON-serializable dict of persistent feature state.

        Override to capture state that should survive across sessions.
        The default implementation returns an empty dict.
        """
        return {}

    def restore_state(self, state: dict) -> None:
        """Apply previously saved state produced by :meth:`save_state`.

        Called by :meth:`FeatureManager.restore_feature_states` after
        :meth:`build` completes.  Override to apply persisted values.
        """

    def send_message(self, target_feature_name: str, message: Mapping[str, Any]) -> bool:
        if self._feature_manager is None:
            raise logical_error(
                "feature must be registered before sending messages",
                subsystem="feature_lifecycle",
                operation="Feature.send_message",
                exc_type=RuntimeError,
                details={"feature_name": self.name, "target_feature_name": target_feature_name},
                source_skip_frames=1,
            )
        return self._feature_manager.send_message(self.name, target_feature_name, message)

    def bind_logic(self, logic_feature_name: str, *, alias: str = "default") -> None:
        if self._feature_manager is None:
            raise logical_error(
                "feature must be registered before binding logic features",
                subsystem="feature_lifecycle",
                operation="Feature.bind_logic",
                exc_type=RuntimeError,
                details={"feature_name": self.name, "logic_feature_name": logic_feature_name, "alias": alias},
                source_skip_frames=1,
            )
        self._feature_manager.bind_logic(self.name, logic_feature_name, alias=alias)

    def unbind_logic(self, *, alias: str = "default") -> bool:
        if self._feature_manager is None:
            raise logical_error(
                "feature must be registered before unbinding logic features",
                subsystem="feature_lifecycle",
                operation="Feature.unbind_logic",
                exc_type=RuntimeError,
                details={"feature_name": self.name, "alias": alias},
                source_skip_frames=1,
            )
        return self._feature_manager.unbind_logic(self.name, alias=alias)

    def bound_logic_name(self, *, alias: str = "default") -> Optional[str]:
        if self._feature_manager is None:
            raise logical_error(
                "feature must be registered before querying logic feature names",
                subsystem="feature_lifecycle",
                operation="Feature.bound_logic_name",
                exc_type=RuntimeError,
                details={"feature_name": self.name, "alias": alias},
                source_skip_frames=1,
            )
        return self._feature_manager.bound_logic_name(self.name, alias=alias)

    def send_logic_message(self, message: Mapping[str, Any], *, alias: str = "default") -> bool:
        if self._feature_manager is None:
            raise logical_error(
                "feature must be registered before sending logic messages",
                subsystem="feature_lifecycle",
                operation="Feature.send_logic_message",
                exc_type=RuntimeError,
                details={"feature_name": self.name, "alias": alias},
                source_skip_frames=1,
            )
        return self._feature_manager.send_logic_message(self.name, message, alias=alias)

    def enqueue_message(self, message: FeatureMessage) -> None:
        if not isinstance(message, FeatureMessage):
            raise logical_error(
                "feature messages must be FeatureMessage instances",
                subsystem="feature_lifecycle",
                operation="Feature.enqueue_message",
                exc_type=TypeError,
                details={"feature_name": self.name, "message_type": type(message).__name__},
                source_skip_frames=1,
            )
        self._message_queue.append(message)

    def has_messages(self) -> bool:
        return bool(self._message_queue)

    def message_count(self) -> int:
        return len(self._message_queue)

    def peek_message(self) -> Optional[FeatureMessage]:
        if not self._message_queue:
            return None
        return self._message_queue[0]

    def pop_message(self) -> Optional[FeatureMessage]:
        if not self._message_queue:
            return None
        return self._message_queue.popleft()

    def clear_messages(self) -> None:
        self._message_queue.clear()

    def _drain_messages(self, host, *, should_dispatch: Callable[[FeatureMessage], bool], dispatch: Callable[[object, FeatureMessage], None]) -> None:
        """Drain queued messages through a shared predicate/dispatch pipeline."""
        while self.has_messages():
            message = self.pop_message()
            if message is None:
                continue
            if not should_dispatch(message):
                continue
            dispatch(host, message)

    def register_font_role(
        self,
        host,
        role_name: str,
        *,
        size: int,
        file_path: Optional[str] = None,
        system_name: Optional[str] = None,
        bold: bool = False,
        italic: bool = False,
        scene_name: Optional[str] = None,
    ) -> str:
        """Register one namespaced font role owned by this feature."""
        local_name = self._normalize_font_role_name(role_name)
        app = self._resolve_app(host)
        qualified_name = f"feature.{self.name}.{local_name}"
        app.register_font_role(
            qualified_name,
            size=size,
            file_path=file_path,
            system_name=system_name,
            bold=bold,
            italic=italic,
            scene_name=scene_name,
        )
        self._font_roles[local_name] = qualified_name
        return qualified_name

    def register_font_roles(self, host, roles: Dict[str, Dict[str, Any]], *, scene_name: Optional[str] = None) -> Dict[str, str]:
        """Register multiple namespaced font roles owned by this feature."""
        registered: Dict[str, str] = {}
        for role_name, spec in dict(roles).items():
            if not isinstance(spec, dict):
                raise logical_error(
                    "font role definitions must be dictionaries",
                    subsystem="feature_lifecycle",
                    operation="Feature.register_font_roles",
                    exc_type=TypeError,
                    details={"feature_name": self.name, "role_name": role_name, "spec_type": type(spec).__name__},
                    source_skip_frames=1,
                )
            registered[role_name] = self.register_font_role(
                host,
                role_name,
                size=spec["size"],
                file_path=spec.get("file_path"),
                system_name=spec.get("system_name"),
                bold=bool(spec.get("bold", False)),
                italic=bool(spec.get("italic", False)),
                scene_name=scene_name,
            )
        return registered

    def use_font_roles(self, role_names: Mapping[str, str] | Iterable[str]) -> Dict[str, str]:
        """Bind local feature role names to already-registered global role names."""
        registered: Dict[str, str] = {}
        if isinstance(role_names, Mapping):
            items = role_names.items()
        else:
            items = ((name, name) for name in role_names)

        for local_name, global_name in items:
            normalized_local = self._normalize_font_role_name(local_name)
            normalized_global = self._normalize_font_role_name(global_name)
            self._font_roles[normalized_local] = normalized_global
            registered[normalized_local] = normalized_global
        return registered

    def font_role(self, role_name: str) -> str:
        """Resolve a local feature font role name to its registered global role."""
        local_name = self._normalize_font_role_name(role_name)
        qualified_name = self._font_roles.get(local_name)
        if qualified_name is None:
            raise logical_error(
                f"unknown feature font role: {self.name}.{local_name}",
                subsystem="feature_lifecycle",
                operation="Feature.font_role",
                exc_type=KeyError,
                details={"feature_name": self.name, "role_name": local_name},
                source_skip_frames=1,
            )
        return qualified_name

    @staticmethod
    def _normalize_font_role_name(role_name: str) -> str:
        normalized = str(role_name).strip()
        if not normalized:
            raise logical_error(
                "font role name must be a non-empty string",
                subsystem="feature_lifecycle",
                operation="Feature._normalize_font_role_name",
                exc_type=ValueError,
                details={"role_name": role_name},
                source_skip_frames=1,
            )
        return normalized

    @staticmethod
    def _resolve_app(host):
        app = getattr(host, "app", host)
        if not hasattr(app, "register_font_role"):
            raise logical_error(
                "host does not expose an application with register_font_role()",
                subsystem="feature_lifecycle",
                operation="Feature._resolve_app",
                exc_type=AttributeError,
                details={"host_type": type(host).__name__},
                source_skip_frames=1,
            )
        return app

    def host_requirements_for(self, hook_name: str) -> tuple[str, ...]:
        """Return required host field names for a lifecycle hook."""
        requirements = dict(self.HOST_REQUIREMENTS)
        required = requirements.get(str(hook_name), ())
        return tuple(str(name) for name in required)

    def validate_host_for(self, host, hook_name: str) -> None:
        """Validate required host fields for one lifecycle hook."""
        required_fields = self.host_requirements_for(hook_name)
        if not required_fields:
            return
        missing = [name for name in required_fields if not hasattr(host, name)]
        if not missing:
            return
        missing_csv = ", ".join(missing)
        raise logical_error(
            f"{self.__class__.__name__}.{hook_name} requires host fields: {missing_csv}",
            subsystem="feature_lifecycle",
            operation="Feature.validate_host_for",
            exc_type=AttributeError,
            details={"feature_class": self.__class__.__name__, "hook_name": hook_name, "missing_fields": tuple(missing)},
            source_skip_frames=1,
        )


class DirectFeature(Feature):
    """Feature subtype for direct screen event/update/draw integration.

    Bypasses the control pipeline entirely, receiving raw per-frame dt_seconds
    and drawing directly to the restored pristine surface — analogous to how
    DirectX bypasses the Windows GDI for direct hardware access.
    """

    def handle_direct_event(self, host, event) -> bool:
        return False

    def on_direct_update(self, host, dt_seconds: float) -> None:
        return None

    def draw_direct(self, host, surface, theme) -> None:
        return None


class LogicFeature(Feature):
    """Feature subtype for domain logic routed through message commands."""

    def on_logic_command(self, host, message: FeatureMessage) -> None:
        return None

    def on_update(self, host) -> None:
        self._drain_messages(
            host,
            should_dispatch=lambda message: message.command is not None,
            dispatch=self.on_logic_command,
        )


class RoutedFeature(Feature):
    """Feature subtype that routes queued messages by a canonical topic key."""

    def host_requirements_for(self, hook_name: str) -> tuple[str, ...]:
        """Extend base requirements: bind_runtime always requires 'app' for scheduler wiring."""
        explicit = super().host_requirements_for(hook_name)
        if hook_name == "bind_runtime" and "app" not in explicit:
            return ("app", *explicit)
        return explicit

    def message_handlers(self) -> Dict[str, Callable[[Any, FeatureMessage], None]]:
        """Return mapping of topic names to message handlers."""
        return {}

    def on_message(self, host, message: FeatureMessage) -> None:
        """Handle one routed message; unresolved topics are ignored by default."""
        handlers = self.message_handlers()
        topic = message.topic
        if topic is None:
            return
        handler = handlers.get(topic)
        if handler is None:
            return
        handler(host, message)

    def on_update(self, host) -> None:
        runtime_update = getattr(self, "_routed_runtime_on_update", None)
        if callable(runtime_update):
            runtime_update(host)
        self._drain_messages(
            host,
            should_dispatch=lambda message: message.topic is not None,
            dispatch=self.on_message,
        )


class FeatureManager:
    """Coordinates lifecycle, messaging, and utility registrations for features."""

    _LIFECYCLE_HOOKS = (
        "on_register",
        "on_unregister",
        "build",
        "bind_runtime",
        "configure_accessibility",
        "shutdown_runtime",
        "handle_event",
        "on_update",
        "draw",
        "handle_direct_event",
        "on_direct_update",
        "draw_direct",
        "on_logic_command",
        "on_message",
        "prewarm",
    )

    def __init__(self, app) -> None:
        self.app = app
        self._features: "OrderedDict[str, Feature]" = OrderedDict()
        self._feature_hosts: Dict[str, object] = {}
        self._runnables: Dict[str, Dict[str, Callable[..., Any]]] = {}
        self._runtime_bound: set[str] = set()
        self._logic_bindings: Dict[str, Dict[str, str]] = {}
        self._prewarmed: set[tuple[str, str]] = set()
        # Pre-partitioned list of DirectFeature instances to avoid per-frame isinstance checks.
        self._direct_features: List["DirectFeature"] = []
        self._scene_feature_entries: Dict[str, tuple[tuple[Feature, object], ...]] = {}
        self._scene_direct_feature_entries: Dict[str, tuple[tuple[DirectFeature, object], ...]] = {}

    def register(self, feature: Feature, host=None) -> Feature:
        if not isinstance(feature, Feature):
            raise logical_error(
                "register expects a Feature instance",
                subsystem="feature_lifecycle",
                operation="FeatureManager.register",
                exc_type=TypeError,
                details={"feature_type": type(feature).__name__},
                source_skip_frames=1,
            )
        if feature.name in self._features:
            raise logical_error(
                f"feature already registered: {feature.name}",
                subsystem="feature_lifecycle",
                operation="FeatureManager.register",
                exc_type=ValueError,
                details={"feature_name": feature.name},
                source_skip_frames=1,
            )
        self._validate_host_contract(feature)
        feature._feature_manager = self
        host_obj = self.app if host is None else host
        # Call on_register before inserting into _features so that any companion
        # features registered inside on_register appear before this feature in
        # iteration order (e.g. for correct message-passing in update_features).
        feature.on_register(host_obj)
        self._features[feature.name] = feature
        self._feature_hosts[feature.name] = host_obj
        if isinstance(feature, DirectFeature):
            self._direct_features.append(feature)
        self._runtime_bound.discard(feature.name)
        self._invalidate_scene_feature_views()
        return feature

    def unregister(self, name: str, host=None) -> bool:
        key = str(name)
        feature = self._features.get(key)
        if feature is None:
            return False
        host_obj = self._feature_hosts.get(feature.name)
        if host_obj is None:
            host_obj = self.app if host is None else host
        if feature.name in self._runtime_bound:
            feature.shutdown_runtime(host_obj)
        feature.on_unregister(host_obj)
        self._features.pop(key, None)
        self._feature_hosts.pop(feature.name, None)
        self._runtime_bound.discard(feature.name)
        self._logic_bindings.pop(feature.name, None)
        if isinstance(feature, DirectFeature):
            try:
                self._direct_features.remove(feature)
            except ValueError:
                pass
        for consumer_name, alias_map in tuple(self._logic_bindings.items()):
            aliases_to_remove = [alias for alias, provider_name in alias_map.items() if provider_name == feature.name]
            for alias in aliases_to_remove:
                alias_map.pop(alias, None)
            if not alias_map:
                self._logic_bindings.pop(consumer_name, None)
        feature._feature_manager = None
        self._runnables.pop(feature.name, None)
        self._invalidate_scene_feature_views()
        return True

    def get(self, name: str) -> Optional[Feature]:
        return self._features.get(str(name))

    def names(self) -> tuple[str, ...]:
        return tuple(self._features.keys())

    def features(self) -> Iterable[Feature]:
        return tuple(self._features.values())

    def send_message(self, sender_name: str, target_feature_name: str, message: Mapping[str, Any]) -> bool:
        collector = telemetry_collector()
        if not isinstance(message, Mapping):
            raise logical_error(
                "feature messages must be mappings",
                subsystem="feature_lifecycle",
                operation="FeatureManager.send_message",
                exc_type=TypeError,
                details={"sender_name": sender_name, "target_feature_name": target_feature_name, "message_type": type(message).__name__},
                source_skip_frames=1,
            )
        envelope = FeatureMessage.from_payload(str(sender_name), str(target_feature_name), message)
        topic = envelope.topic or ""
        target = self._features.get(str(target_feature_name))
        if target is None:
            collector.record_duration(
                "feature_lifecycle",
                "send_message_missing_target",
                0.0,
                metadata={"sender": str(sender_name), "target": str(target_feature_name), "topic": topic},
            )
            return False
        with collector.span(
            "feature_lifecycle",
            "send_message",
            metadata={"sender": str(sender_name), "target": target.name, "topic": topic},
        ):
            envelope.target = target.name
            target.enqueue_message(envelope)
            collector.record_duration(
                "feature_lifecycle",
                "target_queue_depth",
                0.0,
                metadata={"target": target.name, "queue_depth": target.message_count()},
            )
            return True

    def register_runnable(self, feature_name: str, runnable_name: str, runnable: Callable[..., Any]) -> None:
        self._require_feature(feature_name)
        if not callable(runnable):
            raise logical_error(
                "runnable must be callable",
                subsystem="feature_lifecycle",
                operation="FeatureManager.register_runnable",
                exc_type=TypeError,
                details={"feature_name": feature_name, "runnable_name": runnable_name, "runnable_type": type(runnable).__name__},
                source_skip_frames=1,
            )
        name = str(runnable_name).strip()
        if not name:
            raise logical_error(
                "runnable_name must be a non-empty string",
                subsystem="feature_lifecycle",
                operation="FeatureManager.register_runnable",
                exc_type=ValueError,
                details={"feature_name": feature_name, "runnable_name": runnable_name},
                source_skip_frames=1,
            )
        bucket = self._runnables.setdefault(str(feature_name), {})
        bucket[name] = runnable

    def bind_logic(self, consumer_feature_name: str, logic_feature_name: str, *, alias: str = "default") -> None:
        consumer = self._require_feature(consumer_feature_name)
        provider = self._require_feature(logic_feature_name)
        if not isinstance(provider, LogicFeature):
            raise logical_error(
                f"feature is not a LogicFeature: {provider.name}",
                subsystem="feature_lifecycle",
                operation="FeatureManager.bind_logic",
                exc_type=TypeError,
                details={"consumer": consumer.name, "provider": provider.name, "alias": alias},
                source_skip_frames=1,
            )
        alias_name = self._normalize_alias(alias)
        bucket = self._logic_bindings.setdefault(consumer.name, {})
        bucket[alias_name] = provider.name

    def unbind_logic(self, consumer_feature_name: str, *, alias: str = "default") -> bool:
        alias_name = self._normalize_alias(alias)
        bucket = self._logic_bindings.get(str(consumer_feature_name))
        if not bucket or alias_name not in bucket:
            return False
        bucket.pop(alias_name, None)
        if not bucket:
            self._logic_bindings.pop(str(consumer_feature_name), None)
        return True

    def bound_logic_name(self, consumer_feature_name: str, *, alias: str = "default") -> Optional[str]:
        alias_name = self._normalize_alias(alias)
        bucket = self._logic_bindings.get(str(consumer_feature_name), {})
        return bucket.get(alias_name)

    def send_logic_message(self, consumer_feature_name: str, message: Mapping[str, Any], *, alias: str = "default") -> bool:
        provider_name = self.bound_logic_name(consumer_feature_name, alias=alias)
        if provider_name is None:
            return False
        return self.send_message(str(consumer_feature_name), provider_name, message)

    def run(self, feature_name: str, runnable_name: str, *args, **kwargs) -> Any:
        feature_bucket = self._runnables.get(str(feature_name), {})
        runnable = feature_bucket.get(str(runnable_name))
        if runnable is None:
            raise logical_error(
                f"unknown runnable: {feature_name}.{runnable_name}",
                subsystem="feature_lifecycle",
                operation="FeatureManager.run",
                exc_type=KeyError,
                details={"feature_name": feature_name, "runnable_name": runnable_name},
                source_skip_frames=1,
            )
        return runnable(*args, **kwargs)

    def handle_event(self, event, host=None) -> bool:
        collector = telemetry_collector()
        for feature, host_obj in self._iter_scene_feature_entries(override_host=host):
            with collector.span("feature_lifecycle", "feature_handle_event", metadata={"feature_name": feature.name}):
                if feature.handle_event(host_obj, event):
                    return True
        return False

    def update_features(self, host=None) -> None:
        collector = telemetry_collector()
        for feature, host_obj in self._iter_scene_feature_entries(override_host=host):
            with collector.span("feature_lifecycle", "feature_update", metadata={"feature_name": feature.name}):
                feature.on_update(host_obj)

    def draw(self, surface, theme, host=None) -> None:
        collector = telemetry_collector()
        for feature, host_obj in self._iter_scene_feature_entries(override_host=host):
            with collector.span("feature_lifecycle", "feature_draw", metadata={"feature_name": feature.name}):
                feature.draw(host_obj, surface, theme)

    def handle_direct_event(self, event, host=None) -> bool:
        collector = telemetry_collector()
        for feature, host_obj in self._iter_scene_direct_feature_entries(override_host=host):
            with collector.span("feature_lifecycle", "direct_feature_handle_event", metadata={"feature_name": feature.name}):
                if feature.handle_direct_event(host_obj, event):
                    return True
        return False

    def update_direct_features(self, dt_seconds: float, host=None) -> None:
        collector = telemetry_collector()
        for feature, host_obj in self._iter_scene_direct_feature_entries(override_host=host):
            with collector.span("feature_lifecycle", "direct_feature_update", metadata={"feature_name": feature.name}):
                feature.on_direct_update(host_obj, dt_seconds)

    def draw_direct_features(self, surface, theme, host=None) -> None:
        collector = telemetry_collector()
        for feature, host_obj in self._iter_scene_direct_feature_entries(override_host=host):
            with collector.span("feature_lifecycle", "direct_feature_draw", metadata={"feature_name": feature.name}):
                feature.draw_direct(host_obj, surface, theme)

    def prewarm_features(self, host, surface, theme, *, scene_name: Optional[str] = None, force: bool = False) -> int:
        target_scene_name = str(self.app.active_scene_name if scene_name is None else scene_name)
        warmed = 0
        for feature in self._features.values():
            feature_scene = feature.scene_name
            if feature_scene is not None and feature_scene != target_scene_name:
                continue
            cache_key = (feature.name, target_scene_name)
            if cache_key in self._prewarmed and not force:
                continue
            host_obj = self._resolve_host(feature.name, host)
            feature.validate_host_for(host_obj, "prewarm")
            start = perf_counter()
            feature.prewarm(host_obj, surface, theme)
            elapsed_ms = (perf_counter() - start) * 1000.0
            self._record_prewarm_sample(target_scene_name, feature.name, elapsed_ms)
            self._prewarmed.add(cache_key)
            warmed += 1
        return warmed

    @staticmethod
    def _record_prewarm_sample(scene_name: str, feature_name: str, elapsed_ms: float) -> None:
        try:
            from ..app.first_frame_profiler import first_frame_profiler

            first_frame_profiler().record_once(
                "feature.prewarm",
                f"{scene_name}:{feature_name}",
                elapsed_ms,
                detail="feature prewarm hook",
            )
        except Exception as exc:
            report_nonfatal_error(
                "failed to record feature prewarm telemetry sample",
                kind="logical",
                subsystem="feature_lifecycle",
                operation="FeatureManager._record_prewarm_sample",
                cause=exc,
                details={"scene_name": scene_name, "feature_name": feature_name, "elapsed_ms": float(elapsed_ms)},
                source_skip_frames=1,
            )
            return

    def build_features(self, host) -> None:
        collector = telemetry_collector()
        for feature, _host_obj in self._iter_scene_feature_entries(scene_name=None, include_all=True):
            feature.validate_host_for(host, "build")
            with collector.span("feature_lifecycle", "feature_build", metadata={"feature_name": feature.name}):
                feature.build(host)

    def bind_runtime(self, host) -> None:
        collector = telemetry_collector()
        for feature, _host_obj in self._iter_scene_feature_entries(scene_name=None, include_all=True):
            feature.validate_host_for(host, "bind_runtime")
            with collector.span("feature_lifecycle", "feature_bind_runtime", metadata={"feature_name": feature.name}):
                feature.bind_runtime(host)
            self._runtime_bound.add(feature.name)

    def shutdown_runtime(self, host=None) -> None:
        """Call shutdown_runtime(host) for features with active runtime bindings."""
        collector = telemetry_collector()
        active_entries = self._iter_scene_feature_entries(scene_name=None, include_all=True, override_host=host)
        for feature, host_obj in reversed(active_entries):
            if feature.name not in self._runtime_bound:
                continue
            with collector.span("feature_lifecycle", "feature_shutdown_runtime", metadata={"feature_name": feature.name}):
                try:
                    feature.shutdown_runtime(host_obj)
                finally:
                    release_runtime_subscriptions = getattr(feature, "_release_runtime_subscriptions", None)
                    if callable(release_runtime_subscriptions):
                        release_runtime_subscriptions()
            self._runtime_bound.discard(feature.name)

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        collector = telemetry_collector()
        next_index = int(tab_index_start)
        for feature, _host_obj in self._iter_scene_feature_entries(scene_name=None, include_all=True):
            feature.validate_host_for(host, "configure_accessibility")
            with collector.span("feature_lifecycle", "feature_configure_accessibility", metadata={"feature_name": feature.name}):
                next_index = int(feature.configure_accessibility(host, next_index))
        return next_index

    def _invalidate_scene_feature_views(self) -> None:
        self._scene_feature_entries.clear()
        self._scene_direct_feature_entries.clear()

    def _build_scene_feature_entries(self, scene_name: str) -> tuple[tuple[Feature, object], ...]:
        entries = []
        for feature in self._features.values():
            if not self._is_feature_active_for_scene(feature, scene_name=scene_name):
                continue
            entries.append((feature, self._feature_hosts.get(feature.name, self.app)))
        return tuple(entries)

    def _build_scene_direct_feature_entries(self, scene_name: str) -> tuple[tuple[DirectFeature, object], ...]:
        entries = []
        for feature in self._direct_features:
            if not self._is_feature_active_for_scene(feature, scene_name=scene_name):
                continue
            entries.append((feature, self._feature_hosts.get(feature.name, self.app)))
        return tuple(entries)

    def _iter_scene_feature_entries(self, *, scene_name: Optional[str] = None, include_all: bool = False, override_host=None):
        if include_all:
            if override_host is None:
                return tuple((feature, self._feature_hosts.get(feature.name, self.app)) for feature in self._features.values())
            return tuple((feature, override_host) for feature in self._features.values())
        target_scene_name = self.app.active_scene_name if scene_name is None else str(scene_name)
        entries = self._scene_feature_entries.get(target_scene_name)
        if entries is None:
            entries = self._build_scene_feature_entries(target_scene_name)
            self._scene_feature_entries[target_scene_name] = entries
        if override_host is None:
            return entries
        return tuple((feature, override_host) for feature, _host_obj in entries)

    def _iter_scene_direct_feature_entries(self, *, scene_name: Optional[str] = None, include_all: bool = False, override_host=None):
        if include_all:
            if override_host is None:
                return tuple((feature, self._feature_hosts.get(feature.name, self.app)) for feature in self._direct_features)
            return tuple((feature, override_host) for feature in self._direct_features)
        target_scene_name = self.app.active_scene_name if scene_name is None else str(scene_name)
        entries = self._scene_direct_feature_entries.get(target_scene_name)
        if entries is None:
            entries = self._build_scene_direct_feature_entries(target_scene_name)
            self._scene_direct_feature_entries[target_scene_name] = entries
        if override_host is None:
            return entries
        return tuple((feature, override_host) for feature, _host_obj in entries)

    def _require_feature(self, feature_name: str) -> Feature:
        feature = self.get(feature_name)
        if feature is None:
            raise logical_error(
                f"unknown feature: {feature_name}",
                subsystem="feature_lifecycle",
                operation="FeatureManager._require_feature",
                exc_type=KeyError,
                details={"feature_name": feature_name},
                source_skip_frames=1,
            )
        return feature

    def _resolve_host(self, feature_name: str, override_host=None):
        if override_host is not None:
            return override_host
        return self._feature_hosts.get(feature_name, self.app)

    def _is_feature_active_for_scene(self, feature: Feature, *, scene_name: Optional[str] = None) -> bool:
        target_scene_name = self.app.active_scene_name if scene_name is None else scene_name
        feature_scene = feature.scene_name
        if feature_scene is None:
            return True
        return feature_scene == target_scene_name

    @classmethod
    def _validate_host_contract(cls, feature: Feature) -> None:
        for hook_name in cls._LIFECYCLE_HOOKS:
            method = getattr(feature, hook_name, None)
            if method is None or not callable(method):
                continue
            try:
                signature = inspect.signature(method)
            except (TypeError, ValueError):
                continue
            positional = [
                parameter
                for parameter in signature.parameters.values()
                if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            if not positional:
                continue
            host_parameter_name = positional[0].name
            if host_parameter_name in ("host", "_host"):
                continue
            raise logical_error(
                f"{feature.__class__.__name__}.{hook_name} first positional parameter must be 'host' or '_host', got {host_parameter_name!r}",
                subsystem="feature_lifecycle",
                operation="FeatureManager._validate_host_contract",
                exc_type=ValueError,
                details={"feature_class": feature.__class__.__name__, "hook_name": hook_name, "parameter_name": host_parameter_name},
                source_skip_frames=1,
            )

    @staticmethod
    def _normalize_alias(alias: str) -> str:
        alias_name = str(alias).strip()
        if not alias_name:
            raise logical_error(
                "logic binding alias must be a non-empty string",
                subsystem="feature_lifecycle",
                operation="FeatureManager._normalize_alias",
                exc_type=ValueError,
                details={"alias": alias},
                source_skip_frames=1,
            )
        return alias_name

    def save_feature_states(self) -> Dict[str, dict]:
        """Collect persistent state from every registered feature.

        Returns a ``{feature_name: state_dict}`` mapping suitable for
        JSON serialisation and later passing to :meth:`restore_feature_states`.
        Features that raise during :meth:`Feature.save_state` are skipped with
        an empty dict recorded under their name.
        """
        states: Dict[str, dict] = {}
        for feature in self._features.values():
            try:
                state = feature.save_state()
            except Exception:
                state = {}
            states[feature.name] = state if isinstance(state, dict) else {}
        return states

    def restore_feature_states(self, states: Dict[str, dict]) -> None:
        """Distribute saved states to registered features.

        *states* should be a ``{feature_name: state_dict}`` mapping as produced
        by :meth:`save_feature_states`.  Features with no entry in *states* are
        silently skipped.  Errors during :meth:`Feature.restore_state` are
        swallowed so that a corrupt state block cannot prevent other features
        from restoring.
        """
        if not isinstance(states, dict):
            return
        for name, state in states.items():
            feature = self._features.get(str(name))
            if feature is None or not isinstance(state, dict):
                continue
            try:
                feature.restore_state(state)
            except Exception:
                pass
