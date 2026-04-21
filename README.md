# gui_do

Rebased, architecture-first pygame GUI package focused on clean interaction patterns and reliable pointer capture behavior.

## Design Rules

- One primary class per module.
- Folder hierarchy reflects GUI responsibilities.
- Pointer capture owns drag locking behavior.
- Slider and scrollbar never reposition pointer during release.
- Release ends capture only; no cursor reconciliation logic in controls.

## Package Structure

- gui/app
  - gui_application.py: GuiApplication
- gui/loop
  - ui_engine.py: UiEngine
- gui/core
  - ui_node.py: UiNode
  - scene.py: Scene
  - renderer.py: Renderer
  - input_state.py: InputState
  - pointer_capture.py: PointerCapture
- gui/controls
  - panel_control.py: PanelControl
  - frame_control.py: FrameControl
  - image_control.py: ImageControl
  - toggle_control.py: ToggleControl
  - canvas_control.py: CanvasControl
  - window_control.py: WindowControl
  - task_panel_control.py: TaskPanelControl
  - arrow_box_control.py: ArrowBoxControl
  - button_group_control.py: ButtonGroupControl
  - label_control.py: LabelControl
  - button_control.py: ButtonControl
  - slider_control.py: SliderControl
  - scrollbar_control.py: ScrollbarControl
- gui/layout
  - layout_axis.py: LayoutAxis
  - layout_manager.py: LayoutManager
- gui/core
  - task_scheduler.py: TaskScheduler, TaskEvent
  - timers.py: Timers
- gui/theme
  - color_theme.py: ColorTheme

## Install

```bash
pip install pygame
```

## Public API

```python
from gui import (
  ArrowBoxControl,
    GuiApplication,
    UiEngine,
    PanelControl,
  FrameControl,
  ImageControl,
  ToggleControl,
  CanvasControl,
  WindowControl,
  TaskPanelControl,
  ButtonGroupControl,
    LabelControl,
    ButtonControl,
    SliderControl,
    ScrollbarControl,
    LayoutAxis,
  LayoutManager,
  TaskScheduler,
  TaskEvent,
  Timers,
    ColorTheme,
)
```

## Restored Functional Surface

The rebased package now restores major pruned capabilities from pre-rebase scope while keeping rebased architecture constraints:

- Additional widget kinds: frame, image, toggle, canvas, window, task panel, arrow box, and button group.
- Layout manager helpers: grid, linear, anchor, and placement utilities.
- Scheduler service: background tasks, main-thread message callbacks, completion/failure events, and result retrieval.
- Timer service: frame-driven repeating callbacks.
- Demo integration showing scheduler, timers, task panel behavior, and expanded control set.

## Pointer-Capture Pattern

The controls follow the standard drag lifecycle:

1. Left press on handle starts drag.
2. Control acquires lock area through PointerCapture.
3. Motion uses locked pointer coordinates only.
4. Left release ends capture.
5. No internal pointer mutation on release.

This removes common end-of-drag cursor drift bugs by treating lock-area capture as the source of truth.

## Run Demo

```bash
python gui_do_demo.py
```

## Run Rebased Tests

```bash
python -m unittest tests.test_rebased_pointer_capture_contracts -v
```

## Testing Policy (Rebased Only)

- The authoritative test surface is rebased-only.
- Legacy pre-rebase tests are intentionally removed and unsupported.
- Backward compatibility with the old package layout and APIs is not provided.
- `tests/test_rebased_pointer_capture_contracts.py` is the canonical behavioral contract for pointer-capture drag/release behavior.

The demo showcases:

- Horizontal slider
- Horizontal scrollbar
- Vertical slider
- Real-time value labels
- Task panel auto-hide behavior
- Background worker progress updates through scheduler messaging
- Timer-driven UI updates
- Window and canvas controls
- Grouped button selection and arrow-box repeat behavior

## Why This Rebase

This package was restructured to align with GUI best practices for:

- explicit scene graph boundaries,
- predictable control dispatch,
- separation of input normalization and rendering,
- and robust drag behavior built on capture corridors instead of release-time cursor corrections.
