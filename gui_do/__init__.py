"""GUI package entry point."""

from . import _version

__version__ = _version.__version__

import ctypes
import os


def _enable_windows_dpi_awareness() -> None:
    """Enable process DPI awareness on Windows to avoid scaled client-area padding."""
    if os.name != "nt":
        return
    # Keep strict behavior: let platform/ctypes errors surface for visibility.
    ctypes.windll.user32.SetProcessDPIAware()


_enable_windows_dpi_awareness()

# ============================================================================
# TIER 1: PRIMARY ENTRY POINTS & DATA-DRIVEN APIs
# ============================================================================
# These are the recommended way to build applications with gui_do.
# Use bootstrap_host_application with declarative specs for all new apps.

from .features.feature_lifecycle import (
    Feature,
    DirectFeature,
    LogicFeature,
    RoutedFeature,
    FeatureMessage,
    FeatureManager,
    ScenePresentationModel,
    SceneSetupSpec,
    setup_standard_font_roles,
)
from .features.data_driven_runtime import (
    FeatureSpec,
    WindowSpec,
    RuntimeSceneSpec,
    ActionSpec,
    StaticAccessibilitySpec,
    CursorSpec,
    SceneRootSpec,
    AnchoredWindowSpec,
    LogicBindingSpec,
    TaskPanelButtonSpec,
    ActionHotkeySpec,
    ControlKeyBindingSpec,
    SceneTaskPanelSpec,
    TaskPanelSlotLayoutSpec,
    TaskPanelWindowToggleGroupSpec,
    PaletteInputBindSpec,
    SceneCommandPaletteSpec,
    TaskPanelSceneNavButtonSpec,
    EventSubscriptionSpec,
    ServiceBindingSpec,
    ServiceConsumerSpec,
    StoreSubscriptionSpec,
    StoreSelectorSpec,
    ObservableEffectSpec,
    SignalEffectSpec,
    FailurePolicySpec,
    FeatureOperationSpec,
    ShortcutOverlaySpec,
    TaskPanelFocusToggleSpec,
    GlobalPointerActionSpec,
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
    RoutedRuntimeSpec,
    RoutedFeatureLifecycleSpec,
    FeatureWindowBundleBindingSpec,
    WindowToggleBindingSpec,
    SceneSetupBindingSpec,
    RuntimeSceneBindingSpec,
    SceneRootBindingSpec,
    CursorBindingSpec,
    FontRoleBindingSpec,
    ActionBindingSpec,
    PaletteBindingSpec,
    SceneBundleBindingSpec,
    HostApplicationBindingSpec,
    TabbedPresenterSpec,
    AccessibilitySequenceSpec,
    TabBuilderSpec,
    NotificationSpec,
    HostApplicationConfig,
    TelemetryConfig,
    bootstrap_host_application,
    make_window_toggle_spec,
    make_scene_nav_action,
    make_exit_action,
    make_palette_toggle_action,
    make_static_accessibility_spec,
    build_feature_specs,
    build_feature_window_bundle_specs,
    build_window_toggle_specs,
    build_scene_setup_specs,
    build_runtime_scene_specs,
    build_scene_root_specs,
    build_cursor_specs,
    build_font_role_specs,
    build_scene_nav_actions,
    build_action_specs,
    build_scene_bundle_specs,
    build_static_accessibility_specs,
    build_host_application_config,
    build_notification_center,
)
from .features.runtime_facilities import FeatureOperationBus, FeatureOperationContext, FeatureOperationHandle, FeatureRuntimeScope
from .features.control_spec import (
    ControlDefinition,
    build_specs_from_column_section,
    RowCellSpec,
    build_horizontal_row_specs,
    build_multi_column_grid_specs,
)

# ============================================================================
# TIER 2: CORE APPLICATION & SCENE MANAGEMENT
# ============================================================================
# Central managers and containers required for all apps.

from .app.gui_application import GuiApplication
from .app.display import create_display
from .persistence.scene_transition_manager import SceneTransitionManager, SceneTransitionStyle
from .features.feature_lifecycle import apply_scene_setup_specs

# ============================================================================
# TIER 3: ESSENTIAL DATA & STATE MANAGEMENT
# ============================================================================
# Core abstractions for reactive programming and presentation models.

from .data.presentation_model import ObservableValue, PresentationModel, ComputedValue
from .data.reactive_batch import reactive_batch, is_batching
from .data.invalidation import InvalidationTracker
from .data.observable_collections import (
    ChangeKind,
    CollectionChange,
    ObservableList,
    ObservableDict,
)
from .data.collection_view import CollectionViewQuery, CollectionView
from .data.binding import Binding, BindingGroup
from .data.observable_stream import ObservableStream
from .data.selection_model import SelectionModel, SelectionMode

# ============================================================================
# TIER 4: EVENTS, ACTIONS, FOCUS & INPUT
# ============================================================================
# Core event and input infrastructure for feature logic.

from .events.gui_event import EventPhase, EventType, GuiEvent
from .events.value_change import ValueChangeCallback, ValueChangeReason
from .events.input_processing import EventManager
from .events.event_bus import EventBus
from .events.gesture_recognizer import GestureRecognizer
from .events.event_recorder import EventRecorder, EventPlayback, RecordedEvent
from .events.input_snapshot import InputSnapshot
from .events.signal import Signal, SignalConnection
from .actions.action_manager import ActionManager
from .actions.action_middleware import ActionContext, ActionMiddleware
from .actions.action_registry import ActionDescriptor, ActionRegistry
from .actions.input_map import InputMap, InputBinding
from .actions.key_chord_manager import KeyChordManager, KeyChord, ChordStep
from .focus.focus_manager import FocusManager
from .focus.focus_scope import FocusScope, FocusScopeManager
from .focus.window_focus_manager import WindowFocusManager
from .focus.focus_ring import FocusRing

# ============================================================================
# TIER 5: SCHEDULING & ANIMATION
# ============================================================================
# Time-based updates, animations, and asynchronous operations.

from .scheduling.task_scheduler import TaskEvent, TaskScheduler
from .scheduling.timers import Timers
from .scheduling.tween_manager import TweenManager, TweenHandle, Easing
from .scheduling.animation_sequence import AnimationSequence, AnimationHandle
from .scheduling.transition_manager import TransitionManager, TransitionSpec, TransitionEvent
from .scheduling.animation_state_machine import AnimationStateMachine, AnimationTransitionMode
from .scheduling.scene_timeline import SceneTimeline
from .scheduling.rate_limiter import Debouncer, Throttler
from .scheduling.cooperative_scheduler import (
    CooperativeScheduler,
    CoroutineHandle,
    Pause,
    Sleep,
    WaitForEvent,
    WaitForSignal,
    WaitUntil,
    WaitForAll,
)

# ============================================================================
# TIER 6: THEME & FONT MANAGEMENT
# ============================================================================
# Visual theming and typography systems.

from .theme.font_manager import FontManager
from .theme.font_role_registry import FontRoleRegistry
from .theme.color_theme import ColorTheme
from .theme.theme_manager import ThemeManager, DesignTokens
from .theme.scoped_theme import ScopedTheme, ScopedThemeManager

# ============================================================================
# TIER 7: TELEMETRY & DIAGNOSTICS
# ============================================================================
# Performance monitoring and diagnostic tools.

from .telemetry.telemetry import (
    TelemetryCollector,
    TelemetrySample,
    configure_telemetry,
    telemetry_collector,
)
from .telemetry.telemetry_analyzer import (
    analyze_telemetry_log_file,
    analyze_telemetry_records,
    load_telemetry_log_file,
    render_telemetry_report,
)

# ============================================================================
# TIER 8: LAYOUT & SPATIAL
# ============================================================================
# Layout engines, constraint systems, and spatial organization.

from .layout.layout_axis import LayoutAxis
from .layout.constraint_layout import ConstraintLayout, AnchorConstraint
from .layout.dock_workspace import DockPane, DockTabs, DockSplit, DockWorkspace
from .layout.flex_layout import FlexLayout, FlexItem, FlexDirection, FlexAlign, FlexJustify
from .layout.grid_layout import GridLayout, GridTrack, GridPlacement
from .layout.layout_animator import LayoutAnimator
from .layout.layout_pass import LayoutPass, MeasureContext, ArrangeContext, LayoutRoot
from .layout.flow_layout import FlowLayout, FlowItem
from .layout.viewport import Viewport
from .layout.window_layout_handler import WindowLayoutHandler

# ============================================================================
# TIER 9: OVERLAY MANAGERS & WINDOWS
# ============================================================================
# Modal dialogs, toasts, tooltips, and floating content.

from .overlays.overlay_manager import OverlayManager, OverlayHandle
from .overlays.popup_placement import (
    Alignment,
    PlacementResult,
    PopupPlacement,
    Side,
    compute_popup_rect,
)
from .overlays.dialog_manager import DialogManager, DialogHandle
from .overlays.toast_manager import ToastManager, ToastHandle, ToastSeverity
from .overlays.context_menu_manager import ContextMenuManager, ContextMenuItem, ContextMenuHandle
from .overlays.command_palette_manager import CommandPaletteManager, CommandEntry, CommandPaletteHandle
from .overlays.tooltip_manager import TooltipManager, TooltipHandle
from .overlays.menu_bar_manager import MenuBarManager
from .overlays.file_dialog_manager import FileDialogManager, FileDialogOptions, FileDialogHandle
from .overlays.notification_center import NotificationCenter, NotificationRecord
from .overlays.resize_manager import ResizeManager
from .overlays.cursor_manager import CursorManager, CursorHandle, CursorShape
from .overlays.drag_drop_manager import DragDropManager, DragPayload
from .overlays.clipboard import ClipboardManager
from .overlays.transfer_data import TransferData, TransferManager
from .overlays.shortcut_help_overlay import ShortcutHelpOverlay, ShortcutSection, ShortcutEntry

# ============================================================================
# TIER 10: FORMS & DATA BINDING
# ============================================================================
# Form models, validation, document editing, and structured data.

from .forms.form_model import FormModel, FormField, ValidationRule, FieldError
from .forms.form_schema import FormSchema, SchemaField
from .forms.document_model import DocumentModel
from .forms.wizard_flow import WizardFlow, WizardStep, WizardHandle
from .data.validator import (
    ValidationResult,
    Validator,
    RequiredValidator,
    RangeValidator,
    LengthValidator,
    PatternValidator,
    CustomValidator,
    DependentValidator,
    ValidationPipeline,
)

# ============================================================================
# TIER 11: STATE & PERSISTENCE
# ============================================================================
# Application state, command history, routing, and persistent storage.

from .state.command_history import CommandHistory, Command, CommandTransaction
from .state.state_machine import StateMachine
from .state.hierarchical_state_machine import HierarchicalStateMachine
from .state.router import Router, RouteEntry
from .persistence.settings_registry import SettingsRegistry, SettingDescriptor
from .persistence.workspace_persistence import (
    WorkspaceState,
    WorkspacePersistenceManager,
    DEFAULT_WORKSPACE_STATE_PATH,
)
from .persistence.scene_snapshot import SceneSnapshot, NodeSnapshot

# ============================================================================
# TIER 12: PRIMARY CONTROLS (BASIC UI BUILDING BLOCKS)
# ============================================================================
# Essential controls for layouts and basic user interactions.
# RECOMMENDATION: Use Feature system and declarative specs to compose these.

from .controls.composite.panel_control import PanelControl
from .controls.display.label_control import LabelControl
from .controls.input.button_control import ButtonControl
from .controls.input.toggle_control import ToggleControl
from .controls.input.slider_control import SliderControl
from .controls.input.scrollbar_control import ScrollbarControl
from .controls.canvas.canvas_control import CanvasControl, CanvasEventPacket
from .controls.canvas.canvas_viewport import CanvasViewport
from .controls.display.frame_control import FrameControl
from .controls.display.image_control import ImageControl
from .controls.display.arrow_box_control import ArrowBoxControl
from .controls.input.button_group_control import ButtonGroupControl
from .controls.data.tab_control import TabControl, TabItem
from .controls.composite.dock_workspace_panel import DockWorkspacePanel

# ============================================================================
# TIER 13: EXTENDED CONTROLS (SPECIALIZED UI COMPONENTS)
# ============================================================================
# Advanced controls for rich user interfaces.
# RECOMMENDATION: Use Feature system to integrate these into your app.

from .controls.input.text_input_control import TextInputControl
from .controls.input.text_area_control import TextAreaControl
from .controls.display.rich_label_control import RichLabelControl
from .controls.input.dropdown_control import DropdownControl, DropdownOption
from .controls.data.list_view_control import ListViewControl, ListItem
from .controls.composite.overlay_panel_control import OverlayPanelControl
from .controls.data.data_grid_control import DataGridControl, GridColumn, GridRow
from .controls.data.tree_control import TreeControl, TreeNode
from .controls.composite.splitter_control import SplitterControl
from .controls.input.spinner_control import SpinnerControl
from .controls.input.range_slider_control import RangeSliderControl
from .controls.input.color_picker_control import ColorPickerControl
from .controls.composite.scroll_view_control import ScrollViewControl
from .controls.display.progress_bar_control import ProgressBarControl
from .controls.display.animated_image_control import AnimatedImageControl
from .controls.composite.error_boundary import ErrorBoundary
from .controls.chrome.window_control import WindowControl
from .controls.chrome.task_panel_control import TaskPanelControl
from .controls.chrome.window_presenter import WindowPresenter
from .controls.chrome.menu_bar_control import (
    MenuEntry,
    MenuStripControl,
    SceneMenuOptions,
    WindowMenuOptions,
)
from .controls.chrome.notification_panel_control import NotificationPanelControl
from .controls.chrome.property_inspector_panel import PropertyInspectorPanel
from .controls.chrome.toolbar_control import ToolbarControl, ToolbarItem
from .controls.chrome.status_bar_control import StatusBarControl, StatusSlot
from .controls.composite.expander_control import ExpanderControl
from .controls.input.date_picker_control import DatePickerControl
from .controls.input.time_picker_control import TimePickerControl
from .controls.display.breadcrumb_control import BreadcrumbControl, BreadcrumbItem
from .controls.input.split_button_control import SplitButtonControl, SplitButtonOption
from .controls.input.chip_input_control import ChipInputControl

# ============================================================================
# TIER 14: TEXT & LOCALIZATION
# ============================================================================
# Text processing, formatting, searching, and internationalization.

from .text.text_formatter import TextFormatter, NumericFormatter, PatternFormatter, FixedPatternFormatter
from .text.text_flow import TextFlow, TextSpan
from .text.text_searcher import TextSearcher, TextMatch
from .text.localization import StringTable, LocaleRegistry

# ============================================================================
# TIER 15: DATA & COLLECTIONS
# ============================================================================
# Advanced data structures, async loading, and collection operations.

from .data.virtual_item_source import VirtualItemSource, FixedItemSource
from .data.sort_filter_proxy import SortFilterProxySource
from .data.async_data_provider import AsyncDataProvider, LoadState, LoadStateKind
from .data.object_pool import ObjectPool
from .data.data_cache import DataCache, CacheStats
from .data.list_diff import ListDiffCalculator, ListDiff, DiffInsert, DiffRemove, DiffMove

# ============================================================================
# TIER 16: GRAPHICS & RENDERING
# ============================================================================
# Graphics rendering, asset management, and visual effects.

from .graphics.built_in_factory import BuiltInGraphicsFactory
from .graphics.dirty_region import DirtyRegionTracker
from .graphics.draw_context import DrawContext, DrawPhase
from .graphics.asset_registry import AssetRegistry
from .graphics.debug_overlay import DebugOverlay
from .graphics.surface_compositor import SurfaceCompositor, Layer
from .graphics.shape_renderer import ShapeRenderer
from .graphics.surface_effects import SurfaceEffects
from .graphics.vector_path import VectorPath
from .graphics.sprite_sheet import SpriteSheet, FrameAnimation
from .graphics.particle_system import ParticleSystem, Emitter, ParticleLayer
from .graphics.tile_map import TileSet, TileMap
from .graphics.offscreen_backend import (
    RenderTarget,
    LiveRenderTarget,
    OffscreenRenderTarget,
    create_render_target,
    create_surface,
)
from .graphics.scene_graph_2d import Node2D, SceneGraph2D, Camera2D

# ============================================================================
# TIER 17: INTROSPECTION & INSPECTION
# ============================================================================
# Runtime property inspection and debugging utilities.

from .introspection.spatial_index import SceneSpatialIndex
from .introspection.property_registry import (
    ui_property,
    PropertyDescriptor,
    PropertyRegistry,
    property_registry,
)
from .introspection.property_inspector import PropertyInspectorModel, InspectedProperty

# ============================================================================
# TIER 18: ADVANCED RUNTIME & BOOTSTRAPPING
# ============================================================================
# Advanced feature wiring, presentation setup, and internal bootstrap helpers.
# RECOMMENDATION: Use these only for extending bootstrap_host_application behavior.

from .features.feature_lifecycle import (
    FrameTimer,
    TabPanelManager,
    WindowRelativeRect,
    resolve_scene_selection_callback,
    minimize_window_menu_entries,
    set_window_visible_state,
    toggle_window_visibility,
    create_anchored_feature_window,
    add_window_menu_strip,
    place_control,
    place_control_unlabeled,
    register_placed_control,
    add_group_label,
    PlacedControl,
    make_labeled_slot_height_fn,
    apply_category_visibility,
    ControlRegistry,
)
from .features.layout_geometry import split_slot_bounds
from .features.data_driven_runtime import (
    build_tools_menu_entries,
    add_standard_menu_strip,
    add_menu_strip_from_spec,
    apply_accessibility_sequence,
    apply_accessibility_sequence_from_attrs,
    register_companion_logic_features,
    ensure_scene_scheduler,
    sorted_window_bindings,
    collect_window_toggle_controls,
    apply_window_toggle_accessibility,
    add_window_toggle_task_panel_controls,
    add_task_panel_window_toggle_group,
    setup_scene_command_palette_bindings,
    register_window_toggle_tooltips,
    initialize_locale_registry,
    bind_input_map_actions,
    register_descriptors,
    resolve_canvas_local_point,
    apply_runtime_scene_pristine_assets,
    bind_runtime_scene_exit_keys,
    prewarm_runtime_scenes,
    add_task_panel_button,
    add_task_panel_buttons,
    register_tooltip_specs,
    register_action_hotkeys,
    register_global_pointer_actions,
    draw_controls_prewarm,
    bind_palette_window_action_bind,
    ensure_scene_task_panel,
    create_task_panel_slot_layout,
    add_task_panel_scene_nav_button,
    add_scene_task_panel_items,
    centered_overlay_rect,
    create_shortcut_help_overlay,
    bind_feature_event_subscription,
    unbind_feature_event_subscription,
    setup_routed_runtime,
    shutdown_routed_runtime,
    bind_task_panel_focus_toggle,
    add_window_control,
    add_window_label,
    add_window_button,
    add_window_button_row,
    instantiate_features_from_specs,
    register_features_from_specs,
    register_window_presentation_specs,
    register_window_tab_builders,
    build_tab_builder_specs,
    create_tab_control_from_specs,
    compute_tabbed_window_layout,
    setup_feature_presenter_tabs_from_window_content,
    register_window_tab_builder_specs,
    setup_feature_presenter_tabs,
    register_tab_update_handlers,
    create_presented_anchored_window,
    create_presented_window_from_spec,
    create_feature_presented_window,
    configure_routed_feature_runtime,
    register_routed_feature_companions,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
    ActiveTabUpdateRouter,
    TabLayoutContext,
    declare_host_actions,
    build_host_main_tab_order,
    apply_host_main_accessibility,
)

# ============================================================================
# TIER 19: INFRASTRUCTURE & INTERNALS (AVOID IN APPLICATION CODE)
# ============================================================================
# Low-level infrastructure that should not be directly used by applications.

from .app.ui_engine import UiEngine

# ============================================================================
# TIER 20: AUDIO
# ============================================================================
# Portable audio cue system wrapping pygame.mixer.

from .audio.sound_event_bus import SoundCue, SoundBankRegistry, SoundEventBus

# ============================================================================
# TIER 21: ACCESSIBILITY
# ============================================================================
# Semantic node tree, role vocabulary, and live-region announcements.

from .accessibility.accessibility_tree import (
    AccessibilityRole,
    LivePoliteness,
    AccessibilityNode,
    AccessibilityTree,
    AccessibilityAnnouncement,
    AccessibilityBus,
)

# ============================================================================
# TIER 22: THEME INVALIDATION
# ============================================================================
# Automatic visual cache flush on theme switch.

from .theme.theme_invalidation_bus import ThemeInvalidationBus

# ============================================================================
# TIER 23: UNDO CONTEXT ROUTING
# ============================================================================
# Named multi-stack undo/redo context routing.

from .state.undo_context_manager import UndoContextManager

# ============================================================================
# TIER 24: ASYNC FORM VALIDATION
# ============================================================================
# Debounced cross-field reactive validation pipeline.

from .forms.async_form_validator import AsyncFieldValidator, AsyncFormValidator

# ============================================================================
# TIER 25: SCOPED SERVICE GRAPH
# ============================================================================
# Hierarchical typed dependency injection scopes.

from .app.service_scope import ServiceKey, ServiceScope, ScopeStack

# ============================================================================
# TIER 26: CANCELABLE DATAFLOW PIPELINE
# ============================================================================
# Thread-safe multi-stage processing pipeline with stale-gen cancellation.

from .scheduling.dataflow_pipeline import (
    CancellationToken,
    PipelineStage,
    DataflowPipeline,
    PipelineHandle,
)

# ============================================================================
# TIER 27: TRANSACTIONAL APP STATE STORE
# ============================================================================
# Single source-of-truth state with selectors, transactions, and snapshots.

from .state.app_state_store import (
    AppStateStore,
    StateSelector,
    StateTransaction,
)

# ============================================================================
# TIER 28: ADAPTIVE CONSTRAINT LAYOUT v2
# ============================================================================
# Declarative priority-based constraint solver with adaptive viewport policies.

from .layout.adaptive_constraint_layout import (
    ConstraintAttr,
    LayoutConstraint,
    ConstraintSet,
    AdaptivePolicy,
    resolve_adaptive_policy,
)

# ============================================================================
# TIER 29: UNIFIED VIRTUALIZATION CORE
# ============================================================================
# List/tree/grid windowing engine with recycle pool and identity tracking.

from .controls.data.virtualization_core import (
    MeasureMode,
    MeasurePolicy,
    VirtualizedWindow,
    RecyclePool,
    VirtualizationCore,
)

# ============================================================================
# TIER 30: INTERACTION STATE MACHINE FRAMEWORK
# ============================================================================
# Pointer/keyboard/gesture phase tracking with guarded transitions.

from .events.interaction_state_machine import (
    InteractionPhase,
    InteractionContext,
    InteractionTransition,
    InteractionStateMachine,
)

# ============================================================================
# TIER 31: SCHEMA-DRIVEN FORM RUNTIME
# ============================================================================
# Field graph, dependency visibility, and policy-based validation.

from .forms.schema_form_runtime import (
    FieldSchema,
    FieldGraphSchema,
    ValidationPolicy,
    SchemaFormRuntime,
)

# ============================================================================
# TIER 32: PORTABLE SNAPSHOT & MIGRATION LAYER
# ============================================================================
# Versioned persistence with BFS migration graph and composable steps.

from .persistence.snapshot_migration import (
    SchemaVersion,
    VersionedSnapshot,
    MigrationStep,
    MigrationRegistry,
    SnapshotMigrator,
    MigrationError,
    make_snapshot,
    read_version,
)


# ============================================================================
# PUBLIC API DEFINITION
# ============================================================================
__all__ = [
    # Tier 1: PRIMARY ENTRY POINTS
    "Feature",
    "DirectFeature",
    "LogicFeature",
    "RoutedFeature",
    "FeatureMessage",
    "FeatureManager",
    "ScenePresentationModel",
    "SceneSetupSpec",
    "setup_standard_font_roles",
    "FeatureSpec",
    "WindowSpec",
    "RuntimeSceneSpec",
    "ActionSpec",
    "StaticAccessibilitySpec",
    "CursorSpec",
    "SceneRootSpec",
    "AnchoredWindowSpec",
    "LogicBindingSpec",
    "TaskPanelButtonSpec",
    "TaskPanelWindowToggleGroupSpec",
    "PaletteInputBindSpec",
    "SceneCommandPaletteSpec",
    "ActionHotkeySpec",
    "ControlKeyBindingSpec",
    "SceneTaskPanelSpec",
    "TaskPanelSlotLayoutSpec",
    "TaskPanelSceneNavButtonSpec",
    "EventSubscriptionSpec",
    "ServiceBindingSpec",
    "ServiceConsumerSpec",
    "StoreSubscriptionSpec",
    "StoreSelectorSpec",
    "ObservableEffectSpec",
    "SignalEffectSpec",
    "FailurePolicySpec",
    "FeatureOperationSpec",
    "ShortcutOverlaySpec",
    "TaskPanelFocusToggleSpec",
    "GlobalPointerActionSpec",
    "FeatureDependencySpec",
    "ExecutionContextSpec",
    "WorkloadBudgetClassSpec",
    "WorkloadBudgetSpec",
    "CheckpointDomainSpec",
    "CheckpointSpec",
    "SagaStepSpec",
    "SagaSpec",
    "ReactiveSourceSpec",
    "ReactiveNodeSpec",
    "ReactiveGraphSpec",
    "MigrationStepSpec",
    "MigrationTargetSpec",
    "ContractMigrationSpec",
    "RuntimePolicySpec",
    "EffectBindingSpec",
    "EventPipelineStageSpec",
    "EventPipelineSpec",
    "DurableOperationBindingSpec",
    "DurableOperationQueueSpec",
    "DurableQueueRecord",
    "CapabilityProviderSpec",
    "CapabilityRequirementSpec",
    "ProjectionNodeSpec",
    "ProjectionSpec",
    "PolicyDecision",
    "WorkflowStepSpec",
    "WorkflowSpec",
    "RecomputeNodeSpec",
    "QoSPolicySpec",
    "HealthProbeSpec",
    "ReplaySpec",
    "ReplacePolicySpec",
    "WorkflowCoordinator",
    "RuntimePolicyEngine",
    "EffectLifetimeOrchestrator",
    "EventPipelineRuntime",
    "DurableOperationQueueRuntime",
    "CapabilityContractRuntime",
    "ProjectionRuntime",
    "RecomputeOrchestrator",
    "QoSPolicyRuntime",
    "FeatureHealthRuntime",
    "RuntimeReplayHarness",
    "FeatureHotSwapManager",
    "ExecutionContextRuntime",
    "WorkloadBudgetBrokerRuntime",
    "CheckpointRecoveryRuntime",
    "SagaCompensationRuntime",
    "ReactiveDependencyGraphRuntime",
    "ContractMigrationRuntime",
    "RoutedRuntimeSpec",
    "RoutedFeatureLifecycleSpec",
    "FeatureWindowBundleBindingSpec",
    "WindowToggleBindingSpec",
    "SceneSetupBindingSpec",
    "RuntimeSceneBindingSpec",
    "SceneRootBindingSpec",
    "CursorBindingSpec",
    "FontRoleBindingSpec",
    "ActionBindingSpec",
    "PaletteBindingSpec",
    "SceneBundleBindingSpec",
    "HostApplicationBindingSpec",
    "TabbedPresenterSpec",
    "AccessibilitySequenceSpec",
    "TabBuilderSpec",
        "NotificationSpec",
    "HostApplicationConfig",
    "TelemetryConfig",
    "bootstrap_host_application",
        "build_notification_center",
    "make_window_toggle_spec",
    "make_scene_nav_action",
    "make_exit_action",
    "make_palette_toggle_action",
    "make_static_accessibility_spec",
    "build_feature_specs",
    "build_feature_window_bundle_specs",
    "build_window_toggle_specs",
    "build_scene_setup_specs",
    "build_runtime_scene_specs",
    "build_scene_root_specs",
    "build_cursor_specs",
    "build_font_role_specs",
    "build_scene_nav_actions",
    "build_action_specs",
    "build_scene_bundle_specs",
    "build_static_accessibility_specs",
    "build_host_application_config",
    # Tier 2: CORE APPLICATION
    "GuiApplication",
    "create_display",
    "SceneTransitionManager",
    "SceneTransitionStyle",
    "apply_scene_setup_specs",
    # Tier 3: DATA & STATE
    "ObservableValue",
    "PresentationModel",
    "ComputedValue",
    "InvalidationTracker",
    "ChangeKind",
    "CollectionChange",
    "ObservableList",
    "ObservableDict",
    "CollectionViewQuery",
    "CollectionView",
    "Binding",
    "BindingGroup",
    "ObservableStream",
    "SelectionModel",
    "SelectionMode",
    # Tier 4: EVENTS & ACTIONS
    "EventPhase",
    "EventType",
    "GuiEvent",
    "ValueChangeCallback",
    "ValueChangeReason",
    "EventManager",
    "EventBus",
    "GestureRecognizer",
    "EventRecorder",
    "EventPlayback",
    "RecordedEvent",
    "InputSnapshot",
    "Signal",
    "SignalConnection",
    "ActionManager",
    "ActionContext",
    "ActionMiddleware",
    "ActionDescriptor",
    "ActionRegistry",
    "InputMap",
    "InputBinding",
    "KeyChordManager",
    "KeyChord",
    "ChordStep",
    "FocusManager",
    "FocusScope",
    "FocusScopeManager",
    "WindowFocusManager",
    "FocusRing",
    # Tier 5: SCHEDULING
    "TaskEvent",
    "TaskScheduler",
    "Timers",
    "TweenManager",
    "TweenHandle",
    "Easing",
    "AnimationSequence",
    "AnimationHandle",
    "TransitionManager",
    "TransitionSpec",
    "TransitionEvent",
    "AnimationStateMachine",
    "AnimationTransitionMode",
    "SceneTimeline",
    "Debouncer",
    "Throttler",
    "CooperativeScheduler",
    "CoroutineHandle",
    "Pause",
    "Sleep",
    "WaitForEvent",
    "WaitForSignal",
    "WaitUntil",
    "WaitForAll",
    # Tier 6: THEME
    "FontManager",
    "FontRoleRegistry",
    "ColorTheme",
    "ThemeManager",
    "DesignTokens",
    "ScopedTheme",
    "ScopedThemeManager",
    # Tier 7: TELEMETRY
    "TelemetryCollector",
    "TelemetrySample",
    "configure_telemetry",
    "telemetry_collector",
    "analyze_telemetry_log_file",
    "analyze_telemetry_records",
    "load_telemetry_log_file",
    "render_telemetry_report",
    # Tier 8: LAYOUT
    "LayoutAxis",
    "ConstraintLayout",
    "AnchorConstraint",
    "DockPane",
    "DockTabs",
    "DockSplit",
    "DockWorkspace",
    "FlexLayout",
    "FlexItem",
    "FlexDirection",
    "FlexAlign",
    "FlexJustify",
    "GridLayout",
    "GridTrack",
    "GridPlacement",
    "LayoutAnimator",
    "LayoutPass",
    "MeasureContext",
    "ArrangeContext",
    "LayoutRoot",
    "FlowLayout",
    "FlowItem",
    "Viewport",
    # Tier 9: OVERLAYS
    "OverlayManager",
    "OverlayHandle",
    "Alignment",
    "PlacementResult",
    "PopupPlacement",
    "Side",
    "compute_popup_rect",
    "DialogManager",
    "DialogHandle",
    "ToastManager",
    "ToastHandle",
    "ToastSeverity",
    "ContextMenuManager",
    "ContextMenuItem",
    "ContextMenuHandle",
    "CommandPaletteManager",
    "CommandEntry",
    "CommandPaletteHandle",
    "TooltipManager",
    "TooltipHandle",
    "MenuBarManager",
    "FileDialogManager",
    "FileDialogOptions",
    "FileDialogHandle",
    "NotificationCenter",
    "NotificationRecord",
    "ResizeManager",
    "CursorManager",
    "CursorHandle",
    "CursorShape",
    "DragDropManager",
    "DragPayload",
    "ClipboardManager",
    "TransferData",
    "TransferManager",
    "ShortcutHelpOverlay",
    "ShortcutSection",
    "ShortcutEntry",
    # Tier 10: FORMS
    "FormModel",
    "FormField",
    "ValidationRule",
    "FieldError",
    "FormSchema",
    "SchemaField",
    "DocumentModel",
    "WizardFlow",
    "WizardStep",
    "WizardHandle",
    "ValidationResult",
    "Validator",
    "RequiredValidator",
    "RangeValidator",
    "LengthValidator",
    "PatternValidator",
    "CustomValidator",
    "DependentValidator",
    "ValidationPipeline",
    # Tier 11: STATE
    "CommandHistory",
    "Command",
    "CommandTransaction",
    "StateMachine",
    "HierarchicalStateMachine",
    "Router",
    "RouteEntry",
    "SettingsRegistry",
    "SettingDescriptor",
    "WorkspaceState",
    "WorkspacePersistenceManager",
    "DEFAULT_WORKSPACE_STATE_PATH",
    "SceneSnapshot",
    "NodeSnapshot",
    # Tier 12: PRIMARY CONTROLS
    "PanelControl",
    "LabelControl",
    "ButtonControl",
    "ToggleControl",
    "SliderControl",
    "ScrollbarControl",
    "CanvasControl",
    "CanvasEventPacket",
    "CanvasViewport",
    "FrameControl",
    "ImageControl",
    "ArrowBoxControl",
    "ButtonGroupControl",
    "TabControl",
    "TabItem",
    "DockWorkspacePanel",
    # Tier 13: EXTENDED CONTROLS
    "TextInputControl",
    "TextAreaControl",
    "RichLabelControl",
    "DropdownControl",
    "DropdownOption",
    "ListViewControl",
    "ListItem",
    "OverlayPanelControl",
    "DataGridControl",
    "GridColumn",
    "GridRow",
    "TreeControl",
    "TreeNode",
    "SplitterControl",
    "SpinnerControl",
    "RangeSliderControl",
    "ColorPickerControl",
    "ScrollViewControl",
    "ProgressBarControl",
    "AnimatedImageControl",
    "ErrorBoundary",
    "WindowControl",
    "TaskPanelControl",
    "WindowPresenter",
    "MenuStripControl",
    "MenuEntry",
    "SceneMenuOptions",
    "WindowMenuOptions",
    "NotificationPanelControl",
    "PropertyInspectorPanel",
    "ToolbarControl",
    "ToolbarItem",
    "StatusBarControl",
    "StatusSlot",
    "ExpanderControl",
    "DatePickerControl",
    "TimePickerControl",
    "BreadcrumbControl",
    "BreadcrumbItem",
    "SplitButtonControl",
    "SplitButtonOption",
    "ChipInputControl",
    # Tier 14: TEXT
    "TextFormatter",
    "NumericFormatter",
    "PatternFormatter",
    "FixedPatternFormatter",
    "TextFlow",
    "TextSpan",
    "TextSearcher",
    "TextMatch",
    "StringTable",
    "LocaleRegistry",
    # Tier 15: DATA
    "VirtualItemSource",
    "FixedItemSource",
    "SortFilterProxySource",
    "AsyncDataProvider",
    "LoadState",
    "LoadStateKind",
    "ObjectPool",
    "DataCache",
    "CacheStats",
    "ListDiffCalculator",
    "ListDiff",
    "DiffInsert",
    "DiffRemove",
    "DiffMove",
    # Tier 16: GRAPHICS
    "BuiltInGraphicsFactory",
    "DirtyRegionTracker",
    "DrawContext",
    "DrawPhase",
    "AssetRegistry",
    "DebugOverlay",
    "SurfaceCompositor",
    "Layer",
    "ShapeRenderer",
    "SurfaceEffects",
    "VectorPath",
    "SpriteSheet",
    "FrameAnimation",
    "ParticleSystem",
    "Emitter",
    "ParticleLayer",
    "TileSet",
    "TileMap",
    # Tier 17: INTROSPECTION
    "SceneSpatialIndex",
    "ui_property",
    "PropertyDescriptor",
    "PropertyRegistry",
    "property_registry",
    "PropertyInspectorModel",
    "InspectedProperty",
    # Tier 18: ADVANCED RUNTIME
    "FrameTimer",
    "TabPanelManager",
    "WindowRelativeRect",
    "resolve_scene_selection_callback",
    "minimize_window_menu_entries",
    "set_window_visible_state",
    "toggle_window_visibility",
    "create_anchored_feature_window",
    "add_window_menu_strip",
    "split_slot_bounds",
    "place_control",
    "place_control_unlabeled",
    "register_placed_control",
    "add_group_label",
    "PlacedControl",
    "make_labeled_slot_height_fn",
    "apply_category_visibility",
    "ControlRegistry",
    "RowCellSpec",
    "build_horizontal_row_specs",
    "build_multi_column_grid_specs",
    "build_tools_menu_entries",
    "add_standard_menu_strip",
    "add_menu_strip_from_spec",
    "apply_accessibility_sequence",
    "apply_accessibility_sequence_from_attrs",
    "register_companion_logic_features",
    "ensure_scene_scheduler",
    "sorted_window_bindings",
    "collect_window_toggle_controls",
    "apply_window_toggle_accessibility",
    "add_window_toggle_task_panel_controls",
    "add_task_panel_window_toggle_group",
    "setup_scene_command_palette_bindings",
    "register_window_toggle_tooltips",
    "initialize_locale_registry",
    "bind_input_map_actions",
    "register_descriptors",
    "resolve_canvas_local_point",
    "apply_runtime_scene_pristine_assets",
    "bind_runtime_scene_exit_keys",
    "prewarm_runtime_scenes",
    "add_task_panel_button",
    "add_task_panel_buttons",
    "register_tooltip_specs",
    "register_action_hotkeys",
    "register_global_pointer_actions",
    "draw_controls_prewarm",
    "bind_palette_window_action_bind",
    "ensure_scene_task_panel",
    "create_task_panel_slot_layout",
    "add_task_panel_scene_nav_button",
    "add_scene_task_panel_items",
    "centered_overlay_rect",
    "create_shortcut_help_overlay",
    "bind_feature_event_subscription",
    "unbind_feature_event_subscription",
    "setup_routed_runtime",
    "FeatureOperationBus",
    "FeatureOperationContext",
    "FeatureOperationHandle",
    "FeatureRuntimeScope",
    "shutdown_routed_runtime",
    "bind_task_panel_focus_toggle",
    "add_window_control",
    "add_window_label",
    "add_window_button",
    "add_window_button_row",
    "instantiate_features_from_specs",
    "register_features_from_specs",
    "register_window_presentation_specs",
    "register_window_tab_builders",
    "build_tab_builder_specs",
    "create_tab_control_from_specs",
    "compute_tabbed_window_layout",
    "setup_feature_presenter_tabs_from_window_content",
    "register_window_tab_builder_specs",
    "setup_feature_presenter_tabs",
    "register_tab_update_handlers",
    "create_presented_anchored_window",
    "create_presented_window_from_spec",
    "create_feature_presented_window",
    "configure_routed_feature_runtime",
    "register_routed_feature_companions",
    "bind_routed_feature_lifecycle",
    "shutdown_routed_feature_lifecycle",
    "ActiveTabUpdateRouter",
    "TabLayoutContext",
    "declare_host_actions",
    "build_host_main_tab_order",
    "apply_host_main_accessibility",
    # Tier 19: INFRASTRUCTURE
    "UiEngine",
    # Tier 25: SCOPED SERVICE GRAPH
    "ServiceKey",
    "ServiceScope",
    "ScopeStack",
    # Tier 26: CANCELABLE DATAFLOW PIPELINE
    "CancellationToken",
    "PipelineStage",
    "DataflowPipeline",
    "PipelineHandle",
    # Tier 27: TRANSACTIONAL APP STATE STORE
    "AppStateStore",
    "StateSelector",
    "StateTransaction",
    # Tier 28: ADAPTIVE CONSTRAINT LAYOUT v2
    "ConstraintAttr",
    "LayoutConstraint",
    "ConstraintSet",
    "AdaptivePolicy",
    "resolve_adaptive_policy",
    # Tier 29: UNIFIED VIRTUALIZATION CORE
    "MeasureMode",
    "MeasurePolicy",
    "VirtualizedWindow",
    "RecyclePool",
    "VirtualizationCore",
    # Tier 30: INTERACTION STATE MACHINE FRAMEWORK
    "InteractionPhase",
    "InteractionContext",
    "InteractionTransition",
    "InteractionStateMachine",
    # Tier 31: SCHEMA-DRIVEN FORM RUNTIME
    "FieldSchema",
    "FieldGraphSchema",
    "ValidationPolicy",
    "SchemaFormRuntime",
    # Tier 32: PORTABLE SNAPSHOT & MIGRATION LAYER
    "SchemaVersion",
    "VersionedSnapshot",
    "MigrationStep",
    "MigrationRegistry",
    "SnapshotMigrator",
    "MigrationError",
    "make_snapshot",
    "read_version",
]
