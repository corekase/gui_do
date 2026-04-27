"""GUI package entry point."""

from ._version import __version__  # noqa: F401  (re-exported for `gui.__version__`)

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
from .core.presentation_model import ObservableValue, PresentationModel
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
]
