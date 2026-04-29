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
)
from .scheduling.tween_manager import TweenManager, TweenHandle, Easing
from .controls.input.text_input_control import TextInputControl
from .layout.constraint_layout import ConstraintLayout, AnchorConstraint
from .overlays.overlay_manager import OverlayManager, OverlayHandle
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

__all__ = [
    "GuiApplication",
    "create_display",
    "UiEngine",
    "PanelControl",
    "LabelControl",
    "ButtonControl",
    "ArrowBoxControl",
    "ButtonGroupControl",
    "CanvasControl",
    "CanvasEventPacket",
    "FrameControl",
    "ImageControl",
    "SliderControl",
    "ScrollbarControl",
    "TaskPanelControl",
    "ToggleControl",
    "WindowControl",
    "LayoutAxis",
    "LayoutManager",
    "WindowTilingManager",
    "DockPane",
    "DockTabs",
    "DockSplit",
    "DockWorkspace",
    "DockWorkspacePanel",
    "ActionManager",
    "ActionDescriptor",
    "ActionRegistry",
    "EventManager",
    "EventBus",
    "FocusManager",
    "FontManager",
    "FontRoleRegistry",
    "EventPhase",
    "EventType",
    "GuiEvent",
    "ValueChangeCallback",
    "ValueChangeReason",
    "InvalidationTracker",
    "ObservableValue",
    "PresentationModel",
    "ComputedValue",
    "TaskEvent",
    "TaskScheduler",
    "Timers",
    "TelemetryCollector",
    "TelemetrySample",
    "configure_telemetry",
    "telemetry_collector",
    "analyze_telemetry_records",
    "analyze_telemetry_log_file",
    "load_telemetry_log_file",
    "render_telemetry_report",
    "BuiltInGraphicsFactory",
    "ColorTheme",
    "Feature",
    "DirectFeature",
    "LogicFeature",
    "RoutedFeature",
    "FeatureMessage",
    "FeatureManager",
    "TweenManager",
    "TweenHandle",
    "Easing",
    "TextInputControl",
    "ConstraintLayout",
    "AnchorConstraint",
    "OverlayManager",
    "OverlayHandle",
    "OverlayPanelControl",
    "ListViewControl",
    "ListItem",
    "DropdownControl",
    "DropdownOption",
    "ToastManager",
    "ToastHandle",
    "ToastSeverity",
    "DialogManager",
    "DialogHandle",
    "DragDropManager",
    "DragPayload",
    "FormModel",
    "FormField",
    "ValidationRule",
    "FieldError",
    "FormSchema",
    "SchemaField",
    "CommandHistory",
    "Command",
    "CommandTransaction",
    "DocumentModel",
    "DataGridControl",
    "GridColumn",
    "GridRow",
    "ContextMenuManager",
    "ContextMenuItem",
    "ContextMenuHandle",
    "SplitterControl",
    "StateMachine",
    "SettingsRegistry",
    "SettingDescriptor",
    "WorkspaceState",
    "WorkspacePersistenceManager",
    "DEFAULT_WORKSPACE_STATE_PATH",
    "Router",
    "RouteEntry",
    "ThemeManager",
    "DesignTokens",
    "TextAreaControl",
    "RichLabelControl",
    "TabControl",
    "TabItem",
    "ResizeManager",
    "MenuBarControl",
    "MenuEntry",
    "SceneMenuStripControl",
    "MenuBarManager",
    "TreeControl",
    "TreeNode",
    "FileDialogManager",
    "FileDialogOptions",
    "FileDialogHandle",
    "FlexLayout",
    "FlexItem",
    "FlexDirection",
    "FlexAlign",
    "FlexJustify",
    "SceneTransitionManager",
    "SceneTransitionStyle",
    "NotificationCenter",
    "NotificationRecord",
    "NotificationPanelControl",
    "ClipboardManager",
    "TransferData",
    "TransferManager",
    "AnimationSequence",
    "AnimationHandle",
    "ScrollViewControl",
    "SpinnerControl",
    "RangeSliderControl",
    "ColorPickerControl",
    "CommandPaletteManager",
    "CommandEntry",
    "CommandPaletteHandle",
    "ChangeKind",
    "CollectionChange",
    "ObservableList",
    "ObservableDict",
    "CollectionViewQuery",
    "CollectionView",
    "Binding",
    "BindingGroup",
    "GestureRecognizer",
    "LayoutAnimator",
    "Debouncer",
    "Throttler",
    "GridLayout",
    "GridTrack",
    "GridPlacement",
    "KeyChordManager",
    "KeyChord",
    "ChordStep",
    "ErrorBoundary",
    "TooltipManager",
    "TooltipHandle",
    "FocusScope",
    "FocusScopeManager",
    "SelectionModel",
    "SelectionMode",
    "TextFormatter",
    "NumericFormatter",
    "PatternFormatter",
    "FixedPatternFormatter",
    "VirtualItemSource",
    "FixedItemSource",
    "CanvasViewport",
    "TransitionManager",
    "TransitionSpec",
    "TransitionEvent",
    "ScopedTheme",
    "ScopedThemeManager",
    "AsyncDataProvider",
    "LoadState",
    "LoadStateKind",
    "LayoutPass",
    "MeasureContext",
    "ArrangeContext",
    "LayoutRoot",
    "CursorManager",
    "CursorHandle",
    "CursorShape",
    "SortFilterProxySource",
    "StringTable",
    "LocaleRegistry",
    "InputMap",
    "InputBinding",
    "SceneSpatialIndex",
    "TextFlow",
    "TextSpan",
    "ResponsiveLayout",
    "Breakpoint",
    "EventRecorder",
    "EventPlayback",
    "RecordedEvent",
    "ui_property",
    "PropertyDescriptor",
    "PropertyRegistry",
    "PropertyInspectorModel",
    "InspectedProperty",
    "PropertyInspectorPanel",
    "property_registry",
    "SceneSnapshot",
    "NodeSnapshot",
]
