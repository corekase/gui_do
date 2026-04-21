"""Rebased GUI package entry point."""

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
from .core.task_scheduler import TaskEvent, TaskScheduler
from .core.timers import Timers
from .graphics.built_in_factory import BuiltInGraphicsFactory
from .theme.color_theme import ColorTheme

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
    "TaskEvent",
    "TaskScheduler",
    "Timers",
    "BuiltInGraphicsFactory",
    "ColorTheme",
]
