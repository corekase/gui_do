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

from .app.gui_application import GuiApplication
from .app.display import create_display
from .app.ui_engine import UiEngine
from .controls.composite.panel_control import PanelControl
from .controls.display.label_control import LabelControl
from .controls.input.button_control import ButtonControl
from .controls.display.arrow_box_control import ArrowBoxControl
from .controls.input.button_group_control import ButtonGroupControl
from .controls.canvas.canvas_control import CanvasControl, CanvasEventPacket
from .controls.display.frame_control import FrameControl
from .controls.display.image_control import ImageControl
from .controls.input.slider_control import SliderControl
from .controls.input.scrollbar_control import ScrollbarControl
from .controls.chrome.task_panel_control import TaskPanelControl
from .controls.input.toggle_control import ToggleControl
from .controls.chrome.window_control import WindowControl
from .layout.layout_axis import LayoutAxis
from .layout.layout_manager import LayoutManager
from .layout.window_tiling_manager import WindowTilingManager
from .layout.dock_workspace import DockPane, DockTabs, DockSplit, DockWorkspace
from .controls.composite.dock_workspace_panel import DockWorkspacePanel
from .actions.action_manager import ActionManager
from .actions.action_middleware import ActionContext, ActionMiddleware
from .actions.action_registry import ActionDescriptor, ActionRegistry
from .events.event_manager import EventManager
from .events.event_bus import EventBus
from .focus.focus_manager import FocusManager
from .theme.font_manager import FontManager
from .theme.font_role_registry import FontRoleRegistry
from .events.gui_event import EventPhase, EventType, GuiEvent
from .events.value_change_callback import ValueChangeCallback
from .events.value_change_reason import ValueChangeReason
from .data.invalidation import InvalidationTracker
from .data.presentation_model import ObservableValue, PresentationModel, ComputedValue
from .scheduling.task_scheduler import TaskEvent, TaskScheduler
from .scheduling.timers import Timers
from .telemetry.telemetry import TelemetryCollector
from .telemetry.telemetry import TelemetrySample
from .telemetry.telemetry import configure_telemetry
from .telemetry.telemetry import telemetry_collector
from .telemetry.telemetry_analyzer import analyze_telemetry_log_file
from .telemetry.telemetry_analyzer import analyze_telemetry_records
from .telemetry.telemetry_analyzer import load_telemetry_log_file
from .telemetry.telemetry_analyzer import render_telemetry_report
from .graphics.built_in_factory import BuiltInGraphicsFactory
from .theme.color_theme import ColorTheme
from .features.feature_lifecycle import (
    Feature,
    DirectFeature,
    LogicFeature,
    RoutedFeature,
    FeatureMessage,
    FeatureManager,
    FrameTimer,
    TabPanelManager,
    WindowRelativeRect,
    resolve_scene_selection_callback,
    minimize_window_menu_entries,
    set_window_visible_state,
    toggle_window_visibility,
    create_anchored_feature_window,
    add_window_scene_menu_strip,
    inset_rect,
    centered_horizontal_strip_layout,
    split_slot_bounds,
    partition_canvas_area,
    place_control,
    place_control_unlabeled,
    register_placed_control,
    add_group_label,
    PlacedControl,
)
from .scheduling.tween_manager import TweenManager, TweenHandle, Easing
from .controls.input.text_input_control import TextInputControl
from .layout.constraint_layout import ConstraintLayout, AnchorConstraint
from .overlays.overlay_manager import OverlayManager, OverlayHandle
from .overlays.popup_placement import (
    Alignment,
    PlacementResult,
    PopupPlacement,
    Side,
    compute_popup_rect,
)
from .controls.composite.overlay_panel_control import OverlayPanelControl
from .controls.data.list_view_control import ListViewControl, ListItem
from .controls.input.dropdown_control import DropdownControl, DropdownOption
from .overlays.toast_manager import ToastManager, ToastHandle, ToastSeverity
from .overlays.dialog_manager import DialogManager, DialogHandle
from .overlays.drag_drop_manager import DragDropManager, DragPayload
from .forms.form_model import FormModel, FormField, ValidationRule, FieldError
from .forms.form_schema import FormSchema, SchemaField
from .state.command_history import CommandHistory, Command, CommandTransaction
from .forms.document_model import DocumentModel
from .controls.data.data_grid_control import DataGridControl, GridColumn, GridRow
from .overlays.context_menu_manager import ContextMenuManager, ContextMenuItem, ContextMenuHandle
from .controls.composite.splitter_control import SplitterControl
from .state.state_machine import StateMachine
from .persistence.settings_registry import SettingsRegistry, SettingDescriptor
from .persistence.workspace_persistence import WorkspaceState, WorkspacePersistenceManager, DEFAULT_WORKSPACE_STATE_PATH
from .state.router import Router, RouteEntry
from .theme.theme_manager import ThemeManager, DesignTokens
from .controls.input.text_area_control import TextAreaControl
from .controls.display.rich_label_control import RichLabelControl
from .controls.data.tab_control import TabControl, TabItem
from .overlays.resize_manager import ResizeManager
from .controls.chrome.menu_bar_control import MenuBarControl, MenuEntry
from .controls.chrome.scene_menu_strip_control import SceneMenuStripControl
from .overlays.menu_bar_manager import MenuBarManager
from .controls.data.tree_control import TreeControl, TreeNode
from .overlays.file_dialog_manager import FileDialogManager, FileDialogOptions, FileDialogHandle
from .layout.flex_layout import FlexLayout, FlexItem, FlexDirection, FlexAlign, FlexJustify
from .persistence.scene_transition_manager import SceneTransitionManager, SceneTransitionStyle
from .overlays.notification_center import NotificationCenter, NotificationRecord
from .controls.chrome.notification_panel_control import NotificationPanelControl
from .overlays.clipboard import ClipboardManager
from .overlays.transfer_data import TransferData, TransferManager
from .scheduling.animation_sequence import AnimationSequence, AnimationHandle
from .controls.composite.scroll_view_control import ScrollViewControl
from .controls.input.spinner_control import SpinnerControl
from .controls.input.range_slider_control import RangeSliderControl
from .controls.input.color_picker_control import ColorPickerControl
from .overlays.command_palette_manager import CommandPaletteManager, CommandEntry, CommandPaletteHandle
from .data.observable_collections import (
    ChangeKind,
    CollectionChange,
    ObservableList,
    ObservableDict,
)
from .data.collection_view import CollectionViewQuery, CollectionView
from .data.binding import Binding, BindingGroup
from .events.gesture_recognizer import GestureRecognizer
from .layout.layout_animator import LayoutAnimator
from .scheduling.rate_limiter import Debouncer, Throttler
from .layout.grid_layout import GridLayout, GridTrack, GridPlacement
from .actions.key_chord_manager import KeyChordManager, KeyChord, ChordStep
from .controls.composite.error_boundary import ErrorBoundary
from .overlays.tooltip_manager import TooltipManager, TooltipHandle
from .focus.focus_scope import FocusScope, FocusScopeManager
from .focus.window_focus_manager import WindowFocusManager
from .data.selection_model import SelectionModel, SelectionMode
from .text.text_formatter import TextFormatter, NumericFormatter, PatternFormatter, FixedPatternFormatter
from .data.virtual_item_source import VirtualItemSource, FixedItemSource
from .controls.canvas.canvas_viewport import CanvasViewport
from .scheduling.transition_manager import TransitionManager, TransitionSpec, TransitionEvent
from .theme.scoped_theme import ScopedTheme, ScopedThemeManager
from .data.async_data_provider import AsyncDataProvider, LoadState, LoadStateKind
from .layout.layout_pass import LayoutPass, MeasureContext, ArrangeContext, LayoutRoot
from .overlays.cursor_manager import CursorManager, CursorHandle, CursorShape
from .data.sort_filter_proxy import SortFilterProxySource
from .text.localization import StringTable, LocaleRegistry
from .actions.input_map import InputMap, InputBinding
from .introspection.spatial_index import SceneSpatialIndex
from .text.text_flow import TextFlow, TextSpan
from .layout.responsive_layout import ResponsiveLayout, Breakpoint
from .events.event_recorder import EventRecorder, EventPlayback, RecordedEvent
from .introspection.property_registry import ui_property, PropertyDescriptor, PropertyRegistry, property_registry
from .introspection.property_inspector import PropertyInspectorModel, InspectedProperty
from .controls.chrome.property_inspector_panel import PropertyInspectorPanel
from .persistence.scene_snapshot import SceneSnapshot, NodeSnapshot
from .graphics.dirty_region import DirtyRegionTracker
from .graphics.draw_context import DrawContext, DrawPhase
from .graphics.asset_registry import AssetRegistry
from .graphics.debug_overlay import DebugOverlay
from .events.input_snapshot import InputSnapshot
from .events.signal import Signal, SignalConnection
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
from .layout.viewport import Viewport
from .state.hierarchical_state_machine import HierarchicalStateMachine
from .focus.focus_ring import FocusRing
from .data.observable_stream import ObservableStream
from .graphics.surface_compositor import SurfaceCompositor, Layer
from .graphics.shape_renderer import ShapeRenderer
from .graphics.surface_effects import SurfaceEffects
from .scheduling.animation_state_machine import AnimationStateMachine, AnimationTransitionMode
from .data.object_pool import ObjectPool
from .graphics.vector_path import VectorPath
from .layout.snap_grid import SnapGrid, AlignmentGuide, SnapComposer, SnapTarget
from .forms.wizard_flow import WizardFlow, WizardStep, WizardHandle
from .scheduling.scene_timeline import SceneTimeline
from .graphics.particle_system import ParticleSystem, Emitter, ParticleLayer
from .graphics.sprite_sheet import SpriteSheet, FrameAnimation
from .controls.display.animated_image_control import AnimatedImageControl
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
from .graphics.tile_map import TileSet, TileMap
from .controls.display.progress_bar_control import ProgressBarControl
from .layout.flow_layout import FlowLayout, FlowItem
from .text.text_searcher import TextSearcher, TextMatch
from .data.list_diff import ListDiffCalculator, ListDiff, DiffInsert, DiffRemove, DiffMove
from .data.data_cache import DataCache, CacheStats
from .overlays.shortcut_help_overlay import ShortcutHelpOverlay, ShortcutSection, ShortcutEntry

from tests.contract_test_catalog import PUBLIC_API_EXPORT_ORDER
__all__ = list(PUBLIC_API_EXPORT_ORDER)
