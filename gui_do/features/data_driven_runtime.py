"""Generalized data-driven runtime and feature wiring helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence, Mapping

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
    SceneSetupSpec,
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
    key: int | None = None


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
class ActionHotkeySpec:
    """Declarative descriptor for registering one action and optional key binding."""

    action_name: str
    handler: Callable[[object], object]
    key: int | None = None
    scene_name: str | None = None


@dataclass(frozen=True)
class ControlKeyBindingSpec:
    """Declarative key binding that activates a control by attribute name.

    The key is bound to the control's standard activation path (_invoke_click),
    which for ButtonControl calls on_click and for ToggleControl commits a toggle.
    No handler lambda is required — declare the key, the attribute that holds the
    control, and an optional scene scope.
    """

    key: int
    control_attr: str          # attribute on the feature instance holding the control
    action_name: str | None = None  # optional name in action registry; auto-generated if None
    scene_name: str | None = None   # optional scene scope for the key binding


@dataclass(frozen=True)
class SceneTaskPanelSpec:
    """Declarative descriptor for scene task-panel creation."""

    scene_name: str
    control_id: str
    height: int = 50
    hidden_peek_pixels: int = 6
    animation_step_px: int = 8
    dock_bottom: bool = True
    auto_hide: bool = True


@dataclass(frozen=True)
class SceneReturnButtonSpec:
    """Declarative descriptor for a standard scene-return button on a task panel."""

    control_id: str = "scene_return"
    label: str = "Return"
    target_scene: str = "main"
    go_to_attr: str | None = None
    left: int = 16
    top_offset: int = 10
    width: int = 110
    height: int = 30
    style: str = "angle"
    accessibility_role: str = "button"
    accessibility_label: str = "Return"
    tab_index: int = -1


@dataclass(frozen=True)
class EventSubscriptionSpec:
    """Declarative descriptor for a feature-managed event-bus subscription."""

    attr_name: str
    topic: str
    handler: Callable[[object], object]
    scope: str | None = None


@dataclass(frozen=True)
class ShortcutOverlaySpec:
    """Declarative descriptor for a feature-owned ShortcutHelpOverlay."""

    attr_name: str
    action_registry_attr: str | None = "action_registry"
    width: int = 600
    height: int = 440
    offset_x: int = 0
    offset_y: int = 0
    toggle_action_name: str | None = None
    toggle_key: int | None = None
    toggle_scene_name: str | None = None


@dataclass(frozen=True)
class TaskPanelFocusToggleSpec:
    """Declarative descriptor for registering a scene task-panel focus toggle action."""

    action_name: str
    scene_name: str
    key: int


@dataclass(frozen=True)
class RoutedRuntimeSpec:
    """Declarative descriptor for standard routed-feature runtime wiring."""

    scene_name: str = "main"
    scheduler_attr_name: str = "scheduler"
    scheduler_dispatch_limit: int | None = None
    logic_bindings: Sequence[LogicBindingSpec] = field(default_factory=tuple)
    action_hotkeys: Sequence[ActionHotkeySpec] = field(default_factory=tuple)
    control_key_bindings: Sequence[ControlKeyBindingSpec] = field(default_factory=tuple)
    event_subscriptions: Sequence[EventSubscriptionSpec] = field(default_factory=tuple)
    shortcut_overlays: Sequence[ShortcutOverlaySpec] = field(default_factory=tuple)
    task_panel_focus_toggles: Sequence[TaskPanelFocusToggleSpec] = field(default_factory=tuple)


@dataclass(frozen=True)
class RoutedFeatureLifecycleSpec:
    """Declarative lifecycle wiring for routed features.

    Combines optional companion-provider registration with runtime setup/teardown
    wiring so feature methods can stay thin and data-driven.
    """

    companion_providers: Sequence[object | Callable[[], object]] = field(default_factory=tuple)
    runtime_spec: RoutedRuntimeSpec | None = None
    runtime_spec_factory: Callable[[object, object], RoutedRuntimeSpec] | None = None
    runtime_spec_attr_name: str = "_runtime_spec"
    scheduler_attr_name: str | None = "scheduler"


@dataclass(frozen=True)
class FeatureWindowBundleBindingSpec:
    """Input descriptor pairing a feature factory with its window toggle metadata.

    Combines the FeatureSpec and WindowToggleBindingSpec declarations that typically
    appear together in ``feature_entries`` and ``window_entries``, so windowed features
    can be declared as a single self-contained entry.
    """

    feature_attr: str
    factory: object  # Callable[[], object]
    window_key: str
    slot_index: int
    task_panel_label: str | None = None
    task_panel_style: str = "round"
    tab_before_showcase: bool = False
    action_label: str | None = None
    action_name: str | None = None
    task_panel_button_id: str | None = None
    toggle_attr: str | None = None
    accessibility_label: str | None = None


@dataclass(frozen=True)
class WindowToggleBindingSpec:
    """Input descriptor for building a WindowSpec with conventional defaults."""

    key: str
    feature_attr: str
    slot_index: int
    task_panel_label: str | None = None
    task_panel_style: str = "round"
    tab_before_showcase: bool = False
    action_label: str | None = None
    action_name: str | None = None
    task_panel_button_id: str | None = None
    toggle_attr: str | None = None
    accessibility_label: str | None = None


@dataclass(frozen=True)
class SceneSetupBindingSpec:
    """Input descriptor for building SceneSetupSpec with common defaults."""

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


@dataclass(frozen=True)
class RuntimeSceneBindingSpec:
    """Input descriptor for building RuntimeSceneSpec with shorthand defaults."""

    scene_name: str
    pristine_asset: str | None = None
    bind_escape_to_exit: bool = False
    prewarm: bool = False


@dataclass(frozen=True)
class SceneRootBindingSpec:
    """Input descriptor for building SceneRootSpec with shorthand defaults."""

    scene_name: str
    control_id: str
    draw_background: bool = False


@dataclass(frozen=True)
class CursorBindingSpec:
    """Input descriptor for building CursorSpec values with shorthand defaults."""

    name: str
    path: str
    hotspot: tuple[int, int] = (0, 0)


@dataclass(frozen=True)
class FontRoleBindingSpec:
    """Input descriptor for building one font role mapping entry."""

    role: str
    size: int
    font: str
    bold: bool = False
    italic: bool = False


@dataclass(frozen=True)
class ActionBindingSpec:
    """Input descriptor for building ActionSpec values from common action kinds."""

    kind: str  # "exit" | "scene_nav" | "palette_open"
    action_id: str
    label: str
    target: str | None = None
    category: str | None = None
    key: int | None = None


@dataclass(frozen=True)
class SceneBundleBindingSpec:
    """Input descriptor for building scene lifecycle/action/root bundles.

    A bundle can declare any combination of scene setup, runtime startup,
    navigation action, and scene-root creation for one scene.
    """

    scene_name: str
    pretty_name: str | None = None
    transition_style: object | None = None
    transition_duration: float | None = None
    make_initial: bool = False
    tiling_enabled: bool = True
    tiling_gap: int | None = 16
    tiling_padding: int | None = 16
    tiling_avoid_task_panel: bool | None = True
    tiling_center_on_failure: bool | None = True
    tiling_relayout: bool = False
    include_scene_setup: bool = True

    pristine_asset: str | None = None
    bind_escape_to_exit: bool = False
    prewarm: bool = False
    include_runtime_scene: bool = True

    include_nav_action: bool = False
    nav_action_id: str | None = None
    nav_label: str | None = None
    nav_category: str | None = "Scenes"

    include_scene_root: bool = False
    scene_root_id: str | None = None
    scene_root_draw_background: bool = False


@dataclass(frozen=True)
class PaletteBindingSpec:
    """User-side declaration for command palette behavior.

    gui_do provides the command palette as a facility; this spec lets the user
    declare whether built-in scene/window entries are populated and whether
    window toggles route through the window presentation model (keeping task
    panel toggle buttons in sync).
    """

    enable_builtin_entries: bool = True
    connect_window_presentation: bool = True


@dataclass(frozen=True)
class HostApplicationBindingSpec:
    """Input descriptor for building a complete HostApplicationConfig."""

    display_size: tuple[int, int]
    window_title: str
    fonts: Mapping[str, object]
    initial_scene_name: str
    scene_entries: Sequence[SceneSetupBindingSpec | SceneSetupSpec | tuple] = field(default_factory=tuple)
    feature_entries: Sequence[tuple[str, Callable[[], object]] | FeatureSpec] = field(default_factory=tuple)
    window_entries: Sequence[WindowToggleBindingSpec | WindowSpec] = field(default_factory=tuple)
    runtime_scene_entries: Sequence[RuntimeSceneBindingSpec | RuntimeSceneSpec | str | tuple] = field(default_factory=tuple)
    action_entries: Sequence[ActionBindingSpec | ActionSpec] = field(default_factory=tuple)
    static_accessibility_entries: Sequence[tuple[str, str] | StaticAccessibilitySpec] = field(default_factory=tuple)
    scene_bundle_entries: Sequence[SceneBundleBindingSpec | SceneSetupSpec | RuntimeSceneSpec | SceneRootSpec | ActionSpec] = field(default_factory=tuple)
    feature_window_bundle_entries: Sequence[FeatureWindowBundleBindingSpec | FeatureSpec | WindowSpec] = field(default_factory=tuple)
    font_role_entries: Sequence[FontRoleBindingSpec | tuple[str, int, str] | tuple[str, int, str, bool, bool] | Mapping[str, Mapping[str, object]]] = field(default_factory=tuple)
    cursor_entries: Sequence[CursorBindingSpec | CursorSpec | tuple[str, str] | tuple[str, str, tuple[int, int]]] = field(default_factory=tuple)
    scene_root_entries: Sequence[SceneRootBindingSpec | SceneRootSpec | tuple[str, str] | tuple[str, str, bool]] = field(default_factory=tuple)
    telemetry: TelemetryConfig | None = None
    target_fps: int = 120
    scene_default_transition_style: object | None = None
    scene_default_transition_duration: float | None = None
    runtime_default_pristine_asset: str | None = None
    runtime_default_bind_escape_to_exit: bool = False
    runtime_default_prewarm: bool = False
    static_accessibility_role: str = "button"
    palette_spec: PaletteBindingSpec | None = None


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


@dataclass(frozen=True)
class NotificationSpec:
    """Declarative descriptor for a pre-seeded :class:`~gui_do.NotificationRecord`.

    Pass a sequence of these to :func:`build_notification_center` to create a
    fully populated :class:`~gui_do.NotificationCenter` without writing
    imperative ``.add()`` calls.

    Attributes:
        message: The notification body text.
        title: Optional short heading.
        severity: Visual classification; defaults to ``ToastSeverity.INFO``.
    """

    message: str
    title: str = ""
    severity: object = None  # ToastSeverity.INFO — resolved at call time to avoid import cycle


@dataclass(frozen=True)
class TabbedPresenterSpec:
    """Declarative descriptor for presenter-hosted tab layout and setup."""

    control_id: str
    selected_key: str
    tab_height: int = 36
    tab_rows: int = 2
    padding: int = 0
    min_content_height: int = 60


def build_notification_center(
    specs: Sequence["NotificationSpec"],
    *,
    max_records: int = 6,
) -> "object":
    """Return a pre-populated :class:`~gui_do.NotificationCenter`.

    Creates the center with *max_records* capacity, then adds one
    :class:`~gui_do.NotificationRecord` per entry in *specs*.

    Args:
        specs: Ordered sequence of :class:`NotificationSpec` objects.
        max_records: Maximum number of records the center will retain.

    Returns:
        A ready-to-use :class:`~gui_do.NotificationCenter` instance.

    Example::

        from gui_do import NotificationSpec, build_notification_center
        from gui_do import ToastSeverity

        nc = build_notification_center(
            (
                NotificationSpec("Build succeeded", title="Pipeline", severity=ToastSeverity.SUCCESS),
                NotificationSpec("Unsaved changes", title="Editor", severity=ToastSeverity.WARNING),
            ),
            max_records=6,
        )
    """
    from ..overlays.notification_center import NotificationCenter, NotificationRecord
    from ..overlays.toast_manager import ToastSeverity as _Sev

    center = NotificationCenter(None, max_records=max(1, int(max_records)))
    for spec in specs:
        severity = spec.severity if spec.severity is not None else _Sev.INFO
        center.add(NotificationRecord(spec.message, title=str(spec.title), severity=severity))
    return center


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
    palette_spec: PaletteBindingSpec | None = None


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
    palette_spec = getattr(config, "palette_spec", None)
    if palette_spec is not None and palette_spec.enable_builtin_entries:
        host._palette_manager.enable_builtin_scene_and_window_entries(
            host.app,
            on_scene_selected=host.scene_transitions.go,
            window_presentation=host.window_presentation if palette_spec.connect_window_presentation else None,
        )
    declare_host_actions(host, config.action_specs)

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

    # 14 – Accessibility metadata
    window_toggle_controls = collect_window_toggle_controls(host, host.window_presentation)
    base_controls = build_host_main_tab_order(host, window_toggle_controls)
    apply_host_main_accessibility(host, base_controls, config.static_accessibility_specs)

    # 15 – Switch to initial scene
    host.app.switch_scene(config.initial_scene_name)


def declare_host_actions(host, action_specs) -> None:
    """Declare all standard actions on host.action_registry from declarative specs.

    Also binds any declared key to the application input dispatcher so the user's
    key choice (e.g. F5 for palette_open) is honoured without any hidden auto-binding.
    """
    r = host.action_registry
    app_actions = getattr(host.app, "actions", None)
    for spec in action_specs:
        handler = _build_standard_action_handler(host, spec)
        if spec.category is None:
            r.declare(spec.action_id, spec.label, handler)
        else:
            r.declare(spec.action_id, spec.label, handler, category=spec.category)
        if spec.key is not None and app_actions is not None:
            app_actions.register_action(str(spec.action_id), lambda _ev, _h=handler: _h(None, _ev))
            app_actions.bind_key(int(spec.key), str(spec.action_id))
    host.window_presentation.declare_actions(r, category="Windows")


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
    """Return the main-scene controls in declarative accessibility order."""
    before_showcase = [c for b, c in window_toggle_controls if b.tab_before_showcase]
    after_showcase = [c for b, c in window_toggle_controls if not b.tab_before_showcase]
    base_controls = [host.exit_button]
    base_controls.extend(before_showcase)
    base_controls.append(host.showcase_button)
    base_controls.extend(after_showcase)
    return base_controls


def apply_host_main_accessibility(host, base_controls, static_accessibility_specs) -> None:
    """Apply static and dynamic accessibility metadata after build_features."""
    for spec in static_accessibility_specs:
        control = getattr(host, spec.control_attr, None)
        if control is None:
            continue
        control.set_accessibility(role=spec.role, label=spec.label)
    apply_window_toggle_accessibility(host, host.window_presentation, role="toggle")


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


def add_window_toggle_task_panel_controls(
    host,
    task_panel,
    app_layout,
    window_presentation,
    *,
    min_slot_index: int | None = None,
    max_slot_index: int | None = None,
):
    """Create window toggle controls on the task panel from declarative bindings.

    Optional slot bounds allow callers to create controls in phases so focus order
    can match visual slot order when mixed with non-toggle controls.
    """
    toggle_controls = []
    max_seen_slot_index = 0
    for binding in sorted_window_bindings(window_presentation.bindings()):
        slot_index = 1 if binding.task_panel_slot_index is None else int(binding.task_panel_slot_index)
        if min_slot_index is not None and slot_index < int(min_slot_index):
            continue
        if max_slot_index is not None and slot_index > int(max_slot_index):
            continue
        max_seen_slot_index = max(max_seen_slot_index, slot_index)
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
    return toggle_controls, max_seen_slot_index


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


def register_action_hotkeys(app_actions, specs: Sequence[ActionHotkeySpec]) -> None:
    """Register multiple actions and optional key bindings from declarative specs."""
    if app_actions is None:
        return
    for spec in specs:
        action_name = str(spec.action_name)
        app_actions.register_action(action_name, spec.handler)
        if spec.key is None:
            continue
        if spec.scene_name is None:
            app_actions.bind_key(spec.key, action_name)
        else:
            app_actions.bind_key(spec.key, action_name, scene=str(spec.scene_name))


def register_control_key_bindings(feature, app_actions, specs) -> None:
    """Register declarative key-to-control bindings from ControlKeyBindingSpec entries.

    Each spec resolves ``control_attr`` on *feature* at registration time and binds
    the key to the control's activation path (_invoke_click).  This covers buttons
    (on_click) and toggles (_commit_toggle) with no handler lambda required.
    """
    if app_actions is None:
        return
    for spec in specs:
        control = getattr(feature, str(spec.control_attr), None)
        if control is None:
            continue
        action_name = str(spec.action_name) if spec.action_name else f"_ctrl_{spec.control_attr}"
        def _make_handler(c):
            def _handler(_e):
                invoke = getattr(c, "_invoke_click", None)
                if callable(invoke):
                    invoke()
                return True
            return _handler
        app_actions.register_action(action_name, _make_handler(control))
        if spec.scene_name is None:
            app_actions.bind_key(int(spec.key), action_name)
        else:
            app_actions.bind_key(int(spec.key), action_name, scene=str(spec.scene_name))


def draw_controls_prewarm(surface, theme, controls: Iterable[object]) -> None:
    """Draw a sequence of controls for prewarm, skipping ``None`` entries safely."""
    for control in controls:
        if control is None:
            continue
        draw = getattr(control, "draw", None)
        if callable(draw):
            draw(surface, theme)


def ensure_scene_task_panel(host, spec: SceneTaskPanelSpec):
    """Create/return a scene task panel from a declarative spec."""
    return host.scene_presentation.ensure_scene_task_panel(
        str(spec.scene_name),
        control_id=str(spec.control_id),
        height=int(spec.height),
        hidden_peek_pixels=int(spec.hidden_peek_pixels),
        animation_step_px=int(spec.animation_step_px),
        dock_bottom=bool(spec.dock_bottom),
        auto_hide=bool(spec.auto_hide),
    )


def _resolve_scene_navigation_callback(host, spec: SceneReturnButtonSpec):
    """Resolve return-button navigation callback with host-first overrides."""
    attr_name = spec.go_to_attr or f"go_to_{spec.target_scene}"
    cb = getattr(host, str(attr_name), None)
    if callable(cb):
        return cb

    scene_transitions = getattr(host, "scene_transitions", None)
    if scene_transitions is not None and hasattr(scene_transitions, "go"):
        return lambda: scene_transitions.go(str(spec.target_scene))

    app = getattr(host, "app", None)
    if app is not None and hasattr(app, "switch_scene"):
        return lambda: app.switch_scene(str(spec.target_scene))

    return lambda: None


def add_scene_return_button(task_panel, host, spec: SceneReturnButtonSpec):
    """Add a standard scene-return button to a task panel from declarative spec."""
    rect = Rect(
        int(spec.left),
        int(task_panel.rect.top + int(spec.top_offset)),
        int(spec.width),
        int(spec.height),
    )
    button = task_panel.add(
        ButtonControl(
            str(spec.control_id),
            rect,
            str(spec.label),
            _resolve_scene_navigation_callback(host, spec),
            style=str(spec.style),
        )
    )
    button.set_accessibility(role=str(spec.accessibility_role), label=str(spec.accessibility_label))
    button.set_tab_index(int(spec.tab_index))
    return button


def centered_overlay_rect(surface, *, width: int, height: int, offset_x: int = 0, offset_y: int = 0) -> Rect:
    """Return a centered overlay rect on *surface* with optional pixel offsets."""
    w = max(1, int(width))
    h = max(1, int(height))
    return Rect(
        max(0, (int(surface.get_width()) // 2) - (w // 2) + int(offset_x)),
        max(0, (int(surface.get_height()) // 2) - (h // 2) + int(offset_y)),
        w,
        h,
    )


def create_shortcut_help_overlay(
    app,
    *,
    action_registry=None,
    width: int = 600,
    height: int = 440,
    offset_x: int = 0,
    offset_y: int = 0,
):
    """Create a ShortcutHelpOverlay centered on the app surface."""
    from ..overlays.shortcut_help_overlay import ShortcutHelpOverlay

    overlay_rect = centered_overlay_rect(
        app.surface,
        width=int(width),
        height=int(height),
        offset_x=int(offset_x),
        offset_y=int(offset_y),
    )
    return ShortcutHelpOverlay(
        app.overlay,
        action_registry=action_registry,
        overlay_rect=overlay_rect,
    )


def bind_feature_event_subscription(feature, app_events, spec: EventSubscriptionSpec):
    """Create and store an event subscription token on a feature attribute."""
    if app_events is None or not hasattr(app_events, "subscribe"):
        setattr(feature, str(spec.attr_name), None)
        return None
    token = app_events.subscribe(str(spec.topic), spec.handler, scope=spec.scope)
    setattr(feature, str(spec.attr_name), token)
    return token


def unbind_feature_event_subscription(feature, app_events, *, attr_name: str) -> bool:
    """Unsubscribe and clear a feature-owned event subscription token attribute."""
    token = getattr(feature, str(attr_name), None)
    if token is None:
        return False
    if app_events is None or not hasattr(app_events, "unsubscribe"):
        setattr(feature, str(attr_name), None)
        return False
    app_events.unsubscribe(token)
    setattr(feature, str(attr_name), None)
    return True


def setup_routed_runtime(feature, host, spec: RoutedRuntimeSpec):
    """Apply standard routed-feature runtime wiring from a declarative spec.

    Wires scheduler/logic aliases, optional action hotkeys, event subscriptions,
    and optional shortcut overlays while keeping feature bind_runtime methods short.
    """
    scheduler = setup_routed_feature_runtime(
        feature,
        host,
        scene_name=str(spec.scene_name),
        scheduler_attr_name=str(spec.scheduler_attr_name),
        scheduler_dispatch_limit=spec.scheduler_dispatch_limit,
        logic_bindings=tuple(spec.logic_bindings),
    )

    app = getattr(host, "app", None)
    app_actions = getattr(app, "actions", None)
    app_events = getattr(app, "events", None)

    if spec.action_hotkeys and app_actions is not None:
        register_action_hotkeys(app_actions, tuple(spec.action_hotkeys))

    if spec.control_key_bindings and app_actions is not None:
        register_control_key_bindings(feature, app_actions, tuple(spec.control_key_bindings))

    if spec.event_subscriptions and app_events is not None:
        for subscription in spec.event_subscriptions:
            bind_feature_event_subscription(feature, app_events, subscription)

    if spec.shortcut_overlays and app is not None:
        for overlay_spec in spec.shortcut_overlays:
            action_registry = None
            if overlay_spec.action_registry_attr:
                action_registry = getattr(host, str(overlay_spec.action_registry_attr), None)
            overlay = create_shortcut_help_overlay(
                app,
                action_registry=action_registry,
                width=int(overlay_spec.width),
                height=int(overlay_spec.height),
                offset_x=int(overlay_spec.offset_x),
                offset_y=int(overlay_spec.offset_y),
            )
            setattr(feature, str(overlay_spec.attr_name), overlay)
            if overlay_spec.toggle_action_name and app_actions is not None:
                def _make_toggle(ov):
                    return lambda _e: (ov.toggle() or True)
                action_name = str(overlay_spec.toggle_action_name)
                app_actions.register_action(action_name, _make_toggle(overlay))
                if overlay_spec.toggle_key is not None:
                    if overlay_spec.toggle_scene_name is not None:
                        app_actions.bind_key(int(overlay_spec.toggle_key), action_name, scene=str(overlay_spec.toggle_scene_name))
                    else:
                        app_actions.bind_key(int(overlay_spec.toggle_key), action_name)

    if spec.task_panel_focus_toggles and app is not None and app_actions is not None:
        for tpft in spec.task_panel_focus_toggles:
            bind_task_panel_focus_toggle(
                app_actions,
                app,
                action_name=str(tpft.action_name),
                scene_name=str(tpft.scene_name),
                key=int(tpft.key),
            )

    return scheduler


def shutdown_routed_runtime(feature, host, spec: RoutedRuntimeSpec) -> None:
    """Unwire routed-feature runtime resources declared in RoutedRuntimeSpec."""
    app = getattr(host, "app", None)
    app_events = getattr(app, "events", None)
    if spec.event_subscriptions and app_events is not None:
        for subscription in spec.event_subscriptions:
            unbind_feature_event_subscription(feature, app_events, attr_name=subscription.attr_name)


def _resolve_routed_feature_runtime_spec(feature, host, lifecycle_spec: RoutedFeatureLifecycleSpec) -> RoutedRuntimeSpec:
    """Resolve routed runtime spec from a static value or dynamic factory."""
    if lifecycle_spec.runtime_spec_factory is not None:
        return lifecycle_spec.runtime_spec_factory(feature, host)
    if lifecycle_spec.runtime_spec is not None:
        return lifecycle_spec.runtime_spec
    raise ValueError("RoutedFeatureLifecycleSpec requires runtime_spec or runtime_spec_factory")


def register_routed_feature_companions(feature, host, lifecycle_spec: RoutedFeatureLifecycleSpec) -> tuple[object, ...]:
    """Register companion providers declared by RoutedFeatureLifecycleSpec.

    Entries in ``companion_providers`` can be either provider instances or
    zero-argument factories.
    """
    manager = getattr(feature, "_feature_manager", None)
    if manager is None:
        return ()
    providers: list[object] = []
    for provider_entry in lifecycle_spec.companion_providers:
        provider = provider_entry() if callable(provider_entry) else provider_entry
        if provider is None:
            continue
        providers.append(provider)
    if providers:
        register_companion_logic_features(manager, host, providers)
    return tuple(providers)


def bind_routed_feature_lifecycle(feature, host, lifecycle_spec: RoutedFeatureLifecycleSpec):
    """Bind runtime resources for a routed feature from one lifecycle spec."""
    runtime_spec = _resolve_routed_feature_runtime_spec(feature, host, lifecycle_spec)
    scheduler = setup_routed_runtime(feature, host, runtime_spec)
    runtime_attr = str(lifecycle_spec.runtime_spec_attr_name)
    if runtime_attr:
        setattr(feature, runtime_attr, runtime_spec)
    scheduler_attr = lifecycle_spec.scheduler_attr_name
    if scheduler_attr:
        setattr(feature, str(scheduler_attr), scheduler)
    return scheduler


def shutdown_routed_feature_lifecycle(feature, host, lifecycle_spec: RoutedFeatureLifecycleSpec) -> bool:
    """Shutdown runtime resources for a routed feature from one lifecycle spec."""
    runtime_spec = None
    runtime_attr = str(lifecycle_spec.runtime_spec_attr_name)
    if runtime_attr:
        runtime_spec = getattr(feature, runtime_attr, None)
    if runtime_spec is None:
        runtime_spec = lifecycle_spec.runtime_spec
    if runtime_spec is None:
        return False
    shutdown_routed_runtime(feature, host, runtime_spec)
    if runtime_attr:
        setattr(feature, runtime_attr, None)
    scheduler_attr = lifecycle_spec.scheduler_attr_name
    if scheduler_attr:
        setattr(feature, str(scheduler_attr), None)
    return True


def bind_task_panel_focus_toggle(
    app_actions,
    app,
    *,
    action_name: str,
    scene_name: str,
    key,
) -> None:
    """Register and bind the standard task-panel focus toggle action.

    Encapsulates the repeated pattern of registering a focus-toggle action and
    binding it to a key per scene::

        bind_task_panel_focus_toggle(
            host.app.actions, host.app,
            action_name="toggle_task_panel_focus",
            scene_name="main",
            key=pygame.K_F1,
        )
    """
    def _toggle(_event):
        overlay = getattr(app, "overlay", None)
        has_overlay = getattr(overlay, "has_overlay", None)
        if callable(has_overlay) and has_overlay("__command_palette__"):
            return True
        task_panel_focus = getattr(app, "task_panel_focus", None)
        return bool(task_panel_focus is not None and task_panel_focus.toggle(app.scene, app))

    app_actions.register_action(str(action_name), _toggle)
    app_actions.bind_key(key, str(action_name), scene=str(scene_name))


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


class TabLayoutContext:
    """Cursor-tracking helper for building tab content layouts.

    Carries window, control list, pad, x, and y cursor so tab build
    methods describe *what* to place rather than tracking coordinates
    manually.  Call ``build()`` to retrieve the accumulated control list.

    Usage::

        ctx = TabLayoutContext(self.window, rect)
        ctx.add_label("my_lbl", 22, "Hello")
        ctx.add_button_row(height=28, gap=8, specs=(...))
        return ctx.build()
    """

    def __init__(self, window, rect: Rect, *, pad: int = 8) -> None:
        self._window = window
        self._rect = Rect(rect)
        self._pad = int(pad)
        self._controls: list = []
        self._x = rect.left + self._pad
        self._y = rect.top + self._pad
        self._w = rect.width - self._pad * 2

    # ------------------------------------------------------------------
    # Read-only geometry accessors
    # ------------------------------------------------------------------

    @property
    def x(self) -> int:
        """Left x position for content (rect.left + pad)."""
        return self._x

    @property
    def y(self) -> int:
        """Current y cursor position."""
        return self._y

    @property
    def width(self) -> int:
        """Content width (rect.width - pad * 2)."""
        return self._w

    @property
    def pad(self) -> int:
        """Padding value supplied at construction."""
        return self._pad

    # ------------------------------------------------------------------
    # Control placement helpers
    # ------------------------------------------------------------------

    def add_control(self, control):
        """Add an already-constructed control to the window and control list.

        Does **not** advance the y cursor — call ``advance(n)`` afterwards.
        """
        return add_window_control(self._window, self._controls, control)

    def add_label(
        self,
        control_id: str,
        height: int,
        text: str,
        *,
        width: int | None = None,
        advance: int | None = None,
        align: str = "left",
    ):
        """Add a label at the current cursor and advance y.

        *width* defaults to the full content width (``self.width``).
        *advance* defaults to ``height + 8``.  Pass ``advance=0`` to keep y
        unchanged (useful when placing a label beside another control).
        """
        w = int(width) if width is not None else self._w
        ctrl = add_window_label(
            self._window,
            self._controls,
            str(control_id),
            Rect(self._x, self._y, w, int(height)),
            str(text),
            align=str(align),
        )
        self._y += int(advance) if advance is not None else int(height) + 8
        return ctrl

    def add_button(
        self,
        control_id: str,
        width: int,
        height: int,
        text: str,
        on_click,
        *,
        style=None,
        x_offset: int = 0,
        advance: int | None = None,
    ):
        """Add a button at the current cursor and advance y.

        *x_offset* shifts the button right of the standard left margin.
        *advance* defaults to ``height + 8``.
        """
        ctrl = add_window_button(
            self._window,
            self._controls,
            str(control_id),
            Rect(self._x + int(x_offset), self._y, int(width), int(height)),
            str(text),
            on_click,
            style=style,
        )
        self._y += int(advance) if advance is not None else int(height) + 8
        return ctrl

    def add_button_row(
        self,
        *,
        height: int,
        gap: int,
        specs,
        width: int | None = None,
        advance: int | None = None,
    ) -> tuple:
        """Add a horizontal button row at the current cursor and advance y.

        *width* is the per-button width.  *advance* defaults to ``height + 8``.
        """
        result = add_window_button_row(
            self._window,
            self._controls,
            x=self._x,
            y=self._y,
            width=int(width) if width is not None else self._w,
            height=int(height),
            gap=int(gap),
            specs=specs,
        )
        self._y += int(advance) if advance is not None else int(height) + 8
        return result

    # ------------------------------------------------------------------
    # Cursor management
    # ------------------------------------------------------------------

    def advance(self, n: int) -> "TabLayoutContext":
        """Manually advance the y cursor by *n* pixels."""
        self._y += int(n)
        return self

    def remaining_height(self, *, margin: int = 0) -> int:
        """Height from the current cursor to the bottom of the rect minus margin."""
        return max(0, self._rect.bottom - self._y - int(margin))

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def build(self) -> list:
        """Return the accumulated control list."""
        return list(self._controls)


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
    label: str = "Open Command Palette",
    key: int | None = None,
) -> ActionSpec:
    """Build a standard command-palette open ActionSpec."""
    return ActionSpec(
        action_id=str(action_id),
        label=str(label),
        kind="palette_open",
        target=None,
        category=None,
        key=key,
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


def build_feature_specs(entries: Sequence[tuple[str, Callable[[], object]] | FeatureSpec]) -> tuple[FeatureSpec, ...]:
    """Build FeatureSpec values from shorthand tuples or existing FeatureSpec instances.

    Each entry can be either:
    - ``FeatureSpec(attr_name=..., factory=...)``
    - ``(attr_name, factory)``
    """
    specs: list[FeatureSpec] = []
    for entry in entries:
        if isinstance(entry, FeatureSpec):
            specs.append(entry)
            continue
        attr_name, factory = entry
        specs.append(FeatureSpec(attr_name=str(attr_name), factory=factory))
    return tuple(specs)


def build_feature_window_bundle_specs(
    entries: Sequence[FeatureWindowBundleBindingSpec | FeatureSpec | WindowSpec],
) -> tuple[tuple[FeatureSpec, ...], tuple[WindowSpec, ...]]:
    """Build parallel (FeatureSpec, WindowSpec) tuples from bundle entries.

    Each ``FeatureWindowBundleBindingSpec`` expands into one ``FeatureSpec`` and one
    ``WindowSpec``.  Pre-built ``FeatureSpec`` or ``WindowSpec`` entries are routed to
    their respective output tuple — a bare ``FeatureSpec`` passes through without
    producing a window entry, and a bare ``WindowSpec`` passes through without producing
    a feature entry.
    """
    feature_specs: list[FeatureSpec] = []
    window_specs: list[WindowSpec] = []
    for entry in entries:
        if isinstance(entry, FeatureSpec):
            feature_specs.append(entry)
            continue
        if isinstance(entry, WindowSpec):
            window_specs.append(entry)
            continue
        feature_specs.append(FeatureSpec(attr_name=str(entry.feature_attr), factory=entry.factory))
        window_specs.append(
            make_window_toggle_spec(
                entry.window_key,
                entry.feature_attr,
                slot_index=entry.slot_index,
                task_panel_label=entry.task_panel_label,
                task_panel_style=entry.task_panel_style,
                tab_before_showcase=entry.tab_before_showcase,
                action_label=entry.action_label,
                action_name=entry.action_name,
                task_panel_button_id=entry.task_panel_button_id,
                toggle_attr=entry.toggle_attr,
                accessibility_label=entry.accessibility_label,
            )
        )
    return tuple(feature_specs), tuple(window_specs)


def build_window_toggle_specs(bindings: Sequence[WindowToggleBindingSpec | WindowSpec]) -> tuple[WindowSpec, ...]:
    """Build WindowSpec values from WindowToggleBindingSpec entries.

    Entries may also include pre-built WindowSpec instances for mixed workflows.
    """
    specs: list[WindowSpec] = []
    for binding in bindings:
        if isinstance(binding, WindowSpec):
            specs.append(binding)
            continue
        specs.append(
            make_window_toggle_spec(
                binding.key,
                binding.feature_attr,
                slot_index=binding.slot_index,
                task_panel_label=binding.task_panel_label,
                task_panel_style=binding.task_panel_style,
                tab_before_showcase=binding.tab_before_showcase,
                action_label=binding.action_label,
                action_name=binding.action_name,
                task_panel_button_id=binding.task_panel_button_id,
                toggle_attr=binding.toggle_attr,
                accessibility_label=binding.accessibility_label,
            )
        )
    return tuple(specs)


def build_scene_nav_actions(
    nav_entries: Sequence[tuple[str, str, str] | ActionSpec],
    *,
    category: str = "Scenes",
) -> tuple[ActionSpec, ...]:
    """Build scene-navigation ActionSpec values from shorthand tuples.

    Each tuple entry is ``(action_id, label, target_scene)``.
    Pre-built ActionSpec entries are passed through unchanged.
    """
    specs: list[ActionSpec] = []
    for entry in nav_entries:
        if isinstance(entry, ActionSpec):
            specs.append(entry)
            continue
        action_id, label, target_scene = entry
        specs.append(
            make_scene_nav_action(
                str(action_id),
                label=str(label),
                target_scene=str(target_scene),
                category=str(category),
            )
        )
    return tuple(specs)


def build_action_specs(entries: Sequence[ActionBindingSpec | ActionSpec]) -> tuple[ActionSpec, ...]:
    """Build ActionSpec values from ActionBindingSpec entries.

    Supports common action kinds:
    - ``exit``
    - ``scene_nav`` (requires ``target``)
    - ``palette_open``

    Pre-built ActionSpec entries are passed through unchanged.
    """
    specs: list[ActionSpec] = []
    for entry in entries:
        if isinstance(entry, ActionSpec):
            specs.append(entry)
            continue
        kind = str(entry.kind)
        if kind == "exit":
            specs.append(
                make_exit_action(
                    action_id=str(entry.action_id),
                    label=str(entry.label),
                    category="File" if entry.category is None else str(entry.category),
                )
            )
            continue
        if kind == "scene_nav":
            if entry.target is None:
                raise ValueError("scene_nav action bindings require target")
            specs.append(
                make_scene_nav_action(
                    str(entry.action_id),
                    label=str(entry.label),
                    target_scene=str(entry.target),
                    category="Scenes" if entry.category is None else str(entry.category),
                )
            )
            continue
        if kind == "palette_open":
            specs.append(
                make_palette_open_action(
                    action_id=str(entry.action_id),
                    label=str(entry.label),
                    key=entry.key,
                )
            )
            continue
        raise ValueError(f"Unsupported action binding kind: {kind!r}")
    return tuple(specs)


def build_static_accessibility_specs(
    entries: Sequence[tuple[str, str] | StaticAccessibilitySpec],
    *,
    role: str = "button",
) -> tuple[StaticAccessibilitySpec, ...]:
    """Build StaticAccessibilitySpec values from shorthand tuples.

    Each tuple entry is ``(control_attr, label)`` and uses the shared *role*.
    Pre-built StaticAccessibilitySpec entries are passed through unchanged.
    """
    specs: list[StaticAccessibilitySpec] = []
    for entry in entries:
        if isinstance(entry, StaticAccessibilitySpec):
            specs.append(entry)
            continue
        control_attr, label = entry
        specs.append(
            make_static_accessibility_spec(
                str(control_attr),
                label=str(label),
                role=str(role),
            )
        )
    return tuple(specs)


def build_scene_setup_specs(
    entries: Sequence[SceneSetupBindingSpec | SceneSetupSpec | tuple],
    *,
    default_transition_style: object | None = None,
    default_transition_duration: float | None = None,
    initial_scene_name: str | None = None,
) -> tuple[SceneSetupSpec, ...]:
    """Build SceneSetupSpec values from shorthand tuples or binding specs.

    Supported tuple forms:
    - ``(name, pretty_name)``
    - ``(name, pretty_name, transition_style)``
    - ``(name, pretty_name, transition_style, transition_duration)``
    """
    specs: list[SceneSetupSpec] = []
    for entry in entries:
        if isinstance(entry, SceneSetupSpec):
            make_initial = bool(entry.make_initial or (initial_scene_name is not None and str(entry.name) == str(initial_scene_name)))
            specs.append(
                SceneSetupSpec(
                    name=str(entry.name),
                    pretty_name=entry.pretty_name,
                    transition_style=entry.transition_style,
                    transition_duration=entry.transition_duration,
                    tiling_enabled=bool(entry.tiling_enabled),
                    tiling_gap=entry.tiling_gap,
                    tiling_padding=entry.tiling_padding,
                    tiling_avoid_task_panel=entry.tiling_avoid_task_panel,
                    tiling_center_on_failure=entry.tiling_center_on_failure,
                    tiling_relayout=bool(entry.tiling_relayout),
                    make_initial=make_initial,
                )
            )
            continue

        if isinstance(entry, SceneSetupBindingSpec):
            transition_style = entry.transition_style if entry.transition_style is not None else default_transition_style
            transition_duration = entry.transition_duration if entry.transition_duration is not None else default_transition_duration
            make_initial = bool(entry.make_initial or (initial_scene_name is not None and str(entry.name) == str(initial_scene_name)))
            specs.append(
                SceneSetupSpec(
                    name=str(entry.name),
                    pretty_name=entry.pretty_name,
                    transition_style=transition_style,
                    transition_duration=transition_duration,
                    tiling_enabled=bool(entry.tiling_enabled),
                    tiling_gap=entry.tiling_gap,
                    tiling_padding=entry.tiling_padding,
                    tiling_avoid_task_panel=entry.tiling_avoid_task_panel,
                    tiling_center_on_failure=entry.tiling_center_on_failure,
                    tiling_relayout=bool(entry.tiling_relayout),
                    make_initial=make_initial,
                )
            )
            continue

        if len(entry) == 2:
            name, pretty_name = entry
            transition_style = default_transition_style
            transition_duration = default_transition_duration
        elif len(entry) == 3:
            name, pretty_name, transition_style = entry
            transition_duration = default_transition_duration
        elif len(entry) == 4:
            name, pretty_name, transition_style, transition_duration = entry
        else:
            raise ValueError("Scene setup tuple entries must contain 2-4 values")

        specs.append(
            SceneSetupSpec(
                name=str(name),
                pretty_name=None if pretty_name is None else str(pretty_name),
                transition_style=transition_style,
                transition_duration=transition_duration,
                make_initial=bool(initial_scene_name is not None and str(name) == str(initial_scene_name)),
            )
        )
    return tuple(specs)


def build_runtime_scene_specs(
    entries: Sequence[RuntimeSceneBindingSpec | RuntimeSceneSpec | str | tuple],
    *,
    pristine_asset: str | None = None,
    bind_escape_to_exit: bool = False,
    prewarm: bool = False,
) -> tuple[RuntimeSceneSpec, ...]:
    """Build RuntimeSceneSpec values from shorthand scene names or tuples.

    Supported tuple forms:
    - ``(scene_name, pristine_asset)``
    - ``(scene_name, pristine_asset, bind_escape_to_exit)``
    - ``(scene_name, pristine_asset, bind_escape_to_exit, prewarm)``
    """
    specs: list[RuntimeSceneSpec] = []
    for entry in entries:
        if isinstance(entry, RuntimeSceneSpec):
            specs.append(entry)
            continue
        if isinstance(entry, RuntimeSceneBindingSpec):
            specs.append(
                RuntimeSceneSpec(
                    scene_name=str(entry.scene_name),
                    pristine_asset=entry.pristine_asset,
                    bind_escape_to_exit=bool(entry.bind_escape_to_exit),
                    prewarm=bool(entry.prewarm),
                )
            )
            continue
        if isinstance(entry, str):
            specs.append(
                RuntimeSceneSpec(
                    scene_name=str(entry),
                    pristine_asset=pristine_asset,
                    bind_escape_to_exit=bool(bind_escape_to_exit),
                    prewarm=bool(prewarm),
                )
            )
            continue

        if len(entry) == 2:
            scene_name, scene_asset = entry
            scene_bind_escape = bind_escape_to_exit
            scene_prewarm = prewarm
        elif len(entry) == 3:
            scene_name, scene_asset, scene_bind_escape = entry
            scene_prewarm = prewarm
        elif len(entry) == 4:
            scene_name, scene_asset, scene_bind_escape, scene_prewarm = entry
        else:
            raise ValueError("Runtime scene tuple entries must contain 2-4 values")

        specs.append(
            RuntimeSceneSpec(
                scene_name=str(scene_name),
                pristine_asset=None if scene_asset is None else str(scene_asset),
                bind_escape_to_exit=bool(scene_bind_escape),
                prewarm=bool(scene_prewarm),
            )
        )
    return tuple(specs)


def build_scene_root_specs(entries: Sequence[SceneRootBindingSpec | SceneRootSpec | tuple[str, str] | tuple[str, str, bool]]) -> tuple[SceneRootSpec, ...]:
    """Build SceneRootSpec values from shorthand tuples or binding specs."""
    specs: list[SceneRootSpec] = []
    for entry in entries:
        if isinstance(entry, SceneRootSpec):
            specs.append(entry)
            continue
        if isinstance(entry, SceneRootBindingSpec):
            specs.append(
                SceneRootSpec(
                    scene_name=str(entry.scene_name),
                    control_id=str(entry.control_id),
                    draw_background=bool(entry.draw_background),
                )
            )
            continue
        if len(entry) == 2:
            scene_name, control_id = entry
            draw_background = False
        elif len(entry) == 3:
            scene_name, control_id, draw_background = entry
        else:
            raise ValueError("Scene root tuple entries must contain 2-3 values")
        specs.append(
            SceneRootSpec(
                scene_name=str(scene_name),
                control_id=str(control_id),
                draw_background=bool(draw_background),
            )
        )
    return tuple(specs)


def build_cursor_specs(
    entries: Sequence[CursorBindingSpec | CursorSpec | tuple[str, str] | tuple[str, str, tuple[int, int]]],
    *,
    default_hotspot: tuple[int, int] = (0, 0),
) -> tuple[CursorSpec, ...]:
    """Build CursorSpec values from shorthand tuples or CursorBindingSpec entries."""
    specs: list[CursorSpec] = []
    for entry in entries:
        if isinstance(entry, CursorSpec):
            specs.append(entry)
            continue
        if isinstance(entry, CursorBindingSpec):
            specs.append(
                CursorSpec(
                    name=str(entry.name),
                    path=str(entry.path),
                    hotspot=(int(entry.hotspot[0]), int(entry.hotspot[1])),
                )
            )
            continue
        if len(entry) == 2:
            name, path = entry
            hotspot = default_hotspot
        elif len(entry) == 3:
            name, path, hotspot = entry
        else:
            raise ValueError("Cursor tuple entries must contain 2-3 values")
        specs.append(
            CursorSpec(
                name=str(name),
                path=str(path),
                hotspot=(int(hotspot[0]), int(hotspot[1])),
            )
        )
    return tuple(specs)


def build_font_role_specs(
    entries: Sequence[FontRoleBindingSpec | tuple[str, int, str] | tuple[str, int, str, bool, bool] | Mapping[str, Mapping[str, object]]],
) -> tuple[dict, ...]:
    """Build ``HostApplicationConfig.font_role_specs`` from compact role entries.

    The return shape matches what ``setup_standard_font_roles(..., *role_specs)``
    expects: a tuple of role-mapping dict blocks.
    """
    role_map: dict[str, dict[str, object]] = {}
    passthrough_blocks: list[dict] = []

    for entry in entries:
        if isinstance(entry, Mapping):
            passthrough_blocks.append({str(k): dict(v) for k, v in entry.items()})
            continue
        if isinstance(entry, FontRoleBindingSpec):
            role = str(entry.role)
            role_map[role] = {
                "size": int(entry.size),
                "font": str(entry.font),
                "bold": bool(entry.bold),
                "italic": bool(entry.italic),
            }
            continue
        if len(entry) == 3:
            role, size, font = entry
            bold = False
            italic = False
        elif len(entry) == 5:
            role, size, font, bold, italic = entry
        else:
            raise ValueError("Font role tuple entries must contain 3 or 5 values")
        role_map[str(role)] = {
            "size": int(size),
            "font": str(font),
            "bold": bool(bold),
            "italic": bool(italic),
        }

    blocks: list[dict] = []
    if role_map:
        blocks.append(role_map)
    blocks.extend(passthrough_blocks)
    return tuple(blocks)


def build_scene_bundle_specs(
    entries: Sequence[
        SceneBundleBindingSpec
        | SceneSetupSpec
        | RuntimeSceneSpec
        | SceneRootSpec
        | ActionSpec
    ],
    *,
    default_transition_style: object | None = None,
    default_transition_duration: float | None = None,
    default_nav_category: str = "Scenes",
    initial_scene_name: str | None = None,
) -> tuple[tuple[SceneSetupSpec, ...], tuple[RuntimeSceneSpec, ...], tuple[SceneRootSpec, ...], tuple[ActionSpec, ...]]:
    """Build scene setup/runtime/root/action collections from scene bundles.

    Supports mixed input entries so callers can combine bundle shorthand with
    passthrough prebuilt spec instances.
    """
    scene_specs: list[SceneSetupSpec] = []
    runtime_specs: list[RuntimeSceneSpec] = []
    root_specs: list[SceneRootSpec] = []
    action_specs: list[ActionSpec] = []

    for entry in entries:
        if isinstance(entry, SceneSetupSpec):
            scene_specs.append(entry)
            continue
        if isinstance(entry, RuntimeSceneSpec):
            runtime_specs.append(entry)
            continue
        if isinstance(entry, SceneRootSpec):
            root_specs.append(entry)
            continue
        if isinstance(entry, ActionSpec):
            action_specs.append(entry)
            continue

        scene_name = str(entry.scene_name)
        if entry.include_scene_setup:
            scene_specs.append(
                SceneSetupSpec(
                    name=scene_name,
                    pretty_name=entry.pretty_name,
                    transition_style=entry.transition_style if entry.transition_style is not None else default_transition_style,
                    transition_duration=entry.transition_duration if entry.transition_duration is not None else default_transition_duration,
                    tiling_enabled=bool(entry.tiling_enabled),
                    tiling_gap=entry.tiling_gap,
                    tiling_padding=entry.tiling_padding,
                    tiling_avoid_task_panel=entry.tiling_avoid_task_panel,
                    tiling_center_on_failure=entry.tiling_center_on_failure,
                    tiling_relayout=bool(entry.tiling_relayout),
                    make_initial=bool(entry.make_initial or (initial_scene_name is not None and scene_name == str(initial_scene_name))),
                )
            )

        if entry.include_runtime_scene:
            runtime_specs.append(
                RuntimeSceneSpec(
                    scene_name=scene_name,
                    pristine_asset=entry.pristine_asset,
                    bind_escape_to_exit=bool(entry.bind_escape_to_exit),
                    prewarm=bool(entry.prewarm),
                )
            )

        if entry.include_scene_root:
            root_id = entry.scene_root_id or f"{scene_name}_root"
            root_specs.append(
                SceneRootSpec(
                    scene_name=scene_name,
                    control_id=str(root_id),
                    draw_background=bool(entry.scene_root_draw_background),
                )
            )

        if entry.include_nav_action:
            action_specs.append(
                ActionSpec(
                    action_id=str(entry.nav_action_id or f"nav_{scene_name}"),
                    label=str(entry.nav_label or f"Go to {entry.pretty_name or scene_name.replace('_', ' ').title()}"),
                    kind="scene_nav",
                    target=scene_name,
                    category=None if entry.nav_category is None else str(entry.nav_category or default_nav_category),
                )
            )

    return (
        tuple(scene_specs),
        tuple(runtime_specs),
        tuple(root_specs),
        tuple(action_specs),
    )


def build_host_application_config(
    config: HostApplicationBindingSpec | HostApplicationConfig,
) -> HostApplicationConfig:
    """Build HostApplicationConfig from one host-level binding spec.

    Accepts an already built HostApplicationConfig as passthrough for
    advanced workflows that still want a unified call site.
    """
    if isinstance(config, HostApplicationConfig):
        return config

    telemetry = config.telemetry if config.telemetry is not None else TelemetryConfig()

    bundle_scene_specs, bundle_runtime_specs, bundle_root_specs, bundle_action_specs = build_scene_bundle_specs(
        config.scene_bundle_entries,
        default_transition_style=config.scene_default_transition_style,
        default_transition_duration=config.scene_default_transition_duration,
        initial_scene_name=str(config.initial_scene_name),
    )

    explicit_scene_specs = build_scene_setup_specs(
        config.scene_entries,
        default_transition_style=config.scene_default_transition_style,
        default_transition_duration=config.scene_default_transition_duration,
        initial_scene_name=str(config.initial_scene_name),
    )
    explicit_runtime_specs = build_runtime_scene_specs(
        config.runtime_scene_entries,
        pristine_asset=config.runtime_default_pristine_asset,
        bind_escape_to_exit=bool(config.runtime_default_bind_escape_to_exit),
        prewarm=bool(config.runtime_default_prewarm),
    )
    explicit_action_specs = build_action_specs(config.action_entries)
    explicit_root_specs = build_scene_root_specs(config.scene_root_entries)

    bundle_feature_specs, bundle_window_specs = build_feature_window_bundle_specs(
        config.feature_window_bundle_entries
    )

    scene_specs = tuple((*bundle_scene_specs, *explicit_scene_specs))
    runtime_scene_specs = tuple((*bundle_runtime_specs, *explicit_runtime_specs))
    action_specs = tuple((*bundle_action_specs, *explicit_action_specs))
    scene_roots = tuple((*bundle_root_specs, *explicit_root_specs))
    feature_specs = tuple((*build_feature_specs(config.feature_entries), *bundle_feature_specs))
    window_specs = tuple((*bundle_window_specs, *build_window_toggle_specs(config.window_entries)))

    return HostApplicationConfig(
        display_size=(int(config.display_size[0]), int(config.display_size[1])),
        window_title=str(config.window_title),
        fonts=dict(config.fonts),
        font_role_specs=build_font_role_specs(config.font_role_entries),
        cursors=build_cursor_specs(config.cursor_entries),
        scene_specs=scene_specs,
        feature_specs=feature_specs,
        window_specs=window_specs,
        runtime_scene_specs=runtime_scene_specs,
        action_specs=action_specs,
        static_accessibility_specs=build_static_accessibility_specs(
            config.static_accessibility_entries,
            role=str(config.static_accessibility_role),
        ),
        initial_scene_name=str(config.initial_scene_name),
        scene_roots=scene_roots,
        telemetry=telemetry,
        target_fps=int(config.target_fps),
        palette_spec=config.palette_spec,
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


def setup_feature_presenter_tabs_from_window_content(
    presenter,
    *,
    window,
    spec: TabbedPresenterSpec,
    tab_specs: Sequence[TabBuilderSpec],
    on_change,
    tab_manager,
    feature,
    host,
    on_activate_callbacks: Sequence[tuple[str, Callable[[], object]]] = (),
):
    """Compute tab layout from ``window.content_rect`` and wire presenter tabs.

    This wraps ``compute_tabbed_window_layout`` and ``setup_feature_presenter_tabs``
    so presenter ``on_create`` implementations can stay declarative and avoid
    repeated geometry and callback boilerplate.
    """
    tab_rect, tab_content_rect = compute_tabbed_window_layout(
        window.content_rect(),
        tab_height=int(spec.tab_height),
        tab_rows=int(spec.tab_rows),
        padding=int(spec.padding),
        min_content_height=int(spec.min_content_height),
    )
    tab_control = setup_feature_presenter_tabs(
        presenter,
        control_id=str(spec.control_id),
        tab_rect=tab_rect,
        tab_specs=tab_specs,
        selected_key=str(spec.selected_key),
        on_change=on_change,
        tab_manager=tab_manager,
        feature=feature,
        host=host,
        tab_content_rect=tab_content_rect,
    )
    for tab_key, callback in on_activate_callbacks:
        tab_manager.on_activate(str(tab_key), callback)
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
