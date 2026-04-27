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
from .loop.ui_engine import UiEngine
from .controls.panel_control import PanelControl
from .controls.label_control import LabelControl
from .controls.button_control import ButtonControl
from .controls.arrow_box_control import ArrowBoxControl
from .controls.button_group_control import ButtonGroupControl
from .controls.canvas_control import CanvasControl, CanvasEventPacket
from .controls.frame_control import FrameControl
from .controls.image_control import ImageControl
from .controls.slider_control import SliderControl
from .controls.scrollbar_control import ScrollbarControl
from .controls.task_panel_control import TaskPanelControl
from .controls.toggle_control import ToggleControl
from .controls.window_control import WindowControl
from .layout.layout_axis import LayoutAxis
from .layout.layout_manager import LayoutManager
from .layout.window_tiling_manager import WindowTilingManager
from .core.action_manager import ActionManager
from .core.event_manager import EventManager
from .core.event_bus import EventBus
from .core.focus_manager import FocusManager
from .core.font_manager import FontManager
from .core.gui_event import EventPhase, EventType, GuiEvent
from .core.value_change_callback import ValueChangeCallback
from .core.value_change_reason import ValueChangeReason
from .core.invalidation import InvalidationTracker
from .core.presentation_model import ObservableValue, PresentationModel, ComputedValue
from .core.task_scheduler import TaskEvent, TaskScheduler
from .core.timers import Timers
from .core.telemetry import TelemetryCollector
from .core.telemetry import TelemetrySample
from .core.telemetry import configure_telemetry
from .core.telemetry import telemetry_collector
from .core.telemetry_analyzer import analyze_telemetry_log_file
from .core.telemetry_analyzer import analyze_telemetry_records
from .core.telemetry_analyzer import load_telemetry_log_file
from .core.telemetry_analyzer import render_telemetry_report
from .graphics.built_in_factory import BuiltInGraphicsFactory
from .theme.color_theme import ColorTheme
from .core.feature_lifecycle import (
    Feature,
    DirectFeature,
    LogicFeature,
    RoutedFeature,
    FeatureMessage,
    FeatureManager,
)
from .core.tween_manager import TweenManager, TweenHandle, Easing
from .controls.text_input_control import TextInputControl
from .layout.constraint_layout import ConstraintLayout, AnchorConstraint
from .core.overlay_manager import OverlayManager, OverlayHandle
from .controls.overlay_panel_control import OverlayPanelControl
from .controls.list_view_control import ListViewControl, ListItem
from .controls.dropdown_control import DropdownControl, DropdownOption
from .core.toast_manager import ToastManager, ToastHandle, ToastSeverity
from .core.dialog_manager import DialogManager, DialogHandle
from .core.drag_drop_manager import DragDropManager, DragPayload
from .core.form_model import FormModel, FormField, ValidationRule, FieldError
from .core.command_history import CommandHistory, Command, CommandTransaction
from .controls.data_grid_control import DataGridControl, GridColumn, GridRow
from .core.context_menu_manager import ContextMenuManager, ContextMenuItem, ContextMenuHandle
from .controls.splitter_control import SplitterControl
from .core.state_machine import StateMachine
from .core.settings_registry import SettingsRegistry, SettingDescriptor
from .core.router import Router, RouteEntry
from .theme.theme_manager import ThemeManager, DesignTokens
from .controls.text_area_control import TextAreaControl
from .controls.rich_label_control import RichLabelControl
from .controls.tab_control import TabControl, TabItem
from .core.resize_manager import ResizeManager
from .controls.menu_bar_control import MenuBarControl, MenuEntry
from .core.menu_bar_manager import MenuBarManager
from .controls.tree_control import TreeControl, TreeNode
from .core.file_dialog_manager import FileDialogManager, FileDialogOptions, FileDialogHandle
from .layout.flex_layout import FlexLayout, FlexItem, FlexDirection, FlexAlign, FlexJustify
from .core.scene_transition_manager import SceneTransitionManager, SceneTransitionStyle
from .core.notification_center import NotificationCenter, NotificationRecord
from .controls.notification_panel_control import NotificationPanelControl
from .core.clipboard import ClipboardManager
from .core.animation_sequence import AnimationSequence, AnimationHandle
from .controls.scroll_view_control import ScrollViewControl
from .controls.spinner_control import SpinnerControl
from .controls.range_slider_control import RangeSliderControl
from .controls.color_picker_control import ColorPickerControl
from .core.command_palette_manager import CommandPaletteManager, CommandEntry, CommandPaletteHandle

__all__ = [
    "GuiApplication",
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
    "ActionManager",
    "EventManager",
    "EventBus",
    "FocusManager",
    "FontManager",
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
    "CommandHistory",
    "Command",
    "CommandTransaction",
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
    "AnimationSequence",
    "AnimationHandle",
    "ScrollViewControl",
    "SpinnerControl",
    "RangeSliderControl",
    "ColorPickerControl",
    "CommandPaletteManager",
    "CommandEntry",
    "CommandPaletteHandle",
]
