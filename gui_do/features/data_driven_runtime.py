"""Generalized data-driven runtime and feature wiring helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

import pygame
from pygame import Rect

from ..controls.chrome.menu_bar_control import MenuEntry
from ..controls.chrome.scene_menu_strip_control import SceneMenuStripControl
from ..controls.chrome.window_control import WindowControl
from ..controls.data.tab_control import TabControl, TabItem
from ..controls.input.button_control import ButtonControl
from ..controls.display.label_control import LabelControl
from ..controls.input.toggle_control import ToggleControl
from ..text.localization import LocaleRegistry
from .feature_lifecycle import (
    FeatureWindowPresentationModel,
    ScenePresentationModel,
    apply_scene_setup_specs,
    create_anchored_feature_window,
    register_standard_actions,
    resolve_scene_selection_callback,
    setup_standard_font_roles,
)


# ---------------------------------------------------------------------------
# Generalized spec dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeatureSpec:
    """Declarative descriptor for a host-registered feature object."""
    attr_name: str
    factory: Callable[[], object]


@dataclass(frozen=True)
class WindowSpec:
    """Declarative descriptor for a feature window presentation binding."""
    key: str
    feature_attr: str
    toggle_attr: str
    action_name: str
    action_label: str
    task_panel_button_id: str
    task_panel_label: str
    task_panel_style: str
    task_panel_slot_index: int
    tab_before_showcase: bool
    accessibility_label: str


@dataclass(frozen=True)
class RuntimeSceneSpec:
    """Declarative descriptor for a runtime scene's startup behaviour."""
    scene_name: str
    pristine_asset: str | None = None
    bind_escape_to_exit: bool = False
    prewarm: bool = False


@dataclass(frozen=True)
class ActionSpec:
    """Declarative descriptor for a host-level application action."""
    action_id: str
    label: str
    kind: str           # "exit" | "scene_nav" | "palette_open"
    target: str | None = None
    category: str | None = None


@dataclass(frozen=True)
class StaticAccessibilitySpec:
    """Declarative descriptor for a static accessibility annotation on a host control."""
    control_attr: str
    role: str
    label: str


@dataclass(frozen=True)
class CursorSpec:
    """Declarative descriptor for a registered application cursor."""
    name: str
    path: str
    hotspot: tuple[int, int]


@dataclass(frozen=True)
class SceneRootSpec:
    """Declarative descriptor for a scene root panel created at bootstrap."""
    scene_name: str
    control_id: str
    draw_background: bool = False


@dataclass(frozen=True)
class AnchoredWindowSpec:
    """Declarative descriptor for a presenter-backed anchored feature window."""
    control_id: str
    title: str
    size: tuple[int, int]
    anchor: str
    margin: tuple[int, int]
    use_frame_backdrop: bool = True


@dataclass(frozen=True)
class LogicBindingSpec:
    """Declarative descriptor mapping a routed-feature alias to a provider name."""
    alias: str
    provider_name: str


@dataclass(frozen=True)
class TaskPanelButtonSpec:
    """Declarative descriptor for a task-panel button owned by a host attribute."""
    attr_name: str
    control_id: str
    slot_index: int
    label: str
    on_click: Callable[[], object]
    style: str = "angle"


@dataclass(frozen=True)
class AccessibilitySequenceSpec:
    """Declarative descriptor for tab-order/accessibility applied from object attributes."""
    control_attr: str
    role: str
    label: str


@dataclass(frozen=True)
class TabBuilderSpec:
    """Declarative descriptor for tab key/label and feature builder binding."""
    key: str
    label: str
    builder_attr: str


class ActiveTabUpdateRouter:
    """Route per-frame update callbacks by active tab key."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., object]] = {}

    def register(self, tab_key: str, handler: Callable[..., object]) -> None:
        self._handlers[str(tab_key)] = handler

    def unregister(self, tab_key: str) -> bool:
        key = str(tab_key)
        if key in self._handlers:
            del self._handlers[key]
            return True
        return False

    def run(self, active_tab_key: str, *args, **kwargs) -> bool:
        handler = self._handlers.get(str(active_tab_key))
        if handler is None:
            return False
        handler(*args, **kwargs)
        return True

    def keys(self) -> tuple[str, ...]:
        return tuple(self._handlers.keys())


@dataclass
class TelemetryConfig:
    """Telemetry settings for the application."""
    enabled: bool = False
    live_analysis_enabled: bool = True
    file_logging_enabled: bool = False


@dataclass
class HostApplicationConfig:
    """Complete declarative configuration for bootstrapping a host application."""
    display_size: tuple[int, int]
    window_title: str
    fonts: dict
    font_role_specs: tuple[dict, ...]
    cursors: tuple[CursorSpec, ...]
    scene_specs: tuple
    feature_specs: tuple[FeatureSpec, ...]
    window_specs: tuple[WindowSpec, ...]
    runtime_scene_specs: tuple[RuntimeSceneSpec, ...]
    action_specs: tuple[ActionSpec, ...]
    static_accessibility_specs: tuple[StaticAccessibilitySpec, ...]
    initial_scene_name: str
    scene_roots: tuple[SceneRootSpec, ...] = field(default_factory=tuple)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    target_fps: int = 120


# ---------------------------------------------------------------------------
# Host application bootstrap
# ---------------------------------------------------------------------------

def bootstrap_host_application(host, config: HostApplicationConfig) -> None:
    """Bootstrap a host application from a declarative HostApplicationConfig.

    Sets the following attributes on *host* as side-effects:
    - screen, screen_rect, font_roles, app
    - scene_transitions
    - scene_presentation
    - One ``{scene_name}_root`` attribute per SceneRootSpec
    - One attribute per FeatureSpec.attr_name
    - window_presentation
    - action_registry, _palette_manager
    - ``go_to_{scene_name}`` navigation helpers for every configured scene
    """
    from ..app.display import create_display
    from ..app.gui_application import GuiApplication
    from ..actions.action_registry import ActionRegistry
    from ..overlays.command_palette_manager import CommandPaletteManager
    from ..theme.font_role_registry import FontRoleRegistry
    from ..persistence.scene_transition_manager import SceneTransitionManager, SceneTransitionStyle

    # 1 – Display
    host.screen = create_display(config.display_size)
    pygame.display.set_caption(config.window_title)
    host.screen_rect = host.screen.get_rect()

    # 2 – Font roles
    host.font_roles = FontRoleRegistry()
    setup_standard_font_roles(host.font_roles, config.fonts, *config.font_role_specs)

    # 3 – Application
    host.app = GuiApplication(host.screen, font_roles=host.font_roles)

    # 4 – Cursors
    default_cursor: str | None = None
    for cursor in config.cursors:
        host.app.register_cursor(cursor.name, cursor.path, cursor.hotspot)
        if default_cursor is None:
            default_cursor = cursor.name
    if default_cursor is not None:
        host.app.set_cursor(default_cursor)

    # 5 – Telemetry
    host.app.configure_telemetry(
        enabled=config.telemetry.enabled,
        live_analysis_enabled=config.telemetry.live_analysis_enabled,
        file_logging_enabled=config.telemetry.file_logging_enabled,
    )

    # 6 – Layout anchor bounds
    host.app.layout.set_anchor_bounds(host.screen_rect)

    # 7 – Scene transitions + scene setup
    host.scene_transitions = SceneTransitionManager(
        host.app,
        default_style=SceneTransitionStyle.FADE,
        default_duration=0.5,
    )
    apply_scene_setup_specs(host.app, config.scene_specs, scene_transitions=host.scene_transitions)

    # 8 – Navigation convenience helpers (go_to_{scene_name})
    for spec in config.scene_specs:
        sn = spec.name
        setattr(host, f"go_to_{sn}", lambda _sn=sn: host.scene_transitions.go(_sn))

    # 9 – Scene presentation model
    host.scene_presentation = ScenePresentationModel(host)

    # 10 – Declared scene roots
    for root_spec in config.scene_roots:
        root_attr = f"{root_spec.scene_name}_root"
        setattr(
            host,
            root_attr,
            host.scene_presentation.ensure_scene_root(
                root_spec.scene_name,
                control_id=root_spec.control_id,
                draw_background=root_spec.draw_background,
            ),
        )

    # 11 – Features, window presentation
    instantiate_features_from_specs(host, config.feature_specs)
    host.window_presentation = FeatureWindowPresentationModel(
        host,
        tile_windows=host.app.tile_windows,
    )
    register_window_presentation_specs(host.window_presentation, config.window_specs)
    register_features_from_specs(host.app, host, config.feature_specs)

    # 12 – Action registry + command palette
    host.action_registry = ActionRegistry()
    host._palette_manager = CommandPaletteManager(host.app.overlay, host.app)
    host._palette_manager.enable_builtin_scene_and_window_entries(
        host.app,
        on_scene_selected=host.scene_transitions.go,
    )
    _declare_host_actions(host, config.action_specs)

    # 13 – Build features, sync visibility, pristine assets, standard actions
    host.app.build_features(host)
    host.window_presentation.sync_initial_visibility(visible=False)
    apply_runtime_scene_pristine_assets(host.app, config.runtime_scene_specs)
    register_standard_actions(
        host.app.actions,
        app=host.app,
        scene_transitions=host.scene_transitions,
        palette_manager=host._palette_manager,
        window_toggles=host.window_presentation.action_callbacks(),
    )
    bind_runtime_scene_exit_keys(
        host.app.actions,
        config.runtime_scene_specs,
        key=pygame.K_ESCAPE,
        action_name="exit",
    )
    host.app.bind_features_runtime(host)
    prewarm_runtime_scenes(host.app, config.runtime_scene_specs)

    # 14 – Tab order + accessibility
    window_toggle_controls = collect_window_toggle_controls(host, host.window_presentation)
    base_controls = _build_host_main_tab_order(host, window_toggle_controls)
    _apply_host_main_accessibility(host, base_controls, config.static_accessibility_specs)
    host.app.configure_features_accessibility(host, len(base_controls))

    # 15 – Switch to initial scene
    host.app.switch_scene(config.initial_scene_name)


def declare_host_actions(host, action_specs) -> None:
    """Declare all standard actions on host.action_registry from declarative specs."""
    r = host.action_registry
    for spec in action_specs:
        handler = _build_standard_action_handler(host, spec)
        if spec.category is None:
            r.declare(spec.action_id, spec.label, handler)
        else:
            r.declare(spec.action_id, spec.label, handler, category=spec.category)
    host.window_presentation.declare_actions(r, category="Windows")


# Keep private alias for internal bootstrap use
_declare_host_actions = declare_host_actions


def _build_standard_action_handler(host, spec):
    """Return a callable action handler for a standard ActionSpec kind."""
    if spec.kind == "exit":
        return lambda _ctx, _ev: (setattr(host.app, "running", False) or True)
    if spec.kind == "scene_nav":
        target = str(spec.target)
        return lambda _ctx, _ev, _t=target: (host.scene_transitions.go(_t) or True)
    if spec.kind == "palette_open":
        return lambda _ctx, _ev: (host._palette_manager.show(host.app) or True)
    raise ValueError(f"Unsupported action kind: {spec.kind!r}")


def build_host_main_tab_order(host, window_toggle_controls) -> list:
    """Build and apply the main-scene tab order; return the ordered control list."""
    before_showcase = [c for b, c in window_toggle_controls if b.tab_before_showcase]
    after_showcase = [c for b, c in window_toggle_controls if not b.tab_before_showcase]
    base_controls = [host.exit_button]
    base_controls.extend(before_showcase)
    base_controls.append(host.showcase_button)
    base_controls.extend(after_showcase)
    for index, control in enumerate(base_controls):
        control.set_tab_index(index)
    return base_controls


# Keep private alias for internal bootstrap use
_build_host_main_tab_order = build_host_main_tab_order


def apply_host_main_accessibility(host, base_controls, static_accessibility_specs) -> None:
    """Apply static and dynamic accessibility metadata after build_features."""
    for spec in static_accessibility_specs:
        control = getattr(host, spec.control_attr, None)
        if control is None:
            continue
        control.set_accessibility(role=spec.role, label=spec.label)
    apply_window_toggle_accessibility(host, host.window_presentation, role="toggle")


# Keep private alias for internal bootstrap use
_apply_host_main_accessibility = apply_host_main_accessibility


def build_tools_menu_entries(host, *, exclude_labels: Iterable[str] = ()) -> list[MenuEntry]:
    """Build the optional Tools menu entry from the host action registry."""
    action_registry = getattr(host, "action_registry", None)
    if action_registry is None:
        return []
    excluded = {str(label) for label in exclude_labels}
    tools_items = [
        item
        for item in action_registry.context_menu_items(category="Tools")
        if item.label not in excluded
    ]
    if not tools_items:
        return []
    return [MenuEntry("Tools", tools_items)]


def add_standard_scene_menu_strip(
    container,
    host,
    *,
    control_id: str,
    rect,
    scene_name: str,
    scenes_shown: bool = True,
    windows_shown: bool = True,
    tools_exclude_labels: Sequence[str] = (),
    on_window_toggled=None,
):
    """Attach a standardized SceneMenuStripControl with optional Tools menu entries."""
    return container.add(
        SceneMenuStripControl(
            str(control_id),
            rect,
            host.app,
            scene_name=str(scene_name),
            scenes_shown=bool(scenes_shown),
            windows_shown=bool(windows_shown),
            extra_entries_provider=lambda: build_tools_menu_entries(
                host,
                exclude_labels=tools_exclude_labels,
            ),
            on_scene_selected=resolve_scene_selection_callback(host),
            on_window_toggled=on_window_toggled,
        )
    )


def apply_accessibility_sequence(items, tab_index_start: int) -> int:
    """Apply sequential tab order and accessibility metadata to controls."""
    next_index = int(tab_index_start)
    for control, role, label in items:
        if control is None:
            continue
        control.set_tab_index(next_index)
        control.set_accessibility(role=str(role), label=str(label))
        next_index += 1
    return next_index


def apply_accessibility_sequence_from_attrs(target, specs: Sequence[AccessibilitySequenceSpec], tab_index_start: int) -> int:
    """Apply sequential accessibility/tab-order metadata using target attribute names."""
    items = [
        (getattr(target, spec.control_attr, None), spec.role, spec.label)
        for spec in specs
    ]
    return apply_accessibility_sequence(items, tab_index_start)


def register_companion_logic_features(feature_manager, host, providers) -> None:
    """Register companion logic features for a routed/direct feature."""
    for provider in providers:
        feature_manager.register(provider, host)


def ensure_scene_scheduler(feature, host, *, scene_name: str = "main", attr_name: str = "scheduler"):
    """Return and cache a scene scheduler on the feature instance."""
    scheduler = getattr(feature, attr_name, None)
    if scheduler is None:
        scheduler = host.app.get_scene_scheduler(str(scene_name))
        setattr(feature, attr_name, scheduler)
    return scheduler


def sorted_window_bindings(bindings):
    """Return feature-window bindings sorted by declarative slot and key."""
    return tuple(
        sorted(
            tuple(bindings),
            key=lambda b: (
                10_000 if getattr(b, "task_panel_slot_index", None) is None else int(b.task_panel_slot_index),
                str(getattr(b, "key", "")),
            ),
        )
    )


def collect_window_toggle_controls(host, window_presentation):
    """Return sorted (binding, control) pairs for all available window toggles on host."""
    controls = []
    for binding in sorted_window_bindings(window_presentation.bindings()):
        toggle_attr = getattr(binding, "toggle_attr", None)
        if toggle_attr is None:
            continue
        control = getattr(host, str(toggle_attr), None)
        if control is not None:
            controls.append((binding, control))
    return controls


def apply_window_toggle_accessibility(host, window_presentation, *, role: str = "toggle") -> None:
    """Apply accessibility metadata for all window toggle controls declared by bindings."""
    for binding, control in collect_window_toggle_controls(host, window_presentation):
        control.set_accessibility(
            role=str(role),
            label=binding.accessibility_label or binding.action_label or binding.key,
        )


def add_window_toggle_task_panel_controls(host, task_panel, app_layout, window_presentation):
    """Create window toggle controls on the task panel from declarative bindings."""
    toggle_controls = []
    max_slot_index = 0
    for binding in sorted_window_bindings(window_presentation.bindings()):
        slot_index = 1 if binding.task_panel_slot_index is None else int(binding.task_panel_slot_index)
        max_slot_index = max(max_slot_index, slot_index)
        toggle = task_panel.add(
            ToggleControl(
                binding.task_panel_button_id or f"show_{binding.key}",
                app_layout.linear(slot_index),
                binding.task_panel_label or binding.key.title(),
                binding.task_panel_label or binding.key.title(),
                pushed=False,
                on_toggle=lambda pushed, _key=binding.key: window_presentation.set_visible(
                    _key,
                    bool(pushed),
                    from_toggle=True,
                ),
                style=binding.task_panel_style,
            )
        )
        if binding.toggle_attr:
            setattr(host, binding.toggle_attr, toggle)
        toggle_controls.append((binding, toggle))
    return toggle_controls, max_slot_index


def register_window_toggle_tooltips(tooltip_manager, toggle_controls) -> None:
    """Register standardized window toggle tooltip labels."""
    for binding, toggle in toggle_controls:
        label = binding.task_panel_label or binding.action_label or binding.key.title()
        tooltip_manager.register(toggle, f"Toggle the {label} window")


def initialize_locale_registry(tables, *, initial_locale: str) -> LocaleRegistry:
    """Create a LocaleRegistry, register all tables, and select the initial locale."""
    locale_registry = LocaleRegistry()
    for table in tables:
        locale_registry.register(table)
    locale_registry.set_locale(str(initial_locale))
    return locale_registry


def bind_input_map_actions(input_map, bindings, *, mod: int = 0) -> None:
    """Bind multiple (key, action) pairs on an InputMap using a shared modifier."""
    for key, action in bindings:
        input_map.bind(str(action), key=key, mod=int(mod))


def register_descriptors(registry, owner_class, descriptors) -> None:
    """Register a sequence of property descriptors for a given owner class."""
    for descriptor in descriptors:
        registry.register(owner_class, descriptor)


def resolve_canvas_local_point(packet, canvas_rect: Rect):
    """Resolve packet coordinates to canvas-local space, if available."""
    local_pos = getattr(packet, "local_pos", None)
    if local_pos is not None:
        return (float(local_pos[0]), float(local_pos[1]))
    pos = getattr(packet, "pos", None)
    if pos is None:
        return None
    return (float(pos[0] - canvas_rect.left), float(pos[1] - canvas_rect.top))


def apply_runtime_scene_pristine_assets(app, runtime_scene_specs) -> None:
    """Apply configured pristine assets to runtime scenes from declarative specs."""
    for spec in runtime_scene_specs:
        if not spec.pristine_asset:
            continue
        app.set_pristine(spec.pristine_asset, scene_name=spec.scene_name)


def bind_runtime_scene_exit_keys(actions, runtime_scene_specs, *, key, action_name: str = "exit") -> None:
    """Bind a shared exit action key for all runtime scenes that opt in."""
    for spec in runtime_scene_specs:
        if not spec.bind_escape_to_exit:
            continue
        actions.bind_key(key, str(action_name), scene=spec.scene_name)


def prewarm_runtime_scenes(app, runtime_scene_specs) -> None:
    """Prewarm runtime scenes that opt in via declarative scene specs."""
    for spec in runtime_scene_specs:
        if not spec.prewarm:
            continue
        app.prewarm_scene(spec.scene_name)


def add_task_panel_button(task_panel, app_layout, *, control_id: str, slot_index: int, label: str, on_click, style: str = "angle"):
    """Create and add a standard task-panel button positioned by linear slot index."""
    return task_panel.add(
        ButtonControl(
            str(control_id),
            app_layout.linear(int(slot_index)),
            str(label),
            on_click,
            style=str(style),
        )
    )


def add_task_panel_buttons(host, task_panel, app_layout, specs: Sequence[TaskPanelButtonSpec]):
    """Create and assign host-owned task-panel buttons from declarative specs."""
    for spec in specs:
        button = add_task_panel_button(
            task_panel,
            app_layout,
            control_id=spec.control_id,
            slot_index=spec.slot_index,
            label=spec.label,
            on_click=spec.on_click,
            style=spec.style,
        )
        setattr(host, spec.attr_name, button)


def register_tooltip_specs(tooltip_manager, specs) -> None:
    """Register a sequence of tooltip specs as (control, message) pairs."""
    for control, message in specs:
        tooltip_manager.register(control, str(message))


def add_window_control(window, controls: list, control):
    """Add a control to a window and append it to the caller's control list."""
    added = window.add(control)
    controls.append(added)
    return added


def add_window_label(window, controls: list, control_id: str, rect: Rect, text: str, *, align: str = "left"):
    """Create a label control, add it to a window, and track it in controls."""
    return add_window_control(
        window,
        controls,
        LabelControl(str(control_id), Rect(rect), str(text), align=str(align)),
    )


def add_window_button(window, controls: list, control_id: str, rect: Rect, text: str, on_click, *, style=None):
    """Create a button control, add it to a window, and track it in controls."""
    kwargs = {}
    if style is not None:
        kwargs["style"] = style
    return add_window_control(
        window,
        controls,
        ButtonControl(str(control_id), Rect(rect), str(text), on_click, **kwargs),
    )


def add_window_button_row(
    window,
    controls: list,
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    gap: int,
    specs,
):
    """Add a horizontal row of buttons from (id, label, callback[, style]) specs."""
    buttons = []
    left = int(x)
    for spec in specs:
        if len(spec) == 3:
            control_id, label, on_click = spec
            style = None
        elif len(spec) == 4:
            control_id, label, on_click, style = spec
        else:
            raise ValueError("Button row spec must have 3 or 4 values")
        button = add_window_button(
            window,
            controls,
            str(control_id),
            Rect(left, int(y), int(width), int(height)),
            str(label),
            on_click,
            style=style,
        )
        buttons.append(button)
        left += int(width) + int(gap)
    return tuple(buttons)


def make_window_toggle_spec(
    key: str,
    feature_attr: str,
    *,
    slot_index: int,
    task_panel_label: str | None = None,
    task_panel_style: str = "round",
    tab_before_showcase: bool = False,
    action_label: str | None = None,
    action_name: str | None = None,
    task_panel_button_id: str | None = None,
    toggle_attr: str | None = None,
    accessibility_label: str | None = None,
) -> WindowSpec:
    """Build a WindowSpec with conventional defaults for demo/host window toggles."""
    normalized_key = str(key)
    normalized_label = task_panel_label or normalized_key.replace("_", " ").title()
    return WindowSpec(
        key=normalized_key,
        feature_attr=str(feature_attr),
        toggle_attr=toggle_attr or f"{normalized_key}_toggle_window",
        action_name=action_name or f"win_{normalized_key}",
        action_label=action_label or f"Show {normalized_label} Window",
        task_panel_button_id=task_panel_button_id or f"show_{normalized_key}",
        task_panel_label=normalized_label,
        task_panel_style=str(task_panel_style),
        task_panel_slot_index=int(slot_index),
        tab_before_showcase=bool(tab_before_showcase),
        accessibility_label=accessibility_label or f"Show {normalized_label} window",
    )


def make_scene_nav_action(
    action_id: str,
    *,
    label: str,
    target_scene: str,
    category: str = "Scenes",
) -> ActionSpec:
    """Build a scene-navigation ActionSpec with consistent defaults."""
    return ActionSpec(
        action_id=str(action_id),
        label=str(label),
        kind="scene_nav",
        target=str(target_scene),
        category=str(category),
    )


def make_exit_action(
    action_id: str = "exit",
    *,
    label: str = "Exit",
    category: str = "File",
) -> ActionSpec:
    """Build a standard exit ActionSpec."""
    return ActionSpec(
        action_id=str(action_id),
        label=str(label),
        kind="exit",
        target=None,
        category=str(category),
    )


def make_palette_open_action(
    action_id: str = "palette_open",
    *,
    label: str = "Open Command Palette (F5)",
) -> ActionSpec:
    """Build a standard command-palette open ActionSpec."""
    return ActionSpec(
        action_id=str(action_id),
        label=str(label),
        kind="palette_open",
        target=None,
        category=None,
    )


def make_static_accessibility_spec(
    control_attr: str,
    *,
    label: str,
    role: str = "button",
) -> StaticAccessibilitySpec:
    """Build a StaticAccessibilitySpec with a role default suitable for buttons."""
    return StaticAccessibilitySpec(
        control_attr=str(control_attr),
        role=str(role),
        label=str(label),
    )


def instantiate_features_from_specs(host, feature_specs) -> None:
    """Instantiate feature objects from specs and attach them to host attributes."""
    for spec in feature_specs:
        setattr(host, spec.attr_name, spec.factory())


def register_features_from_specs(app, host, feature_specs) -> None:
    """Register instantiated host feature attributes to the application."""
    for spec in feature_specs:
        feature = getattr(host, spec.attr_name)
        app.register_feature(feature, host=host)


def register_window_presentation_specs(window_presentation, window_specs) -> None:
    """Register feature-window presentation bindings from declarative window specs."""
    for spec in window_specs:
        window_presentation.register_feature_window(
            spec.key,
            feature_attr=spec.feature_attr,
            toggle_attr=spec.toggle_attr,
            action_name=spec.action_name,
            action_label=spec.action_label,
            task_panel_button_id=spec.task_panel_button_id,
            task_panel_label=spec.task_panel_label,
            task_panel_style=spec.task_panel_style,
            task_panel_slot_index=spec.task_panel_slot_index,
            tab_before_showcase=spec.tab_before_showcase,
            accessibility_label=spec.accessibility_label,
        )


def register_window_tab_builders(tab_manager, feature, host, rect, tab_specs) -> None:
    """Register tab content builders from declarative (tab_key, builder_attr) specs."""
    for tab_key, builder_attr in tab_specs:
        builder = getattr(feature, str(builder_attr), None)
        if not callable(builder):
            raise AttributeError(f"Missing tab builder '{builder_attr}' for tab '{tab_key}'")
        tab_manager.register(str(tab_key), builder(host, Rect(rect)))


def build_tab_builder_specs(
    tab_entries: Sequence[tuple[str, str]],
    *,
    builder_prefix: str = "_build_",
    builder_suffix: str = "_tab",
) -> tuple[TabBuilderSpec, ...]:
    """Build TabBuilderSpec values from (key, label) entries with builder naming convention."""
    return tuple(
        TabBuilderSpec(
            key=str(tab_key),
            label=str(tab_label),
            builder_attr=f"{builder_prefix}{tab_key}{builder_suffix}",
        )
        for tab_key, tab_label in tab_entries
    )


def create_tab_control_from_specs(
    control_id: str,
    rect,
    tab_specs: Sequence[TabBuilderSpec],
    *,
    selected_key: str,
    on_change,
) -> TabControl:
    """Create a TabControl from declarative tab specs."""
    return TabControl(
        str(control_id),
        Rect(rect),
        items=[TabItem(spec.key, spec.label) for spec in tab_specs],
        selected_key=str(selected_key),
        on_change=on_change,
    )


def compute_tabbed_window_layout(
    content_rect: Rect,
    *,
    tab_height: int,
    tab_rows: int = 2,
    padding: int = 0,
    min_content_height: int = 60,
) -> tuple[Rect, Rect]:
    """Return (tab_rect, tab_content_rect) for a tabbed window content surface."""
    pad = int(padding)
    body_top = content_rect.top + pad
    body_bottom = content_rect.bottom - pad
    body_h = body_bottom - body_top
    body_content_top = body_top + (int(tab_height) * int(tab_rows))
    body_content_h = max(int(min_content_height), body_bottom - body_content_top)
    body_rect = Rect(content_rect.left + pad, body_top, content_rect.width - pad * 2, body_h)
    body_content_rect = Rect(
        content_rect.left + pad,
        body_content_top,
        content_rect.width - pad * 2,
        body_content_h,
    )
    return body_rect, body_content_rect


def register_window_tab_builder_specs(tab_manager, feature, host, rect, tab_specs: Sequence[TabBuilderSpec]) -> None:
    """Register tab content builders from TabBuilderSpec definitions."""
    register_window_tab_builders(
        tab_manager,
        feature,
        host,
        rect,
        [(spec.key, spec.builder_attr) for spec in tab_specs],
    )


def setup_feature_presenter_tabs(
    presenter,
    *,
    control_id: str,
    tab_rect,
    tab_specs: Sequence[TabBuilderSpec],
    selected_key: str,
    on_change,
    tab_manager,
    feature,
    host,
    tab_content_rect,
):
    """Create, attach, and register feature tab controls/builders in one call."""
    tab_control = create_tab_control_from_specs(
        control_id,
        tab_rect,
        tab_specs,
        selected_key=selected_key,
        on_change=on_change,
    )
    presenter.add_control(tab_control)
    register_window_tab_builder_specs(
        tab_manager,
        feature,
        host,
        tab_content_rect,
        tab_specs,
    )
    return tab_control


def register_tab_update_handlers(
    router: ActiveTabUpdateRouter,
    handlers: Sequence[tuple[str, Callable[..., object]]],
) -> None:
    """Register multiple active-tab update handlers on a router."""
    for tab_key, handler in handlers:
        router.register(tab_key, handler)


def create_presented_anchored_window(
    host,
    *,
    control_id: str,
    title: str,
    size: tuple[int, int],
    anchor: str,
    margin: tuple[int, int],
    presenter,
    window_control_cls=WindowControl,
    use_frame_backdrop: bool = True,
):
    """Create an anchored window and attach a presenter in one call."""
    window = create_anchored_feature_window(
        host,
        window_control_cls=window_control_cls,
        control_id=control_id,
        title=title,
        size=size,
        anchor=anchor,
        margin=margin,
        use_frame_backdrop=bool(use_frame_backdrop),
    )
    window.set_presenter(presenter)
    return window


def create_presented_window_from_spec(
    host,
    *,
    presenter,
    spec: AnchoredWindowSpec,
    window_control_cls=WindowControl,
):
    """Create and attach a presenter-backed anchored window from a typed spec."""
    return create_presented_anchored_window(
        host,
        control_id=spec.control_id,
        title=spec.title,
        size=spec.size,
        anchor=spec.anchor,
        margin=spec.margin,
        presenter=presenter,
        window_control_cls=window_control_cls,
        use_frame_backdrop=spec.use_frame_backdrop,
    )


def create_feature_presented_window(
    host,
    *,
    feature,
    presenter_cls,
    spec: AnchoredWindowSpec,
    window_control_cls=WindowControl,
):
    """Instantiate presenter from (feature, host) and create an anchored window from spec."""
    presenter = presenter_cls(feature, host)
    return create_presented_window_from_spec(
        host,
        presenter=presenter,
        spec=spec,
        window_control_cls=window_control_cls,
    )


def bind_feature_logic_aliases(feature, logic_bindings: Sequence[LogicBindingSpec]) -> None:
    """Bind routed-feature logic aliases idempotently from declarative bindings."""
    for binding in logic_bindings:
        if feature.bound_logic_name(alias=binding.alias) is None:
            feature.bind_logic(binding.provider_name, alias=binding.alias)


def setup_routed_feature_runtime(
    feature,
    host,
    *,
    scene_name: str = "main",
    scheduler_attr_name: str = "scheduler",
    scheduler_dispatch_limit: int | None = None,
    logic_bindings: Sequence[LogicBindingSpec] = (),
):
    """Initialize standard routed-feature runtime dependencies and optional logic bindings."""
    scheduler = ensure_scene_scheduler(
        feature,
        host,
        scene_name=scene_name,
        attr_name=scheduler_attr_name,
    )
    if scheduler_dispatch_limit is not None:
        scheduler.set_message_dispatch_limit(int(scheduler_dispatch_limit))
    if logic_bindings:
        bind_feature_logic_aliases(feature, logic_bindings)
    return scheduler
