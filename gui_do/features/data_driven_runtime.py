"""Generalized data-driven runtime and feature wiring helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence, Mapping
import inspect

import pygame
from pygame import Rect

from ..controls.chrome.menu_bar_control import MenuEntry, MenuStripControl, SceneMenuOptions, WindowMenuOptions
from ..controls.chrome.window_control import WindowControl
from ..controls.data.tab_control import TabControl
from ..controls.input.button_control import ButtonControl
from ..controls.display.label_control import LabelControl
from ..layout.flex_layout import FlexLayout
from ..text.localization import LocaleRegistry
from ..app.service_scope import ServiceScope
from .feature_lifecycle import (
    FeatureWindowPresentationModel,
    SceneSetupSpec,
    WindowEffectsSpec,
    ScenePresentationModel,
    apply_scene_setup_specs,
    create_anchored_feature_window,
    resolve_scene_selection_callback,
    setup_standard_font_roles,
)
from .runtime_helpers import (
    apply_accessibility_sequence as _apply_accessibility_sequence,
    apply_accessibility_sequence_from_attrs as _apply_accessibility_sequence_from_attrs,
    initialize_locale_registry as _initialize_locale_registry,
    bind_input_map_actions as _bind_input_map_actions,
    register_descriptors as _register_descriptors,
    resolve_canvas_local_point as _resolve_canvas_local_point,
    apply_runtime_scene_pristine_assets as _apply_runtime_scene_pristine_assets,
    bind_runtime_scene_exit_keys as _bind_runtime_scene_exit_keys,
    prewarm_runtime_scenes as _prewarm_runtime_scenes,
)
from .runtime_models import (
    ActiveTabUpdateRouter,
    HostApplicationConfig,
    NotificationSpec,
    TabbedPresenterSpec,
    TelemetryConfig,
    build_notification_center,
)
from .runtime_facilities import FeatureOperationBus, FeatureRuntimeScope
from .runtime_systems import (
    FeatureDependencySpec,
    ExecutionContextSpec,
    WorkloadBudgetClassSpec,
    WorkloadBudgetSpec,
    CheckpointDomainSpec,
    CheckpointSpec,
    SagaStepSpec,
    SagaSpec,
    ReactiveSourceSpec,
    ReactiveNodeSpec,
    ReactiveGraphSpec,
    MigrationStepSpec,
    MigrationTargetSpec,
    ContractMigrationSpec,
    RuntimePolicySpec,
    EffectBindingSpec,
    EventPipelineStageSpec,
    EventPipelineSpec,
    DurableOperationBindingSpec,
    DurableOperationQueueSpec,
    DurableQueueRecord,
    CapabilityProviderSpec,
    CapabilityRequirementSpec,
    ProjectionNodeSpec,
    ProjectionSpec,
    PolicyDecision,
    WorkflowStepSpec,
    WorkflowSpec,
    RecomputeNodeSpec,
    QoSPolicySpec,
    HealthProbeSpec,
    ReplaySpec,
    ReplacePolicySpec,
    WorkflowCoordinator,
    RuntimePolicyEngine,
    EffectLifetimeOrchestrator,
    EventPipelineRuntime,
    DurableOperationQueueRuntime,
    CapabilityContractRuntime,
    ProjectionRuntime,
    RecomputeOrchestrator,
    QoSPolicyRuntime,
    FeatureHealthRuntime,
    RuntimeReplayHarness,
    FeatureHotSwapManager,
    ExecutionContextRuntime,
    WorkloadBudgetBrokerRuntime,
    CheckpointRecoveryRuntime,
    SagaCompensationRuntime,
    ReactiveDependencyGraphRuntime,
    ContractMigrationRuntime,
    build_routed_runtime_systems,
)
from .runtime_registration_helpers import (
    instantiate_features_from_specs as _instantiate_features_from_specs,
    register_features_from_specs as _register_features_from_specs,
    register_window_presentation_specs as _register_window_presentation_specs,
    register_window_tab_builders as _register_window_tab_builders,
)
from .runtime_routed_helpers import (
    configure_routed_feature_runtime as _configure_routed_feature_runtime,
)
from .runtime_window_toggle_helpers import (
    add_task_panel_window_toggle_group as _add_task_panel_window_toggle_group,
    add_window_toggle_task_panel_controls as _add_window_toggle_task_panel_controls,
    apply_window_toggle_accessibility as _apply_window_toggle_accessibility,
    collect_window_toggle_controls as _collect_window_toggle_controls,
    register_window_toggle_tooltips as _register_window_toggle_tooltips,
    sorted_window_bindings as _sorted_window_bindings,
)
from .runtime_task_panel_helpers import (
    add_right_anchored_task_panel_button as _add_right_anchored_task_panel_button,
    add_task_panel_button as _add_task_panel_button,
    add_task_panel_buttons as _add_task_panel_buttons,
)
from .runtime_tab_helpers import (
    compute_tabbed_window_layout as _compute_tabbed_window_layout,
    create_feature_presented_window as _create_feature_presented_window,
    create_presented_anchored_window as _create_presented_anchored_window,
    create_presented_window_from_spec as _create_presented_window_from_spec,
    create_tab_control_from_specs as _create_tab_control_from_specs,
    register_tab_update_handlers as _register_tab_update_handlers,
    register_window_tab_builder_specs as _register_window_tab_builder_specs,
    setup_feature_presenter_tabs as _setup_feature_presenter_tabs,
    setup_feature_presenter_tabs_from_window_content as _setup_feature_presenter_tabs_from_window_content,
)
from .runtime_spec_factories import (
    make_exit_action as _make_exit_action,
    make_palette_toggle_action as _make_palette_toggle_action,
    make_scene_nav_action as _make_scene_nav_action,
    make_static_accessibility_spec as _make_static_accessibility_spec,
    make_window_toggle_spec as _make_window_toggle_spec,
)
from .runtime_spec_builders import (
    build_action_specs as _build_action_specs,
    build_feature_specs as _build_feature_specs,
    build_feature_window_bundle_specs as _build_feature_window_bundle_specs,
    build_scene_nav_actions as _build_scene_nav_actions,
    build_static_accessibility_specs as _build_static_accessibility_specs,
    build_window_toggle_specs as _build_window_toggle_specs,
)
from .runtime_config_builders import (
    build_cursor_specs as _build_cursor_specs,
    build_font_role_specs as _build_font_role_specs,
    build_host_application_config as _build_host_application_config,
    build_runtime_scene_specs as _build_runtime_scene_specs,
    build_scene_bundle_specs as _build_scene_bundle_specs,
    build_scene_root_specs as _build_scene_root_specs,
    build_scene_setup_specs as _build_scene_setup_specs,
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
class WindowTitlebarControlsSpec:
    """Declarative titlebar button opt-in settings for WindowControl."""

    include_window_lower_button: bool = True
    include_window_hide_image_button: bool = True


@dataclass(frozen=True)
class WindowSpec:
    """Declarative descriptor for a feature window presentation binding."""
    key: str
    feature_attribute_name: str
    toggle_attribute_name: str
    action_name: str
    action_label: str
    task_panel_toggle_button_id: str
    task_panel_label: str
    task_panel_style: str
    task_panel_slot_index: int | None
    accessibility_label: str
    window_effects: WindowEffectsSpec | Mapping[str, bool] = field(default_factory=WindowEffectsSpec)
    window_management_opt_in: bool = True
    titlebar_controls: WindowTitlebarControlsSpec | None = None


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
    kind: str           # "exit" | "scene_nav" | "palette_toggle"
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
    window_management_opt_in: bool = True
    titlebar_controls: WindowTitlebarControlsSpec | None = None


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
    label: str
    on_click: Callable[[], object]
    slot_index: int | None = None
    style: str = "angle"


@dataclass(frozen=True)
class RightAnchoredTaskPanelButtonSpec:
    """Declarative descriptor for a task-panel button anchored to the right edge."""

    attr_name: str
    control_id: str
    label: str
    on_click: Callable[[], object]
    width: int
    height: int
    top_offset: int
    right_padding: int = 16
    style: str = "angle"
    include_in_task_panel_focus_cycle: bool = True


@dataclass(frozen=True)
class TooltipBindingSpec:
    """Declarative descriptor mapping a target attribute to a tooltip message."""

    control_attr: str
    message: str


@dataclass(frozen=True)
class MenuStripSpec:
    """Declarative descriptor for attaching a unified menu strip.

    If scene_menu_opt_in is False, the scene is opted out of the menu strip. Default is True (opted in).
    """

    control_id: str
    scene_name: str
    scenes_shown: bool = True
    windows_shown: bool = True
    scene_menu_label: str = "Scene"
    window_menu_label: str = "Window"
    scene_menu_insert_index: int = 0
    window_menu_insert_index: int = 1
    scene_menu_mode: str = "add_all"  # add_all | opt_in
    scene_menu_opt_in_scene_names: Sequence[str] = field(default_factory=tuple)
    scene_menu_include_current_scene: bool = False
    static_entries: Sequence[MenuEntry] = field(default_factory=tuple)
    tools_exclude_labels: Sequence[str] = field(default_factory=tuple)
    on_window_toggled: Callable[[object, bool], object] | None = None
    tab_index: int = 0
    accessibility_role: str = "menubar"
    accessibility_label: str = "Menu strip"
    scene_menu_opt_in: bool = True


@dataclass(frozen=True)
class AutoSizedStyledLabelSpec:
    """Declarative descriptor for a styled label that auto-sizes to rendered text."""

    control_id: str
    text: str
    left: int
    top: int
    fallback_size: tuple[int, int]
    style_size: int = 64


@dataclass(frozen=True)
class ActionHotkeySpec:
    """Declarative descriptor for registering one action and optional key binding.

    If handler is None, the framework will resolve the action by name at runtime (for built-in actions).
    """

    action_name: str
    handler: Callable[[object], object] | None = None
    key: int | None = None
    scene_name: str | None = None
    mod: int | None = None
    global_key: bool = False


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
class TaskPanelSlotLayoutSpec:
    """Declarative descriptor for task-panel slot layout."""

    left: int = 16
    top_offset: int = 10
    item_width: int = 110
    item_height: int = 30
    spacing: int = 10
    horizontal: bool = True


@dataclass(frozen=True)
class TaskPanelWindowToggleGroupSpec:
    """Declarative marker for placing automatic window-toggle buttons in the task panel.

    Declare one of these in the scene's task panel setup to opt in to automatic window
    toggle management.  The framework creates one ``ToggleControl`` per registered window
    and places it at the slot index declared by each window's binding spec.

    *start_index* is the lowest slot index that the toggle group may occupy.  Controls
    added before that index (Exit buttons, navigation buttons, etc.) are unaffected.
    Controls added after the last window's slot index are equally unaffected — the group
    and other task panel items can freely coexist at any index values.

    Declaring this spec is optional.  Omitting it means no automatic window toggles
    appear in the task panel for this scene.

    Example — task panel with an Exit button at slot 0, window toggles starting at
    slot 1 (System at 1, Life at 3), and a Showcase navigation button at slot 2::

        ensure_scene_task_panel(host, SceneTaskPanelSpec(...))
        add_task_panel_buttons(host, task_panel, layout, [
            TaskPanelButtonSpec(attr_name="exit_button", slot_index=0, ...),
            TaskPanelButtonSpec(attr_name="showcase_button", slot_index=2, ...),
        ])
        add_task_panel_window_toggle_group(
            host, task_panel, layout, host.window_presentation,
            TaskPanelWindowToggleGroupSpec(start_index=1),
        )
    """

    start_index: int = 1


@dataclass(frozen=True)
class PaletteInputBindSpec:
    """Declarative spec for a command palette input bind (toggle or action).

    Defines how one palette operation is triggered via keyboard, pointer button, or both.
    """

    action_name: str
    key: int | None = None
    pointer_button: int | None = None


@dataclass(frozen=True)
class SceneCommandPaletteSpec:
    """Declarative spec for command palette UX bindings.

    This spec models two independent input binds:
    - *toggle*: opens/closes the command palette itself.
    - *action*: while palette is open, toggles visibility of window entries
      under the pointer without dismissing the palette.

    Each bind is a PaletteInputBindSpec that specifies the action name, optional key,
    and optional pointer button. *scene_name* scopes all binds to one scene; pass
    ``None`` for global scope.
    """

    scene_name: str | None = None
    toggle: PaletteInputBindSpec = field(default_factory=lambda: PaletteInputBindSpec(action_name="command_palette_toggle"))
    action: PaletteInputBindSpec = field(default_factory=lambda: PaletteInputBindSpec(action_name="command_palette_action"))


@dataclass(frozen=True)
class TaskPanelSceneNavButtonSpec:
    """Declarative descriptor for a scene-navigation button on a task panel."""

    attr_name: str | None = None
    control_id: str = "scene_return"
    slot_index: int | None = None
    label: str = "Return"
    target_scene: str = "main"
    go_to_attr: str | None = None
    style: str = "angle"
    accessibility_role: str = "button"
    accessibility_label: str = "Return"
    tab_index: int = -1


@dataclass(frozen=True)
class SceneTaskPanelItemsResult:
    """Created controls from one scene task-panel composition pass."""

    scene_nav_buttons: tuple[object, ...] = field(default_factory=tuple)
    window_toggle_controls: tuple[tuple[object, object], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EventSubscriptionSpec:
    """Declarative descriptor for a feature-managed event-bus subscription."""

    attr_name: str
    topic: str
    handler: Callable[[object], object]
    scope: str | None = None


@dataclass(frozen=True)
class ServiceBindingSpec:
    """Declarative descriptor for a service published into a feature runtime scope."""

    attr_name: str
    key: object
    factory: Callable[..., object]
    owned: bool = True


@dataclass(frozen=True)
class ServiceConsumerSpec:
    """Declarative descriptor for a service resolved from a feature runtime scope."""

    attr_name: str
    key: object
    required: bool = True


@dataclass(frozen=True)
class StoreSubscriptionSpec:
    """Declarative descriptor for subscribing to one AppStateStore key."""

    state_key: str
    handler: Callable[[object], object]
    store_attr_name: str = "state_store"
    service_key: object | None = None
    invoke_immediately: bool = False


@dataclass(frozen=True)
class StoreSelectorSpec:
    """Declarative descriptor for selector-backed AppStateStore observation."""

    selector: Callable[[Mapping[str, object]], object]
    handler: Callable[[object], object]
    store_attr_name: str = "state_store"
    service_key: object | None = None
    depends_on: Sequence[str] = field(default_factory=tuple)
    invoke_immediately: bool = False
    attr_name: str | None = None


@dataclass(frozen=True)
class ObservableEffectSpec:
    """Declarative descriptor for subscribing to any observable value."""

    handler: Callable[[object], object]
    observable_attr_name: str | None = None
    service_key: object | None = None
    observable_factory: Callable[..., object] | None = None
    invoke_immediately: bool = False


@dataclass(frozen=True)
class SignalEffectSpec:
    """Declarative descriptor for connecting one signal-like source."""

    handler: Callable[[object], object]
    signal_attr_name: str | None = None
    service_key: object | None = None
    signal_factory: Callable[..., object] | None = None
    once: bool = False


@dataclass(frozen=True)
class FailurePolicySpec:
    """Declarative descriptor for operation retry and timeout policy."""

    name: str
    retries: int = 0
    retry_delay_seconds: float = 0.0
    timeout_seconds: float | None = None
    publish_topic: str | None = None
    publish_scope: str | None = None


@dataclass(frozen=True)
class FeatureOperationSpec:
    """Declarative descriptor for one registered operation-bus handler."""

    name: str
    handler: Callable[..., object]
    failure_policy: str | None = None


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
    toggle_global_key: bool = False
    manual_shortcut_lines: Sequence[str] = field(default_factory=tuple)
    manual_section_title: str = "Keyboard"
    prepend_manual_shortcuts: bool = False
    manual_shortcuts_only: bool = False
    exclude_section_titles: Sequence[str] = field(default_factory=tuple)
    exclude_entry_labels: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class TaskPanelFocusToggleSpec:
    """Declarative descriptor for registering a scene task-panel focus toggle action."""

    action_name: str
    scene_name: str
    key: int


@dataclass(frozen=True)
class GlobalPointerActionSpec:
    """Declarative descriptor for a global pointer button -> action binding.

    The binding is routed before overlay, focus, active-window, feature, and scene
    dispatch, so it behaves like global key bindings (always first).
    """

    action_name: str
    button: int
    scene_name: str | None = None


@dataclass(frozen=True)
class RoutedRuntimeSpec:
    """Declarative descriptor for standard routed-feature runtime wiring."""

    scene_name: str = "main"
    scheduler_attr_name: str = "scheduler"
    scheduler_dispatch_limit: int | None = None
    runtime_scope_attr_name: str = "runtime_scope"
    logic_bindings: Sequence[LogicBindingSpec] = field(default_factory=tuple)
    service_bindings: Sequence[ServiceBindingSpec] = field(default_factory=tuple)
    service_consumers: Sequence[ServiceConsumerSpec] = field(default_factory=tuple)
    store_subscriptions: Sequence[StoreSubscriptionSpec] = field(default_factory=tuple)
    store_selectors: Sequence[StoreSelectorSpec] = field(default_factory=tuple)
    observable_effects: Sequence[ObservableEffectSpec] = field(default_factory=tuple)
    signal_effects: Sequence[SignalEffectSpec] = field(default_factory=tuple)
    operation_bus_attr_name: str | None = None
    operation_service_key: object | None = None
    failure_policies: Sequence[FailurePolicySpec] = field(default_factory=tuple)
    operations: Sequence[FeatureOperationSpec] = field(default_factory=tuple)
    action_hotkeys: Sequence[ActionHotkeySpec] = field(default_factory=tuple)
    control_key_bindings: Sequence[ControlKeyBindingSpec] = field(default_factory=tuple)
    event_subscriptions: Sequence[EventSubscriptionSpec] = field(default_factory=tuple)
    shortcut_overlays: Sequence[ShortcutOverlaySpec] = field(default_factory=tuple)
    task_panel_focus_toggles: Sequence[TaskPanelFocusToggleSpec] = field(default_factory=tuple)
    global_pointer_actions: Sequence[GlobalPointerActionSpec] = field(default_factory=tuple)
    feature_dependencies: Sequence[FeatureDependencySpec] = field(default_factory=tuple)
    execution_context_spec: ExecutionContextSpec | None = None
    execution_context_attr_name: str | None = None
    budget_spec: WorkloadBudgetSpec | None = None
    budget_attr_name: str | None = None
    checkpoint_spec: CheckpointSpec | None = None
    checkpoint_attr_name: str | None = None
    saga_specs: Sequence[SagaSpec] = field(default_factory=tuple)
    saga_attr_name: str | None = None
    reactive_graph_spec: ReactiveGraphSpec | None = None
    reactive_graph_attr_name: str | None = None
    migration_spec: ContractMigrationSpec | None = None
    migration_attr_name: str | None = None
    policy_specs: Sequence[RuntimePolicySpec] = field(default_factory=tuple)
    policy_attr_name: str | None = None
    effect_bindings: Sequence[EffectBindingSpec] = field(default_factory=tuple)
    effects_attr_name: str | None = None
    event_pipelines: Sequence[EventPipelineSpec] = field(default_factory=tuple)
    event_pipeline_attr_name: str | None = None
    durable_queue_spec: DurableOperationQueueSpec | None = None
    durable_queue_attr_name: str | None = None
    capability_providers: Sequence[CapabilityProviderSpec] = field(default_factory=tuple)
    capability_requirements: Sequence[CapabilityRequirementSpec] = field(default_factory=tuple)
    capability_attr_name: str | None = None
    projection_spec: ProjectionSpec | None = None
    projection_attr_name: str | None = None
    workflow_specs: Sequence[WorkflowSpec] = field(default_factory=tuple)
    workflow_attr_name: str | None = None
    recompute_nodes: Sequence[RecomputeNodeSpec] = field(default_factory=tuple)
    recompute_attr_name: str | None = None
    qos_policies: Sequence[QoSPolicySpec] = field(default_factory=tuple)
    qos_attr_name: str | None = None
    health_probes: Sequence[HealthProbeSpec] = field(default_factory=tuple)
    health_attr_name: str | None = None
    replay_spec: ReplaySpec | None = None
    replay_attr_name: str | None = None
    replace_policy: ReplacePolicySpec | None = None
    hot_swap_attr_name: str | None = None
    command_palette: "SceneCommandPaletteSpec | None" = None


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

    feature_attribute_name: str
    factory: object  # Callable[[], object]
    window_key: str
    task_panel_slot_index: int | None = None
    task_panel_label: str | None = None
    task_panel_style: str = "round"
    action_label: str | None = None
    action_name: str | None = None
    task_panel_toggle_button_id: str | None = None
    toggle_attribute_name: str | None = None
    accessibility_label: str | None = None
    window_effects: WindowEffectsSpec | Mapping[str, bool] = field(default_factory=WindowEffectsSpec)
    window_management_opt_in: bool = True
    titlebar_controls: WindowTitlebarControlsSpec | None = None



@dataclass(frozen=True)
class WindowToggleBindingSpec:
    """Input descriptor for building a WindowSpec with conventional defaults."""

    key: str
    feature_attribute_name: str
    task_panel_slot_index: int | None = None
    task_panel_label: str | None = None
    task_panel_style: str = "round"
    action_label: str | None = None
    action_name: str | None = None
    task_panel_toggle_button_id: str | None = None
    toggle_attribute_name: str | None = None
    accessibility_label: str | None = None
    window_effects: WindowEffectsSpec | Mapping[str, bool] = field(default_factory=WindowEffectsSpec)
    titlebar_controls: WindowTitlebarControlsSpec | None = None


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

    kind: str  # "exit" | "scene_nav" | "palette_toggle"
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
    emit_scene_setup_spec: bool = True

    pristine_asset: str | None = None
    bind_escape_to_exit: bool = False
    prewarm: bool = False
    emit_runtime_scene_spec: bool = True

    emit_nav_action_spec: bool = False
    nav_action_id: str | None = None
    nav_label: str | None = None
    nav_category: str | None = "Scenes"

    emit_scene_root_spec: bool = False
    scene_root_id: str | None = None
    scene_root_draw_background: bool = False


@dataclass(frozen=True)
class PaletteBindingSpec:
    """User-side declaration for command palette behavior.

    gui_do provides the command palette as a facility; this spec lets user code
    opt in/out of built-in Scene and Window entry groups independently, choose
    where those groups appear relative to custom entries, and provide custom
    entries via a user-defined callable.

    ``custom_entries_provider`` may accept either zero arguments or the active
    ``GuiApplication`` as one argument and should return a sequence of
    ``CommandEntry`` values.
    """

    enable_builtin_entries: bool = True
    include_scene_entries: bool = True
    include_window_entries: bool = True
    group_order: Sequence[str] = ("scenes", "windows", "custom")
    custom_entries_provider: Callable[..., Sequence[object]] | None = None
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
class PresenterLabelSpec:
    """Declarative descriptor for a label placed by a tab-builder helper.

    Used with :meth:`~TabLayoutContext.add_label` via the ``_add_tab_labels_from_specs``
    helper pattern.  When *advance* is ``None`` the context's default advance
    (``height + 8``) is used.
    """

    control_id: str
    height: int
    text: str
    advance: int | None = None
    width: int | None = None
    x_offset: int = 0


@dataclass(frozen=True)
class PresenterButtonSpec:
    """Declarative descriptor for a button placed by a tab-builder helper.

    *handler_attr* is the name of the method on the presenter instance to
    call when the button is clicked.  Resolve it with ``getattr(self, spec.handler_attr)``
    before passing to :meth:`~TabLayoutContext.add_button`.
    """

    control_id: str
    width: int
    height: int
    text: str
    handler_attr: str
    advance: int | None = None
    x_offset: int = 0
    style: str | None = None


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
    palette_spec = getattr(config, "palette_spec", None)
    host._palette_spec = palette_spec
    host._palette_manager = None
    wants_palette = bool(
        palette_spec is not None
        or any(str(getattr(spec, "kind", "")) == "palette_toggle" for spec in config.action_specs)
    )
    if wants_palette:
        _ensure_command_palette_manager(host, palette_requested=True)
    declare_host_actions(host, config.action_specs)

    # 13 – Build features, sync visibility, pristine assets, standard actions
    host.app.build_features(host)
    host.window_presentation.sync_initial_visibility(visible=False)
    apply_runtime_scene_pristine_assets(host.app, config.runtime_scene_specs)
    # Register window-presentation toggle handlers on the app-level action dispatcher
    # so they are callable by name (e.g. from the command palette selection path).
    if host.app.actions is not None:
        for _name, _cb in host.window_presentation.action_callbacks().items():
            host.app.actions.register_action(_name, lambda _ev, _f=_cb: (_f() or True))
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
    key choice (e.g. F5 for palette_toggle) is honoured without any hidden auto-binding.
    """
    r = host.action_registry
    app_actions = getattr(host.app, "actions", None)
    for spec in action_specs:
        handler = _build_standard_action_handler(host, spec)
        if spec.category is None:
            r.declare(spec.action_id, spec.label, handler)
        else:
            r.declare(spec.action_id, spec.label, handler, category=spec.category)
        if app_actions is not None:
            app_actions.register_action(str(spec.action_id), lambda _ev, _h=handler: _h(None, _ev))
        if spec.key is not None and app_actions is not None:
            app_actions.bind_key(int(spec.key), str(spec.action_id))
    host.window_presentation.declare_actions(r, category="Windows")


def _build_standard_action_handler(host, spec):
    """Return a callable action handler for a standard ActionSpec kind."""
    if spec.kind == "exit":
        return lambda _ctx, _ev: (setattr(host.app, "running", False) or True)
    if spec.kind == "scene_nav":
        target = str(spec.target)
        return lambda _ctx, _ev, _t=target: (host.scene_transitions.go(_t) or True)
    if spec.kind == "palette_toggle":
        def _toggle_palette(_ctx, _ev):
            palette_manager = _ensure_command_palette_manager(host, palette_requested=True)
            if palette_manager is None:
                return False
            if palette_manager.is_open:
                palette_manager.hide()
            else:
                palette_manager.show(host.app)
            return True

        return _toggle_palette
    raise ValueError(f"Unsupported action kind: {spec.kind!r}")


def _ensure_command_palette_manager(host, *, palette_requested: bool = False):
    """Return a host palette manager, creating/configuring it lazily when needed."""
    palette_manager = getattr(host, "_palette_manager", None)
    if palette_manager is not None:
        return palette_manager

    if not bool(palette_requested):
        return None

    app = getattr(host, "app", None)
    if app is None:
        return None

    from ..overlays.command_palette_manager import CommandPaletteManager

    palette_manager = CommandPaletteManager(app.overlay, app)
    setattr(host, "_palette_manager", palette_manager)

    palette_spec = getattr(host, "_palette_spec", None)
    if palette_spec is not None and bool(getattr(palette_spec, "enable_builtin_entries", False)):
        scene_transitions = getattr(host, "scene_transitions", None)
        on_scene_selected = getattr(scene_transitions, "go", None) if scene_transitions is not None else None
        window_presentation = None
        if bool(getattr(palette_spec, "connect_window_presentation", False)):
            window_presentation = getattr(host, "window_presentation", None)
        palette_manager.configure_builtin_entry_groups(
            app,
            on_scene_selected=on_scene_selected,
            window_presentation=window_presentation,
            include_scene_entries=bool(getattr(palette_spec, "include_scene_entries", True)),
            include_window_entries=bool(getattr(palette_spec, "include_window_entries", True)),
            group_order=tuple(getattr(palette_spec, "group_order", ("scenes", "windows", "custom"))),
            custom_entries_provider=getattr(palette_spec, "custom_entries_provider", None),
        )
    return palette_manager


def build_host_main_tab_order(host, window_toggle_controls) -> list:
    """Return the main-scene controls in declarative accessibility order.

    Keyboard focus order follows visual slot_index order, ensuring that tabbing
    through controls matches their visual layout in the task panel. This maintains
    accessibility best practices where focus order aligns with visual presentation.

    Args:
        host: The host application instance.
        window_toggle_controls: Sequence of (WindowSpec, control) tuples.

    Returns:
        Ordered list of controls for accessibility declaration, with windows sorted
        by their task_panel_slot_index for coherent focus flow.
    """
    base_controls = [host.exit_button]
    sorted_windows = sorted(
        window_toggle_controls,
        key=lambda pair: (10_000 if pair[0].task_panel_slot_index is None else int(pair[0].task_panel_slot_index)),
    )
    showcase_button = getattr(host, "showcase_button", None)

    # Keep showcase in its visual position: after the first window toggle when
    # at least one toggle exists, otherwise directly after Exit.
    if sorted_windows:
        base_controls.append(sorted_windows[0][1])
        if showcase_button is not None:
            base_controls.append(showcase_button)
        base_controls.extend(c for _b, c in sorted_windows[1:])
        return base_controls

    if showcase_button is not None:
        base_controls.append(showcase_button)
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


def add_standard_menu_strip(
    container,
    host,
    *,
    control_id: str,
    scene_name: str,
    scenes_shown: bool = True,
    windows_shown: bool = True,
    tools_exclude_labels: Sequence[str] = (),
    on_window_toggled=None,
    scene_menu_label: str = "Scene",
    window_menu_label: str = "Window",
    scene_menu_insert_index: int = 0,
    window_menu_insert_index: int = 1,
    scene_menu_mode: str = "add_all",
    scene_menu_opt_in_scene_names: Sequence[str] = (),
    scene_menu_include_current_scene: bool = False,
):
    """Attach a standardized MenuStripControl with optional Scene/Window sections."""
    return add_menu_strip_from_spec(
        container,
        host,
        MenuStripSpec(
            control_id=str(control_id),
            scene_name=str(scene_name),
            scenes_shown=bool(scenes_shown),
            windows_shown=bool(windows_shown),
            scene_menu_label=str(scene_menu_label),
            window_menu_label=str(window_menu_label),
            scene_menu_insert_index=int(scene_menu_insert_index),
            window_menu_insert_index=int(window_menu_insert_index),
            scene_menu_mode=str(scene_menu_mode),
            scene_menu_opt_in_scene_names=tuple(scene_menu_opt_in_scene_names),
            scene_menu_include_current_scene=bool(scene_menu_include_current_scene),
            tools_exclude_labels=tuple(tools_exclude_labels),
            on_window_toggled=on_window_toggled,
        ),
    )


def add_menu_strip_from_spec(container, host, spec: MenuStripSpec):
    """Attach a MenuStripControl from a declarative menu-strip spec."""
    static_entries = list(spec.static_entries)
    static_entries.extend(
        build_tools_menu_entries(
            host,
            exclude_labels=tuple(spec.tools_exclude_labels),
        )
    )

    # Window presentation is optional; when available, enables window opt-in filtering
    window_presentation = getattr(host, "window_presentation", None)

    menu_strip = container.add(
        MenuStripControl(
            str(spec.control_id),
            static_entries,
            app=host.app,
            scene_name=str(spec.scene_name),
            scene_menu=SceneMenuOptions(
                label=str(spec.scene_menu_label),
                insert_index=int(spec.scene_menu_insert_index),
                mode=str(spec.scene_menu_mode),
                opt_in_scene_names=tuple(spec.scene_menu_opt_in_scene_names),
                include_current_scene=bool(spec.scene_menu_include_current_scene),
                shown=bool(spec.scenes_shown),
            ),
            window_menu=WindowMenuOptions(
                label=str(spec.window_menu_label),
                insert_index=int(spec.window_menu_insert_index),
                shown=bool(spec.windows_shown),
            ),
            on_scene_selected=resolve_scene_selection_callback(host),
            on_window_toggled=spec.on_window_toggled,
            window_presentation=window_presentation,
        )
    )
    menu_strip.set_tab_index(int(spec.tab_index))
    menu_strip.set_accessibility(role=str(spec.accessibility_role), label=str(spec.accessibility_label))
    return menu_strip


def apply_accessibility_sequence(items, tab_index_start: int) -> int:
    """Apply sequential tab order and accessibility metadata to controls."""
    return _apply_accessibility_sequence(items, tab_index_start)


def apply_accessibility_sequence_from_attrs(target, specs: Sequence[AccessibilitySequenceSpec], tab_index_start: int) -> int:
    """Apply sequential accessibility/tab-order metadata using target attribute names."""
    return _apply_accessibility_sequence_from_attrs(target, specs, tab_index_start)


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
    """Return feature-window bindings ordered by explicit slot then declaration order."""
    return _sorted_window_bindings(bindings)


def collect_window_toggle_controls(host, window_presentation):
    """Return sorted (binding, control) pairs for all available window toggles on host."""
    return _collect_window_toggle_controls(host, window_presentation)


def apply_window_toggle_accessibility(host, window_presentation, *, role: str = "toggle") -> None:
    """Apply accessibility metadata for all window toggle controls declared by bindings."""
    _apply_window_toggle_accessibility(host, window_presentation, role=role)


def add_window_toggle_task_panel_controls(
    host,
    task_panel,
    app_layout,
    window_presentation,
    *,
    min_slot_index: int | None = None,
    max_slot_index: int | None = None,
    attr_owner=None,
    slot_overrides: Mapping[str, int] | None = None,
):
    """Create window toggle controls on the task panel from declarative bindings.

    Optional slot bounds allow callers to create controls in phases so focus order
    can match visual slot order when mixed with non-toggle controls.
    """
    return _add_window_toggle_task_panel_controls(
        host,
        task_panel,
        app_layout,
        window_presentation,
        min_slot_index=min_slot_index,
        max_slot_index=max_slot_index,
        attr_owner=attr_owner,
        slot_overrides=slot_overrides,
    )


def register_window_toggle_tooltips(tooltip_manager, toggle_controls) -> None:
    """Register standardized window toggle tooltip labels."""
    _register_window_toggle_tooltips(tooltip_manager, toggle_controls)


def add_task_panel_window_toggle_group(
    host,
    task_panel,
    app_layout,
    window_presentation,
    spec: "TaskPanelWindowToggleGroupSpec",
    *,
    attr_owner=None,
    slot_overrides: Mapping[str, int] | None = None,
) -> list:
    """Create window toggle controls from a declarative ``TaskPanelWindowToggleGroupSpec``.

    This is the canonical spec-driven alternative to calling
    ``add_window_toggle_task_panel_controls`` directly.  The *spec* records where the
    group begins; individual window slot positions are controlled by the ``slot_index``
    declared on each ``FeatureWindowBundleBindingSpec`` / ``WindowToggleBindingSpec``.

    Returns the same ``list[(binding, toggle)]`` structure as
    ``add_window_toggle_task_panel_controls`` so callers can pass the result to
    ``register_window_toggle_tooltips`` or accessibility helpers.
    """
    return _add_task_panel_window_toggle_group(
        host,
        task_panel,
        app_layout,
        window_presentation,
        spec,
        attr_owner=attr_owner,
        slot_overrides=slot_overrides,
    )


def _resolve_pointer_activation_pos(event, app):
    pos = getattr(event, "pos", None)
    if isinstance(pos, tuple) and len(pos) == 2:
        return (int(pos[0]), int(pos[1]))
    logical_pointer_pos = getattr(app, "logical_pointer_pos", None)
    if isinstance(logical_pointer_pos, tuple) and len(logical_pointer_pos) == 2:
        return (int(logical_pointer_pos[0]), int(logical_pointer_pos[1]))
    return None


def setup_scene_command_palette_bindings(app, palette_manager, spec: "SceneCommandPaletteSpec") -> None:
    """Register command palette toggle/action binds from one scene-level spec.

    Toggle bind: toggles the overall palette visibility.
    Action bind: consumes the event and, when palette is open, activates the
    entry under pointer while keeping the palette open.
    """
    app_actions = getattr(app, "actions", None)
    if app_actions is None:
        return

    toggle_action_name = str(spec.toggle.action_name)
    if not app_actions.has_action(toggle_action_name):
        def _toggle(_event):
            if palette_manager.is_open:
                palette_manager.hide()
            else:
                palette_manager.show(app)
            return True

        app_actions.register_action(toggle_action_name, _toggle)

    if spec.toggle.key is not None:
        app_actions.bind_global_key(int(spec.toggle.key), toggle_action_name, scene=spec.scene_name)
    if spec.toggle.pointer_button is not None and hasattr(app_actions, "bind_global_pointer_button"):
        app_actions.bind_global_pointer_button(int(spec.toggle.pointer_button), toggle_action_name, scene=spec.scene_name)

    action_action_name = str(spec.action.action_name)
    if not app_actions.has_action(action_action_name):
        def _action(event):
            # Show palette if not already open, and stop—next action will activate entry
            if not palette_manager.is_open:
                palette_manager.show(app)
                return True
            # Activate the pointer-targeted entry while preserving open palette state.
            pos = _resolve_pointer_activation_pos(event, app)
            if pos is not None:
                palette_manager.try_activate_action_at(pos, suppress_followup_select=False)
            return True

        app_actions.register_action(action_action_name, _action)

    if spec.action.key is not None:
        app_actions.bind_global_key(int(spec.action.key), action_action_name, scene=spec.scene_name)
    if spec.action.pointer_button is not None and hasattr(app_actions, "bind_global_pointer_button"):
        app_actions.bind_global_pointer_button(int(spec.action.pointer_button), action_action_name, scene=spec.scene_name)


def initialize_locale_registry(tables, *, initial_locale: str) -> LocaleRegistry:
    """Create a LocaleRegistry, register all tables, and select the initial locale."""
    return _initialize_locale_registry(tables, initial_locale=initial_locale)


def bind_input_map_actions(input_map, bindings, *, mod: int = 0) -> None:
    """Bind multiple (key, action) pairs on an InputMap using a shared modifier."""
    _bind_input_map_actions(input_map, bindings, mod=mod)


def register_descriptors(registry, owner_class, descriptors) -> None:
    """Register a sequence of property descriptors for a given owner class."""
    _register_descriptors(registry, owner_class, descriptors)


def resolve_canvas_local_point(packet, canvas_rect: Rect):
    """Resolve packet coordinates to canvas-local space, if available."""
    return _resolve_canvas_local_point(packet, canvas_rect)


def apply_runtime_scene_pristine_assets(app, runtime_scene_specs) -> None:
    """Apply configured pristine assets to runtime scenes from declarative specs."""
    _apply_runtime_scene_pristine_assets(app, runtime_scene_specs)


def bind_runtime_scene_exit_keys(actions, runtime_scene_specs, *, key, action_name: str = "exit") -> None:
    """Bind a shared exit action key for all runtime scenes that opt in."""
    _bind_runtime_scene_exit_keys(actions, runtime_scene_specs, key=key, action_name=action_name)


def prewarm_runtime_scenes(app, runtime_scene_specs) -> None:
    """Prewarm runtime scenes that opt in via declarative scene specs."""
    _prewarm_runtime_scenes(app, runtime_scene_specs)


def add_task_panel_button(
    task_panel,
    app_layout,
    *,
    control_id: str,
    slot_index: int,
    label: str,
    on_click,
    style: str = "angle",
    assign_tab_index: bool = True,
):
    """Create and add a standard task-panel button positioned by slot index."""
    return _add_task_panel_button(
        task_panel,
        app_layout,
        control_id=control_id,
        slot_index=slot_index,
        label=label,
        on_click=on_click,
        style=style,
        assign_tab_index=assign_tab_index,
    )


def add_task_panel_buttons(host, task_panel, app_layout, specs: Sequence[TaskPanelButtonSpec]):
    """Create and assign host-owned task-panel buttons from declarative specs."""
    _add_task_panel_buttons(
        host,
        task_panel,
        app_layout,
        specs,
        add_task_panel_button_fn=add_task_panel_button,
    )


def add_right_anchored_task_panel_button(host, task_panel, spec: RightAnchoredTaskPanelButtonSpec):
    """Create one task-panel button anchored to the panel's right edge."""
    return _add_right_anchored_task_panel_button(host, task_panel, spec)


def register_tooltip_specs(tooltip_manager, specs) -> None:
    """Register a sequence of tooltip specs as (control, message) pairs."""
    for control, message in specs:
        tooltip_manager.register(control, str(message))


def register_tooltip_attr_specs(target, tooltip_manager, specs: Sequence[TooltipBindingSpec]) -> None:
    """Register tooltips from declarative attribute-based binding specs."""
    for spec in specs:
        control = getattr(target, str(spec.control_attr), None)
        if control is None:
            continue
        tooltip_manager.register(control, str(spec.message))


def _invoke_action_hotkey_handler(handler: Callable[..., object] | None, *, event, feature=None, host=None) -> object:
    """Invoke an action-hotkey handler with compatible arity.

    Supported handler signatures:
    - handler(event)
    - handler(feature, event)
    - handler(feature, host, event)
    - any callable accepting varargs
    """
    if handler is None:
        return False

    try:
        signature = inspect.signature(handler)
    except (TypeError, ValueError):
        return handler(event)

    parameters = tuple(signature.parameters.values())
    if any(parameter.kind is inspect.Parameter.VAR_POSITIONAL for parameter in parameters):
        return handler(feature, host, event)

    positional = [
        parameter
        for parameter in parameters
        if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    argc = len(positional)
    if argc <= 1:
        return handler(event)
    if argc == 2:
        return handler(feature, event)
    return handler(feature, host, event)


def register_action_hotkeys(app_actions, specs: Sequence[ActionHotkeySpec], *, feature=None, host=None) -> None:
    """Register multiple actions and optional key bindings from declarative specs."""
    if app_actions is None:
        return
    for spec in specs:
        action_name = str(spec.action_name)
        required_mod = None if spec.mod is None else int(spec.mod)
        needs_context_wrap = (feature is not None) or (host is not None)

        # If handler is omitted, bind the key to an already-registered action
        # (e.g. built-in actions like tile_now) without overriding it.
        if spec.handler is not None:
            # Preserve legacy identity semantics when no wrapper behavior is needed.
            # Modifier checks are handled by ActionManager binding matching.
            if not needs_context_wrap:
                app_actions.register_action(action_name, spec.handler)
            else:
                def _make_handler(raw_handler):
                    def _handler(event):
                        return bool(
                            _invoke_action_hotkey_handler(
                                raw_handler,
                                event=event,
                                feature=feature,
                                host=host,
                            )
                        )

                    return _handler

                app_actions.register_action(action_name, _make_handler(spec.handler))
        if spec.key is None:
            continue
        if bool(spec.global_key) and hasattr(app_actions, "bind_global_key"):
            if spec.scene_name is None:
                if required_mod is None:
                    app_actions.bind_global_key(int(spec.key), action_name)
                else:
                    app_actions.bind_global_key(int(spec.key), action_name, mod=int(required_mod))
            else:
                if required_mod is None:
                    app_actions.bind_global_key(int(spec.key), action_name, scene=str(spec.scene_name))
                else:
                    app_actions.bind_global_key(
                        int(spec.key),
                        action_name,
                        scene=str(spec.scene_name),
                        mod=int(required_mod),
                    )
            continue
        if spec.scene_name is None:
            if required_mod is None:
                app_actions.bind_key(int(spec.key), action_name)
            else:
                app_actions.bind_key(int(spec.key), action_name, mod=int(required_mod))
        else:
            if required_mod is None:
                app_actions.bind_key(int(spec.key), action_name, scene=str(spec.scene_name))
            else:
                app_actions.bind_key(
                    int(spec.key),
                    action_name,
                    scene=str(spec.scene_name),
                    mod=int(required_mod),
                )


def register_global_pointer_actions(app_actions, specs: Sequence[GlobalPointerActionSpec]) -> None:
    """Register declarative global pointer-button bindings."""
    if app_actions is None:
        return
    bind_global_pointer = getattr(app_actions, "bind_global_pointer_button", None)
    if not callable(bind_global_pointer):
        return
    for spec in specs:
        action_name = str(spec.action_name)
        button = int(spec.button)
        if spec.scene_name is None:
            bind_global_pointer(button, action_name)
        else:
            bind_global_pointer(button, action_name, scene=str(spec.scene_name))


def bind_palette_window_action_bind(host, app_actions, *, action_name: str = "command_palette_action") -> None:
    """Register an action bind that activates entries in an open palette.

    The event is consumed in all cases; if the palette is closed or pointer is not
    over an entry, no side effect is applied.
    """
    if app_actions is None:
        return
    palette_manager = getattr(host, "_palette_manager", None)
    if palette_manager is None:
        return
    app = getattr(host, "app", None)
    if app is None:
        return

    def _handler(event):
        if not palette_manager.is_open:
            return True
        pos = _resolve_pointer_activation_pos(event, app)
        if pos is not None:
            palette_manager.try_activate_action_at(pos, suppress_followup_select=False)
        return True

    app_actions.register_action(action_name, _handler)


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


def create_auto_sized_styled_label(host, spec: AutoSizedStyledLabelSpec, *, scene_name: str | None = None) -> LabelControl:
    """Create a styled label and auto-size it from the per-scene font manager."""
    label = host.app.style_label(
        LabelControl(
            str(spec.control_id),
            Rect(int(spec.left), int(spec.top), int(spec.fallback_size[0]), int(spec.fallback_size[1])),
            str(spec.text),
        ),
        size=int(spec.style_size),
    )
    active_scene = str(scene_name) if scene_name is not None else str(getattr(host.app, "active_scene_name", ""))
    scene_runtimes = getattr(host.app, "_scenes", None)
    scene_runtime = scene_runtimes.get(active_scene) if isinstance(scene_runtimes, dict) else None
    scene_font_manager = getattr(getattr(scene_runtime, "theme", None), "fonts", None)
    if scene_font_manager is not None and scene_font_manager.has_role(label.font_role):
        font = scene_font_manager.font_instance(label.font_role, size=label.font_size)
        label.rect.size = font.text_surface_size(label.text)
    return label


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


class _TaskPanelSlotNode:
    def __init__(self, width: int, height: int) -> None:
        self.rect = Rect(0, 0, int(width), int(height))


class _FlexTaskPanelSlotLayout:
    """Flex-backed adapter exposing slot rectangles for task-panel content."""

    def __init__(self, task_panel, spec: TaskPanelSlotLayoutSpec) -> None:
        self._task_panel = task_panel
        self._left = int(spec.left)
        self._top = int(spec.top_offset)
        self._item_width = int(spec.item_width)
        self._item_height = int(spec.item_height)
        self._spacing = int(spec.spacing)
        self._horizontal = bool(spec.horizontal)
        self._slots: list[_TaskPanelSlotNode] = []

    def _ensure_slot(self, index: int) -> None:
        while len(self._slots) <= int(index):
            self._slots.append(_TaskPanelSlotNode(self._item_width, self._item_height))

        layout = FlexLayout(
            direction="row" if self._horizontal else "column",
            gap=self._spacing,
            padding=0,
        )
        for slot in self._slots:
            layout.add(slot, grow=0, basis=self._item_width if self._horizontal else self._item_height)

        if self._horizontal:
            container = Rect(
                self._left,
                int(self._task_panel.rect.top) + self._top,
                max(1, int(self._task_panel.rect.width) - (self._left * 2)),
                self._item_height,
            )
        else:
            container = Rect(
                self._left,
                int(self._task_panel.rect.top) + self._top,
                self._item_width,
                max(1, int(self._task_panel.rect.height) - (self._top * 2)),
            )
        layout.apply(container)

    def slot_rect(self, index: int) -> Rect:
        self._ensure_slot(int(index))
        return Rect(self._slots[int(index)].rect)


def create_task_panel_slot_layout(task_panel, spec: TaskPanelSlotLayoutSpec):
    """Create a flex-backed slot adapter for scene task-panel items."""
    return _FlexTaskPanelSlotLayout(task_panel, spec)


def _resolve_scene_navigation_callback(host, spec: TaskPanelSceneNavButtonSpec):
    """Resolve scene-navigation callback with host-first overrides."""
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


def add_task_panel_scene_nav_button(task_panel, app_layout, host, spec: TaskPanelSceneNavButtonSpec):
    """Add a scene-navigation button to a task panel from declarative spec."""
    resolved_slot_index = 0 if spec.slot_index is None else int(spec.slot_index)
    button = add_task_panel_button(
        task_panel,
        app_layout,
        control_id=str(spec.control_id),
        slot_index=resolved_slot_index,
        label=str(spec.label),
        on_click=_resolve_scene_navigation_callback(host, spec),
        style=str(spec.style),
        assign_tab_index=False,
    )
    button.set_accessibility(role=str(spec.accessibility_role), label=str(spec.accessibility_label))
    button.set_tab_index(int(spec.tab_index))
    if spec.attr_name:
        setattr(host, str(spec.attr_name), button)
    return button


def add_scene_task_panel_items(
    host,
    task_panel,
    app_layout,
    *,
    button_specs: Sequence[TaskPanelButtonSpec] = (),
    scene_nav_button_specs: Sequence[TaskPanelSceneNavButtonSpec] = (),
    window_toggle_group_spec: "TaskPanelWindowToggleGroupSpec | None" = None,
    window_presentation=None,
    window_toggle_attr_owner=None,
    window_toggle_slot_overrides: Mapping[str, int] | None = None,
    tab_sequence_start: int | None = None,
) -> SceneTaskPanelItemsResult:
    """Compose scene task-panel content from declarative button/toggle specs."""
    resolved_button_slots: dict[str, int] = {}
    resolved_scene_nav_slots: dict[str, int] = {}
    resolved_toggle_slots: dict[str, int] = {}

    next_auto_slot = 0
    used_slots: set[int] = set()

    def _claim_slot(specified: int | None, *, minimum: int = 0) -> int:
        nonlocal next_auto_slot
        if specified is not None:
            slot = int(specified)
            used_slots.add(slot)
            next_auto_slot = max(next_auto_slot, slot + 1)
            return slot
        next_auto_slot = max(next_auto_slot, int(minimum))
        while next_auto_slot in used_slots:
            next_auto_slot += 1
        slot = next_auto_slot
        used_slots.add(slot)
        next_auto_slot += 1
        return slot

    for spec in button_specs:
        slot = _claim_slot(spec.slot_index)
        resolved_button_slots[str(spec.attr_name)] = slot
        button = add_task_panel_button(
            task_panel,
            app_layout,
            control_id=spec.control_id,
            slot_index=slot,
            label=spec.label,
            on_click=spec.on_click,
            style=spec.style,
        )
        setattr(host, spec.attr_name, button)

    resolved_override_map = dict(window_toggle_slot_overrides or {})

    effective_window_toggle_group_spec = window_toggle_group_spec
    if window_toggle_group_spec is not None and window_presentation is not None:
        min_slot = int(window_toggle_group_spec.start_index)
        if min_slot >= len(used_slots):
            min_slot = int(next_auto_slot)
        effective_window_toggle_group_spec = TaskPanelWindowToggleGroupSpec(start_index=int(min_slot))
        next_auto_slot = max(next_auto_slot, min_slot)
        for binding in sorted_window_bindings(window_presentation.bindings()):
            key = str(getattr(binding, "key", ""))
            if key in resolved_override_map:
                slot = int(resolved_override_map[key])
                used_slots.add(slot)
                next_auto_slot = max(next_auto_slot, slot + 1)
                resolved_toggle_slots[key] = slot
                continue
            declared = getattr(binding, "task_panel_slot_index", None)
            slot = _claim_slot(int(declared) if declared is not None else None, minimum=min_slot)
            resolved_override_map[key] = slot
            resolved_toggle_slots[key] = slot

    next_auto_slot = (max(used_slots) + 1) if used_slots else 0
    scene_nav_buttons = []
    for spec in scene_nav_button_specs:
        slot = _claim_slot(spec.slot_index, minimum=next_auto_slot)
        resolved_scene_nav_slots[str(spec.control_id)] = slot
        button = add_task_panel_scene_nav_button(
            task_panel,
            app_layout,
            host,
            TaskPanelSceneNavButtonSpec(
                attr_name=spec.attr_name,
                control_id=spec.control_id,
                slot_index=slot,
                label=spec.label,
                target_scene=spec.target_scene,
                go_to_attr=spec.go_to_attr,
                style=spec.style,
                accessibility_role=spec.accessibility_role,
                accessibility_label=spec.accessibility_label,
                tab_index=spec.tab_index,
            ),
        )
        scene_nav_buttons.append(button)

    window_toggle_controls = []
    if effective_window_toggle_group_spec is not None and window_presentation is not None:
        window_toggle_controls = add_task_panel_window_toggle_group(
            host,
            task_panel,
            app_layout,
            window_presentation,
            effective_window_toggle_group_spec,
            attr_owner=window_toggle_attr_owner,
            slot_overrides=resolved_override_map,
        )

    if tab_sequence_start is not None:
        ordered_items = []
        for spec in button_specs:
            control = getattr(host, str(spec.attr_name), None)
            if control is None:
                continue
            ordered_items.append((int(resolved_button_slots[str(spec.attr_name)]), control, "button", str(spec.label)))
        for btn, spec in zip(scene_nav_buttons, scene_nav_button_specs):
            ordered_items.append(
                (
                    int(resolved_scene_nav_slots[str(spec.control_id)]),
                    btn,
                    str(spec.accessibility_role),
                    str(spec.accessibility_label),
                )
            )
        for binding, control in window_toggle_controls:
            slot_index = int(resolved_toggle_slots.get(str(binding.key), 0))
            label = binding.accessibility_label or binding.action_label or binding.key
            ordered_items.append((int(slot_index), control, "toggle", str(label)))
        ordered_items.sort(key=lambda x: x[0])
        items = [(control, role, label) for _slot, control, role, label in ordered_items]
        apply_accessibility_sequence(items, int(tab_sequence_start))

    return SceneTaskPanelItemsResult(
        scene_nav_buttons=tuple(scene_nav_buttons),
        window_toggle_controls=tuple(window_toggle_controls),
    )


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
    manual_shortcut_lines: Sequence[str] = (),
    manual_section_title: str = "Keyboard",
    prepend_manual_shortcuts: bool = False,
    manual_shortcuts_only: bool = False,
    exclude_section_titles: Sequence[str] = (),
    exclude_entry_labels: Sequence[str] = (),
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
        app=app,
        action_registry=action_registry,
        overlay_rect=overlay_rect,
        manual_shortcut_lines=tuple(manual_shortcut_lines),
        manual_section_title=str(manual_section_title),
        prepend_manual_shortcuts=bool(prepend_manual_shortcuts),
        manual_shortcuts_only=bool(manual_shortcuts_only),
        exclude_section_titles=tuple(exclude_section_titles),
        exclude_entry_labels=tuple(exclude_entry_labels),
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


def _resolve_parent_runtime_service_scope(host) -> ServiceScope | None:
    runtime_scope = getattr(host, "runtime_scope", None)
    scope = getattr(runtime_scope, "service_scope", None)
    if isinstance(scope, ServiceScope):
        return scope
    app = getattr(host, "app", None)
    app_scope = getattr(app, "service_scope", None)
    if isinstance(app_scope, ServiceScope):
        return app_scope
    return None


def _invoke_runtime_factory(factory: Callable[..., object], feature, host, runtime_scope: FeatureRuntimeScope):
    try:
        signature = inspect.signature(factory)
    except (TypeError, ValueError):
        return factory(feature, host, runtime_scope)
    parameters = tuple(signature.parameters.values())
    if any(parameter.kind is inspect.Parameter.VAR_POSITIONAL for parameter in parameters):
        return factory(feature, host, runtime_scope)
    positional = [
        parameter
        for parameter in parameters
        if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    argc = len(positional)
    if argc <= 0:
        return factory()
    if argc == 1:
        return factory(feature)
    if argc == 2:
        return factory(feature, host)
    return factory(feature, host, runtime_scope)


def create_feature_runtime_scope(feature, host, spec: RoutedRuntimeSpec) -> FeatureRuntimeScope:
    """Create and attach a lifecycle-owned runtime scope for a feature."""
    scope = FeatureRuntimeScope(parent_scope=_resolve_parent_runtime_service_scope(host))
    attr_name = str(getattr(spec, "runtime_scope_attr_name", "runtime_scope") or "")
    if attr_name:
        setattr(feature, attr_name, scope)
    return scope


def bind_feature_runtime_services(
    feature,
    host,
    runtime_scope: FeatureRuntimeScope,
    bindings: Sequence[ServiceBindingSpec],
) -> None:
    """Instantiate and publish feature-owned runtime services."""
    for binding in bindings:
        instance = _invoke_runtime_factory(binding.factory, feature, host, runtime_scope)
        runtime_scope.bind_service(binding.key, instance, owned=bool(binding.owned))
        attr_name = str(binding.attr_name)
        if attr_name:
            setattr(feature, attr_name, instance)


def resolve_feature_runtime_services(
    feature,
    runtime_scope: FeatureRuntimeScope,
    consumers: Sequence[ServiceConsumerSpec],
) -> None:
    """Resolve runtime services into feature attributes."""
    for consumer in consumers:
        attr_name = str(consumer.attr_name)
        if bool(consumer.required):
            instance = runtime_scope.get_service(consumer.key)
        else:
            instance = runtime_scope.get_optional_service(consumer.key)
        setattr(feature, attr_name, instance)


def _resolve_runtime_store(feature, runtime_scope: FeatureRuntimeScope, *, store_attr_name: str, service_key: object | None):
    if service_key is not None:
        return runtime_scope.get_service(service_key)
    return getattr(feature, str(store_attr_name))


def _resolve_runtime_observable(feature, runtime_scope: FeatureRuntimeScope, spec: ObservableEffectSpec):
    if spec.observable_attr_name:
        return getattr(feature, str(spec.observable_attr_name))
    if spec.service_key is not None:
        return runtime_scope.get_service(spec.service_key)
    if spec.observable_factory is not None:
        return _invoke_runtime_factory(spec.observable_factory, feature, None, runtime_scope)
    raise ValueError("ObservableEffectSpec requires observable_attr_name, service_key, or observable_factory")


def _resolve_runtime_signal(feature, runtime_scope: FeatureRuntimeScope, spec: SignalEffectSpec):
    if spec.signal_attr_name:
        return getattr(feature, str(spec.signal_attr_name))
    if spec.service_key is not None:
        return runtime_scope.get_service(spec.service_key)
    if spec.signal_factory is not None:
        return _invoke_runtime_factory(spec.signal_factory, feature, None, runtime_scope)
    raise ValueError("SignalEffectSpec requires signal_attr_name, service_key, or signal_factory")


def bind_store_subscriptions(feature, runtime_scope: FeatureRuntimeScope, subscriptions: Sequence[StoreSubscriptionSpec]) -> None:
    """Bind AppStateStore key subscriptions into the runtime scope."""
    for spec in subscriptions:
        store = _resolve_runtime_store(
            feature,
            runtime_scope,
            store_attr_name=str(spec.store_attr_name),
            service_key=spec.service_key,
        )
        unsubscribe = store.subscribe(str(spec.state_key), spec.handler)
        runtime_scope.add_cleanup(unsubscribe)
        if spec.invoke_immediately:
            spec.handler(store.get(str(spec.state_key)))


def bind_store_selectors(feature, runtime_scope: FeatureRuntimeScope, selectors: Sequence[StoreSelectorSpec]) -> None:
    """Bind selector-backed AppStateStore effects into the runtime scope."""
    for spec in selectors:
        store = _resolve_runtime_store(
            feature,
            runtime_scope,
            store_attr_name=str(spec.store_attr_name),
            service_key=spec.service_key,
        )
        selector = store.select(
            spec.selector,
            depends_on=(set(spec.depends_on) if spec.depends_on else None),
        )
        if spec.attr_name:
            setattr(feature, str(spec.attr_name), selector)
        runtime_scope.add_cleanup(selector.subscribe(spec.handler))
        if spec.invoke_immediately:
            spec.handler(selector.value)


def bind_observable_effects(feature, host, runtime_scope: FeatureRuntimeScope, effects: Sequence[ObservableEffectSpec]) -> None:
    """Bind observable subscriptions into the runtime scope."""
    for spec in effects:
        if spec.observable_factory is not None:
            observable = _invoke_runtime_factory(spec.observable_factory, feature, host, runtime_scope)
        else:
            observable = _resolve_runtime_observable(feature, runtime_scope, spec)
        runtime_scope.subscribe(observable, spec.handler)
        if spec.invoke_immediately and hasattr(observable, "value"):
            spec.handler(observable.value)


def bind_signal_effects(feature, host, runtime_scope: FeatureRuntimeScope, effects: Sequence[SignalEffectSpec]) -> None:
    """Bind signal connections into the runtime scope."""
    for spec in effects:
        if spec.signal_factory is not None:
            signal = _invoke_runtime_factory(spec.signal_factory, feature, host, runtime_scope)
        else:
            signal = _resolve_runtime_signal(feature, runtime_scope, spec)
        connection = signal.connect_once(spec.handler) if spec.once else signal.connect(spec.handler)
        runtime_scope.own_connection(connection)


def create_feature_operation_bus(feature, host, runtime_scope: FeatureRuntimeScope, spec: RoutedRuntimeSpec) -> FeatureOperationBus | None:
    """Create and configure a feature-scoped operation bus when requested."""
    needs_bus = bool(spec.operations or spec.failure_policies or spec.operation_service_key is not None or spec.operation_bus_attr_name)
    if not needs_bus:
        return None
    app = getattr(host, "app", None)
    bus = FeatureOperationBus(
        feature=feature,
        host=host,
        runtime_scope=runtime_scope,
        timers=getattr(app, "timers", None),
        event_bus=getattr(app, "events", None),
    )
    runtime_scope.own_disposable(bus)
    if spec.operation_bus_attr_name:
        setattr(feature, str(spec.operation_bus_attr_name), bus)
    if spec.operation_service_key is not None:
        runtime_scope.bind_service(spec.operation_service_key, bus, owned=False)
    for policy in spec.failure_policies:
        bus.register_failure_policy(
            str(policy.name),
            retries=int(policy.retries),
            retry_delay_seconds=float(policy.retry_delay_seconds),
            timeout_seconds=policy.timeout_seconds,
            publish_topic=policy.publish_topic,
            publish_scope=policy.publish_scope,
        )
    for operation in spec.operations:
        runtime_scope.add_cleanup(
            bus.register(
                str(operation.name),
                operation.handler,
                failure_policy=operation.failure_policy,
            )
        )
    return bus


def setup_routed_runtime(feature, host, spec: RoutedRuntimeSpec):
    """Apply standard routed-feature runtime wiring from a declarative spec.

    Wires scheduler/logic aliases, optional action hotkeys, event subscriptions,
    and optional shortcut overlays while keeping feature bind_runtime methods short.
    """
    scheduler = configure_routed_feature_runtime(
        feature,
        host,
        scene_name=str(spec.scene_name),
        scheduler_attr_name=str(spec.scheduler_attr_name),
        scheduler_dispatch_limit=spec.scheduler_dispatch_limit,
        logic_bindings=tuple(spec.logic_bindings),
    )
    runtime_scope = create_feature_runtime_scope(feature, host, spec)

    if spec.service_bindings:
        bind_feature_runtime_services(feature, host, runtime_scope, tuple(spec.service_bindings))

    operation_bus = create_feature_operation_bus(feature, host, runtime_scope, spec)

    if spec.service_consumers:
        resolve_feature_runtime_services(feature, runtime_scope, tuple(spec.service_consumers))

    if operation_bus is not None and spec.operation_service_key is not None and spec.service_consumers:
        resolve_feature_runtime_services(feature, runtime_scope, tuple(spec.service_consumers))

    if spec.store_subscriptions:
        bind_store_subscriptions(feature, runtime_scope, tuple(spec.store_subscriptions))

    if spec.store_selectors:
        bind_store_selectors(feature, runtime_scope, tuple(spec.store_selectors))

    if spec.observable_effects:
        bind_observable_effects(feature, host, runtime_scope, tuple(spec.observable_effects))

    if spec.signal_effects:
        bind_signal_effects(feature, host, runtime_scope, tuple(spec.signal_effects))

    runtime_systems = build_routed_runtime_systems(
        feature,
        host,
        runtime_scope=runtime_scope,
        operation_bus=operation_bus,
        execution_context_spec=spec.execution_context_spec,
        budget_spec=spec.budget_spec,
        checkpoint_spec=spec.checkpoint_spec,
        saga_specs=tuple(spec.saga_specs),
        reactive_graph_spec=spec.reactive_graph_spec,
        migration_spec=spec.migration_spec,
        dependency_specs=tuple(spec.feature_dependencies),
        policy_specs=tuple(spec.policy_specs),
        effect_bindings=tuple(spec.effect_bindings),
        event_pipeline_specs=tuple(spec.event_pipelines),
        durable_queue_spec=spec.durable_queue_spec,
        capability_providers=tuple(spec.capability_providers),
        capability_requirements=tuple(spec.capability_requirements),
        projection_spec=spec.projection_spec,
        workflow_specs=tuple(spec.workflow_specs),
        recompute_nodes=tuple(spec.recompute_nodes),
        qos_policies=tuple(spec.qos_policies),
        health_probes=tuple(spec.health_probes),
        replay_spec=spec.replay_spec,
    )
    if runtime_systems is not None:
        runtime_scope.own_disposable(runtime_systems)
        setattr(feature, "_routed_runtime_on_update", runtime_systems.on_update)
        runtime_scope.add_cleanup(lambda: setattr(feature, "_routed_runtime_on_update", None))
        if spec.execution_context_attr_name:
            setattr(feature, str(spec.execution_context_attr_name), runtime_systems.execution_context)
        if spec.budget_attr_name:
            setattr(feature, str(spec.budget_attr_name), runtime_systems.budget_broker)
        if spec.checkpoint_attr_name:
            setattr(feature, str(spec.checkpoint_attr_name), runtime_systems.checkpoint)
        if spec.saga_attr_name:
            setattr(feature, str(spec.saga_attr_name), runtime_systems.saga)
        if spec.reactive_graph_attr_name:
            setattr(feature, str(spec.reactive_graph_attr_name), runtime_systems.reactive_graph)
        if spec.migration_attr_name:
            setattr(feature, str(spec.migration_attr_name), runtime_systems.migration)
        if spec.policy_attr_name:
            setattr(feature, str(spec.policy_attr_name), runtime_systems.policy_engine)
        if spec.effects_attr_name:
            setattr(feature, str(spec.effects_attr_name), runtime_systems.effects)
        if spec.event_pipeline_attr_name:
            setattr(feature, str(spec.event_pipeline_attr_name), runtime_systems.event_pipelines)
        if spec.durable_queue_attr_name:
            setattr(feature, str(spec.durable_queue_attr_name), runtime_systems.durable_queue)
        if spec.capability_attr_name:
            setattr(feature, str(spec.capability_attr_name), runtime_systems.capability_contracts)
        if spec.projection_attr_name:
            setattr(feature, str(spec.projection_attr_name), runtime_systems.projection)
        if spec.workflow_attr_name:
            setattr(feature, str(spec.workflow_attr_name), runtime_systems.workflow_coordinator)
        if spec.recompute_attr_name:
            setattr(feature, str(spec.recompute_attr_name), runtime_systems.recompute)
        if spec.qos_attr_name:
            setattr(feature, str(spec.qos_attr_name), runtime_systems.qos)
        if spec.health_attr_name:
            setattr(feature, str(spec.health_attr_name), runtime_systems.health)
        if spec.replay_attr_name:
            setattr(feature, str(spec.replay_attr_name), runtime_systems.replay)

    if spec.hot_swap_attr_name:
        manager = getattr(feature, "_feature_manager", None)
        if manager is not None:
            setattr(feature, str(spec.hot_swap_attr_name), FeatureHotSwapManager(manager, host))
            runtime_scope.add_cleanup(lambda: setattr(feature, str(spec.hot_swap_attr_name), None))

    app = getattr(host, "app", None)
    app_actions = getattr(app, "actions", None)
    app_events = getattr(app, "events", None)

    if spec.action_hotkeys and app_actions is not None:
        register_action_hotkeys(app_actions, tuple(spec.action_hotkeys), feature=feature, host=host)

    if spec.global_pointer_actions and app_actions is not None:
        register_global_pointer_actions(app_actions, tuple(spec.global_pointer_actions))

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
                manual_shortcut_lines=tuple(overlay_spec.manual_shortcut_lines),
                manual_section_title=str(overlay_spec.manual_section_title),
                prepend_manual_shortcuts=bool(overlay_spec.prepend_manual_shortcuts),
                manual_shortcuts_only=bool(overlay_spec.manual_shortcuts_only),
                exclude_section_titles=tuple(overlay_spec.exclude_section_titles),
                exclude_entry_labels=tuple(overlay_spec.exclude_entry_labels),
            )
            setattr(feature, str(overlay_spec.attr_name), overlay)
            if overlay_spec.toggle_action_name and app_actions is not None:
                def _make_toggle(ov):
                    return lambda _e: (ov.toggle() or True)
                action_name = str(overlay_spec.toggle_action_name)
                app_actions.register_action(action_name, _make_toggle(overlay))
                if overlay_spec.toggle_key is not None:
                    if bool(overlay_spec.toggle_global_key) and hasattr(app_actions, "bind_global_key"):
                        if overlay_spec.toggle_scene_name is not None:
                            app_actions.bind_global_key(
                                int(overlay_spec.toggle_key),
                                action_name,
                                scene=str(overlay_spec.toggle_scene_name),
                            )
                        else:
                            app_actions.bind_global_key(int(overlay_spec.toggle_key), action_name)
                    else:
                        if overlay_spec.toggle_scene_name is not None:
                            app_actions.bind_key(int(overlay_spec.toggle_key), action_name, scene=str(overlay_spec.toggle_scene_name))
                        else:
                            app_actions.bind_key(int(overlay_spec.toggle_key), action_name)

    # Register command palette first so task panel focus toggle can override if needed
    if spec.command_palette is not None and app is not None:
        palette_manager = _ensure_command_palette_manager(host, palette_requested=True)
        if palette_manager is not None:
            setup_scene_command_palette_bindings(app, palette_manager, spec.command_palette)

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
    attr_name = str(getattr(spec, "runtime_scope_attr_name", "runtime_scope") or "")
    runtime_scope = getattr(feature, attr_name, None) if attr_name else None
    if runtime_scope is not None and hasattr(runtime_scope, "dispose"):
        runtime_scope.dispose()
    if attr_name:
        setattr(feature, attr_name, None)
    if spec.operation_bus_attr_name:
        setattr(feature, str(spec.operation_bus_attr_name), None)
    if spec.execution_context_attr_name:
        setattr(feature, str(spec.execution_context_attr_name), None)
    if spec.budget_attr_name:
        setattr(feature, str(spec.budget_attr_name), None)
    if spec.checkpoint_attr_name:
        setattr(feature, str(spec.checkpoint_attr_name), None)
    if spec.saga_attr_name:
        setattr(feature, str(spec.saga_attr_name), None)
    if spec.reactive_graph_attr_name:
        setattr(feature, str(spec.reactive_graph_attr_name), None)
    if spec.migration_attr_name:
        setattr(feature, str(spec.migration_attr_name), None)
    if spec.policy_attr_name:
        setattr(feature, str(spec.policy_attr_name), None)
    if spec.effects_attr_name:
        setattr(feature, str(spec.effects_attr_name), None)
    if spec.event_pipeline_attr_name:
        setattr(feature, str(spec.event_pipeline_attr_name), None)
    if spec.durable_queue_attr_name:
        setattr(feature, str(spec.durable_queue_attr_name), None)
    if spec.capability_attr_name:
        setattr(feature, str(spec.capability_attr_name), None)
    if spec.projection_attr_name:
        setattr(feature, str(spec.projection_attr_name), None)
    if spec.workflow_attr_name:
        setattr(feature, str(spec.workflow_attr_name), None)
    if spec.recompute_attr_name:
        setattr(feature, str(spec.recompute_attr_name), None)
    if spec.qos_attr_name:
        setattr(feature, str(spec.qos_attr_name), None)
    if spec.health_attr_name:
        setattr(feature, str(spec.health_attr_name), None)
    if spec.replay_attr_name:
        setattr(feature, str(spec.replay_attr_name), None)
    if spec.hot_swap_attr_name:
        setattr(feature, str(spec.hot_swap_attr_name), None)
    setattr(feature, "_routed_runtime_on_update", None)


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


def register_feature_companions(feature, host, *, companion_providers=()) -> tuple[object, ...]:
    """Register companion features/providers on the owning feature manager.

    Entries in *companion_providers* can be provider instances or zero-arg factories.
    """
    if not companion_providers:
        return ()
    manager = getattr(feature, "_feature_manager", None)
    if manager is None:
        return ()
    providers: list[object] = []
    for provider_entry in companion_providers:
        provider = provider_entry() if callable(provider_entry) else provider_entry
        if provider is None:
            continue
        providers.append(provider)
    if providers:
        register_companion_logic_features(manager, host, providers)
    return tuple(providers)


def bind_feature_runtime(
    feature,
    host,
    *,
    runtime_spec: RoutedRuntimeSpec,
    runtime_spec_attr_name: str = "_runtime_spec",
    scheduler_attr_name: str | None = None,
    bind_escape_to_exit_scene: str | None = None,
):
    """Bind routed runtime and optional Escape->exit action wiring.

    This composes setup_routed_runtime with common feature-side attribute storage
    so feature bind_runtime methods stay short and declarative.
    """
    scheduler = setup_routed_runtime(feature, host, runtime_spec)
    if runtime_spec_attr_name:
        setattr(feature, str(runtime_spec_attr_name), runtime_spec)
    if scheduler_attr_name:
        setattr(feature, str(scheduler_attr_name), scheduler)
    if bind_escape_to_exit_scene is not None:
        app_actions = getattr(getattr(host, "app", None), "actions", None)
        bind_global_key = getattr(app_actions, "bind_global_key", None)
        if callable(bind_global_key):
            bind_global_key(pygame.K_ESCAPE, "exit", scene=str(bind_escape_to_exit_scene))
    return scheduler


def shutdown_feature_runtime(
    feature,
    host,
    *,
    runtime_spec: RoutedRuntimeSpec | None = None,
    runtime_spec_attr_name: str = "_runtime_spec",
    scheduler_attr_name: str | None = None,
    bind_escape_to_exit_scene: str | None = None,
) -> bool:
    """Shutdown routed runtime and optional Escape->exit action unbinding."""
    resolved_runtime_spec = runtime_spec
    if resolved_runtime_spec is None and runtime_spec_attr_name:
        resolved_runtime_spec = getattr(feature, str(runtime_spec_attr_name), None)
    if resolved_runtime_spec is None:
        return False
    shutdown_routed_runtime(feature, host, resolved_runtime_spec)
    if runtime_spec_attr_name:
        setattr(feature, str(runtime_spec_attr_name), None)
    if scheduler_attr_name:
        setattr(feature, str(scheduler_attr_name), None)
    if bind_escape_to_exit_scene is not None:
        app_actions = getattr(getattr(host, "app", None), "actions", None)
        unbind_global_key = getattr(app_actions, "unbind_global_key", None)
        if callable(unbind_global_key):
            unbind_global_key(pygame.K_ESCAPE, "exit", scene=str(bind_escape_to_exit_scene))
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
    binding it as a global-first key per scene::

        bind_task_panel_focus_toggle(
            host.app.actions, host.app,
            action_name="toggle_task_panel_focus",
            scene_name="main",
            key=pygame.K_F1,
        )

    The key is bound through ``ActionManager.bind_global_key`` so it always
    routes first, even when an active window or focused control would otherwise
    consume key input.
    """
    def _toggle(_event):
        overlay = getattr(app, "overlay", None)
        has_overlay = getattr(overlay, "has_overlay", None)
        if callable(has_overlay) and has_overlay("__command_palette__"):
            return True
        task_panel_focus = getattr(app, "task_panel_focus", None)
        return bool(task_panel_focus is not None and task_panel_focus.toggle(app.scene, app))

    app_actions.register_action(str(action_name), _toggle)
    app_actions.bind_global_key(key, str(action_name), scene=str(scene_name))


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

    def advance(self, amount: int) -> int:
        """Advance the y cursor by *amount* and return the new y."""
        self._y += int(amount)
        return self._y

    def remaining_height(self, *, margin: int = 0) -> int:
        """Return remaining vertical space to rect.bottom, minus optional margin."""
        return int(self._rect.bottom - self._y - int(margin))

    def build(self) -> list:
        """Return a copy of created controls for the caller."""
        return list(self._controls)


def make_window_toggle_spec(
    key: str,
    feature_attribute_name: str,
    *,
    task_panel_slot_index: int | None = None,
    task_panel_label: str | None = None,
    task_panel_style: str = "round",
    action_label: str | None = None,
    action_name: str | None = None,
    task_panel_toggle_button_id: str | None = None,
    toggle_attribute_name: str | None = None,
    accessibility_label: str | None = None,
    window_effects: dict | None = None,
    window_management_opt_in: bool = True,
    titlebar_controls: WindowTitlebarControlsSpec | None = None,
) -> WindowSpec:
    """Build a WindowSpec with conventional defaults for demo/host window toggles."""
    return _make_window_toggle_spec(
        window_spec_cls=WindowSpec,
        key=key,
        feature_attribute_name=feature_attribute_name,
        task_panel_slot_index=task_panel_slot_index,
        task_panel_label=task_panel_label,
        task_panel_style=task_panel_style,
        action_label=action_label,
        action_name=action_name,
        task_panel_toggle_button_id=task_panel_toggle_button_id,
        toggle_attribute_name=toggle_attribute_name,
        accessibility_label=accessibility_label,
        window_effects=window_effects or {},
        window_management_opt_in=window_management_opt_in,
        titlebar_controls=titlebar_controls,
    )


def make_scene_nav_action(
    action_id: str,
    *,
    label: str,
    target_scene: str,
    category: str = "Scenes",
) -> ActionSpec:
    """Build a scene-navigation ActionSpec with consistent defaults."""
    return _make_scene_nav_action(
        action_spec_cls=ActionSpec,
        action_id=action_id,
        label=label,
        target_scene=target_scene,
        category=category,
    )


def make_exit_action(
    action_id: str = "exit",
    *,
    label: str = "Exit",
    category: str = "File",
) -> ActionSpec:
    """Build a standard exit ActionSpec."""
    return _make_exit_action(
        action_spec_cls=ActionSpec,
        action_id=action_id,
        label=label,
        category=category,
    )


def make_palette_toggle_action(
    action_id: str = "palette_toggle",
    *,
    label: str = "Toggle Command Palette",
    key: int | None = None,
) -> ActionSpec:
    """Build a standard command-palette toggle ActionSpec."""
    return _make_palette_toggle_action(
        action_spec_cls=ActionSpec,
        action_id=action_id,
        label=label,
        key=key,
    )


def make_static_accessibility_spec(
    control_attr: str,
    *,
    label: str,
    role: str = "button",
) -> StaticAccessibilitySpec:
    """Build a StaticAccessibilitySpec with a role default suitable for buttons."""
    return _make_static_accessibility_spec(
        static_accessibility_spec_cls=StaticAccessibilitySpec,
        control_attr=control_attr,
        label=label,
        role=role,
    )


def build_feature_specs(entries: Sequence[tuple[str, Callable[[], object]] | FeatureSpec]) -> tuple[FeatureSpec, ...]:
    """Build FeatureSpec values from shorthand tuples or existing FeatureSpec instances.

    Each entry can be either:
    - ``FeatureSpec(attr_name=..., factory=...)``
    - ``(attr_name, factory)``
    """
    return _build_feature_specs(entries, feature_spec_cls=FeatureSpec)


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
    return _build_feature_window_bundle_specs(
        entries,
        feature_spec_cls=FeatureSpec,
        window_spec_cls=WindowSpec,
        make_window_toggle_spec_fn=make_window_toggle_spec,
    )


def build_window_toggle_specs(bindings: Sequence[WindowToggleBindingSpec | WindowSpec]) -> tuple[WindowSpec, ...]:
    """Build WindowSpec values from WindowToggleBindingSpec entries.

    Entries may also include pre-built WindowSpec instances for mixed workflows.
    """
    return _build_window_toggle_specs(
        bindings,
        window_spec_cls=WindowSpec,
        make_window_toggle_spec_fn=make_window_toggle_spec,
    )


def build_scene_nav_actions(
    nav_entries: Sequence[tuple[str, str, str] | ActionSpec],
    *,
    category: str = "Scenes",
) -> tuple[ActionSpec, ...]:
    """Build scene-navigation ActionSpec values from shorthand tuples.

    Each tuple entry is ``(action_id, label, target_scene)``.
    Pre-built ActionSpec entries are passed through unchanged.
    """
    return _build_scene_nav_actions(
        nav_entries,
        action_spec_cls=ActionSpec,
        make_scene_nav_action_fn=make_scene_nav_action,
        category=category,
    )


def build_action_specs(entries: Sequence[ActionBindingSpec | ActionSpec]) -> tuple[ActionSpec, ...]:
    """Build ActionSpec values from ActionBindingSpec entries.

    Supports common action kinds:
    - ``exit``
    - ``scene_nav`` (requires ``target``)
    - ``palette_toggle``

    Pre-built ActionSpec entries are passed through unchanged.
    """
    return _build_action_specs(
        entries,
        action_spec_cls=ActionSpec,
        make_exit_action_fn=make_exit_action,
        make_scene_nav_action_fn=make_scene_nav_action,
        make_palette_toggle_action_fn=make_palette_toggle_action,
    )


def build_static_accessibility_specs(
    entries: Sequence[tuple[str, str] | StaticAccessibilitySpec],
    *,
    role: str = "button",
) -> tuple[StaticAccessibilitySpec, ...]:
    """Build StaticAccessibilitySpec values from shorthand tuples.

    Each tuple entry is ``(control_attr, label)`` and uses the shared *role*.
    Pre-built StaticAccessibilitySpec entries are passed through unchanged.
    """
    return _build_static_accessibility_specs(
        entries,
        static_accessibility_spec_cls=StaticAccessibilitySpec,
        make_static_accessibility_spec_fn=make_static_accessibility_spec,
        role=role,
    )


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
    return _build_scene_setup_specs(
        entries,
        scene_setup_binding_spec_cls=SceneSetupBindingSpec,
        scene_setup_spec_cls=SceneSetupSpec,
        default_transition_style=default_transition_style,
        default_transition_duration=default_transition_duration,
        initial_scene_name=initial_scene_name,
    )


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
    return _build_runtime_scene_specs(
        entries,
        runtime_scene_binding_spec_cls=RuntimeSceneBindingSpec,
        runtime_scene_spec_cls=RuntimeSceneSpec,
        pristine_asset=pristine_asset,
        bind_escape_to_exit=bind_escape_to_exit,
        prewarm=prewarm,
    )


def build_scene_root_specs(entries: Sequence[SceneRootBindingSpec | SceneRootSpec | tuple[str, str] | tuple[str, str, bool]]) -> tuple[SceneRootSpec, ...]:
    """Build SceneRootSpec values from shorthand tuples or binding specs."""
    return _build_scene_root_specs(
        entries,
        scene_root_binding_spec_cls=SceneRootBindingSpec,
        scene_root_spec_cls=SceneRootSpec,
    )


def build_cursor_specs(
    entries: Sequence[CursorBindingSpec | CursorSpec | tuple[str, str] | tuple[str, str, tuple[int, int]]],
    *,
    default_hotspot: tuple[int, int] = (0, 0),
) -> tuple[CursorSpec, ...]:
    """Build CursorSpec values from shorthand tuples or CursorBindingSpec entries."""
    return _build_cursor_specs(
        entries,
        cursor_binding_spec_cls=CursorBindingSpec,
        cursor_spec_cls=CursorSpec,
        default_hotspot=default_hotspot,
    )


def build_font_role_specs(
    entries: Sequence[FontRoleBindingSpec | tuple[str, int, str] | tuple[str, int, str, bool, bool] | Mapping[str, Mapping[str, object]]],
) -> tuple[dict, ...]:
    """Build ``HostApplicationConfig.font_role_specs`` from compact role entries.

    The return shape matches what ``setup_standard_font_roles(..., *role_specs)``
    expects: a tuple of role-mapping dict blocks.
    """
    return _build_font_role_specs(
        entries,
        font_role_binding_spec_cls=FontRoleBindingSpec,
        mapping_cls=Mapping,
    )


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
    return _build_scene_bundle_specs(
        entries,
        scene_setup_spec_cls=SceneSetupSpec,
        runtime_scene_spec_cls=RuntimeSceneSpec,
        scene_root_spec_cls=SceneRootSpec,
        action_spec_cls=ActionSpec,
        default_transition_style=default_transition_style,
        default_transition_duration=default_transition_duration,
        default_nav_category=default_nav_category,
        initial_scene_name=initial_scene_name,
    )


def build_host_application_config(
    config: HostApplicationBindingSpec | HostApplicationConfig,
) -> HostApplicationConfig:
    """Build HostApplicationConfig from one host-level binding spec.

    Accepts an already built HostApplicationConfig as passthrough for
    advanced workflows that still want a unified call site.
    """
    return _build_host_application_config(
        config,
        host_application_binding_spec_cls=HostApplicationBindingSpec,
        host_application_config_cls=HostApplicationConfig,
        telemetry_config_cls=TelemetryConfig,
        build_scene_bundle_specs_fn=build_scene_bundle_specs,
        build_scene_setup_specs_fn=build_scene_setup_specs,
        build_runtime_scene_specs_fn=build_runtime_scene_specs,
        build_action_specs_fn=build_action_specs,
        build_scene_root_specs_fn=build_scene_root_specs,
        build_feature_window_bundle_specs_fn=build_feature_window_bundle_specs,
        build_feature_specs_fn=build_feature_specs,
        build_window_toggle_specs_fn=build_window_toggle_specs,
        build_font_role_specs_fn=build_font_role_specs,
        build_cursor_specs_fn=build_cursor_specs,
        build_static_accessibility_specs_fn=build_static_accessibility_specs,
    )


def instantiate_features_from_specs(host, feature_specs) -> None:
    """Instantiate feature objects from specs and attach them to host attributes."""
    _instantiate_features_from_specs(host, feature_specs)


def register_features_from_specs(app, host, feature_specs) -> None:
    """Register instantiated host feature attributes to the application."""
    _register_features_from_specs(app, host, feature_specs)


def register_window_presentation_specs(window_presentation, window_specs) -> None:
    """Register feature-window presentation bindings from declarative window specs."""
    _register_window_presentation_specs(window_presentation, window_specs)


def register_window_tab_builders(tab_manager, feature, host, rect, tab_specs) -> None:
    """Register tab content builders from declarative (tab_key, builder_attr) specs."""
    _register_window_tab_builders(tab_manager, feature, host, rect, tab_specs)


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
    return _create_tab_control_from_specs(
        control_id,
        rect,
        tab_specs,
        selected_key=selected_key,
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
    return _compute_tabbed_window_layout(
        content_rect,
        tab_height=tab_height,
        tab_rows=tab_rows,
        padding=padding,
        min_content_height=min_content_height,
    )


def register_window_tab_builder_specs(tab_manager, feature, host, rect, tab_specs: Sequence[TabBuilderSpec]) -> None:
    """Register tab content builders from TabBuilderSpec definitions."""
    _register_window_tab_builder_specs(tab_manager, feature, host, rect, tab_specs)


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
    return _setup_feature_presenter_tabs(
        presenter,
        control_id=control_id,
        tab_rect=tab_rect,
        tab_specs=tab_specs,
        selected_key=selected_key,
        on_change=on_change,
        tab_manager=tab_manager,
        feature=feature,
        host=host,
        tab_content_rect=tab_content_rect,
    )


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
    return _setup_feature_presenter_tabs_from_window_content(
        presenter,
        window=window,
        spec=spec,
        tab_specs=tab_specs,
        on_change=on_change,
        tab_manager=tab_manager,
        feature=feature,
        host=host,
        on_activate_callbacks=on_activate_callbacks,
        compute_tabbed_window_layout_fn=compute_tabbed_window_layout,
        setup_feature_presenter_tabs_fn=setup_feature_presenter_tabs,
    )


def register_tab_update_handlers(
    router: ActiveTabUpdateRouter,
    handlers: Sequence[tuple[str, Callable[..., object]]],
) -> None:
    """Register multiple active-tab update handlers on a router."""
    _register_tab_update_handlers(router, handlers)


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
    titlebar_controls: WindowTitlebarControlsSpec | dict | None = None,
):
    """Create an anchored window and attach a presenter in one call."""
    return _create_presented_anchored_window(
        host,
        control_id=control_id,
        title=title,
        size=size,
        anchor=anchor,
        margin=margin,
        presenter=presenter,
        window_control_cls=window_control_cls,
        use_frame_backdrop=use_frame_backdrop,
        titlebar_controls=titlebar_controls,
        create_anchored_feature_window_fn=create_anchored_feature_window,
    )


def create_presented_window_from_spec(
    host,
    *,
    presenter,
    spec: AnchoredWindowSpec,
    window_control_cls=WindowControl,
):
    """Create and attach a presenter-backed anchored window from a typed spec."""
    return _create_presented_window_from_spec(
        host,
        presenter=presenter,
        spec=spec,
        window_control_cls=window_control_cls,
        create_presented_anchored_window_fn=create_presented_anchored_window,
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
    return _create_feature_presented_window(
        host,
        feature=feature,
        presenter_cls=presenter_cls,
        spec=spec,
        window_control_cls=window_control_cls,
        create_presented_window_from_spec_fn=create_presented_window_from_spec,
    )


def configure_routed_feature_runtime(
    feature,
    host,
    *,
    scene_name: str = "main",
    scheduler_attr_name: str = "scheduler",
    scheduler_dispatch_limit: int | None = None,
    logic_bindings: Sequence[LogicBindingSpec] = (),
    companion_providers=(),
):
    """Single routed-runtime entrypoint for scheduler, logic bindings, and companions."""
    return _configure_routed_feature_runtime(
        feature,
        host,
        ensure_scene_scheduler_fn=ensure_scene_scheduler,
        scene_name=scene_name,
        scheduler_attr_name=scheduler_attr_name,
        scheduler_dispatch_limit=scheduler_dispatch_limit,
        logic_bindings=logic_bindings,
        companion_providers=companion_providers,
    )
