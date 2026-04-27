[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

# gui_do

gui_do is a strict-contract pygame GUI framework for building scene-driven desktop interfaces with reusable controls, runtime services, and feature composition. It gives developers a public API that combines UI controls, event/focus routing, data/state helpers, overlays, scheduling, animation, and telemetry into one coherent runtime. The package is designed for tools, editors, dashboards, and application UIs that need deterministic behavior and clear architecture boundaries.

<a id="table-of-contents"></a>

## Table of Contents

- [Quick Start](#quick-start)
- [Overview](#overview)
- [Minimal Runnable Example](#minimal-runnable-example)
- [Package Management](#package-management)
  - [Start a New Project](#start-a-new-project)
  - [Add to or Update an Existing Project](#add-to-or-update-an-existing-project)
- [Application Bootstrap](#application-bootstrap)
  - [GuiApplication](#guiapplication)
  - [UiEngine](#uiengine)
  - [Scene Management](#scene-management)
- [Controls](#controls)
  - [UiNode Pattern](#uinode-pattern)
  - [Basic Controls](#basic-controls)
  - [Value and Data Controls](#value-and-data-controls)
  - [Text Controls](#text-controls)
  - [Container Controls](#container-controls)
- [Layout](#layout)
  - [LayoutAxis](#layoutaxis)
  - [LayoutManager](#layoutmanager)
  - [WindowTilingManager](#windowtilingmanager)
  - [ConstraintLayout](#constraintlayout)
- [Events and Input](#events-and-input)
  - [GuiEvent and EventManager](#guievent-and-eventmanager)
  - [EventBus and ActionManager](#eventbus-and-actionmanager)
  - [FocusManager](#focusmanager)
- [Data and State](#data-and-state)
  - [ObservableValue and PresentationModel](#observablevalue-and-presentationmodel)
  - [FormModel](#formmodel)
  - [StateMachine and Router](#statemachine-and-router)
  - [SettingsRegistry](#settingsregistry)
- [Scheduling and Animation](#scheduling-and-animation)
  - [TaskScheduler](#taskscheduler)
  - [Timers](#timers)
  - [TweenManager](#tweenmanager)
- [Overlay, Dialog, and Interaction Services](#overlay-dialog-and-interaction-services)
  - [OverlayManager and OverlayPanelControl](#overlaymanager-and-overlaypanelcontrol)
  - [ToastManager](#toastmanager)
  - [DialogManager](#dialogmanager)
  - [DragDropManager](#dragdropmanager)
  - [ContextMenuManager](#contextmenumanager)
  - [ResizeManager](#resizemanager)
- [Feature System](#feature-system)
  - [Feature Types](#feature-types)
  - [FeatureManager](#featuremanager)
- [Theme and Graphics](#theme-and-graphics)
  - [ColorTheme and ThemeManager](#colortheme-and-thememanager)
  - [BuiltInGraphicsFactory](#builtingraphicsfactory)
  - [FontManager](#fontmanager)
- [Telemetry](#telemetry)
- [Public API Index](#public-api-index)

---

<a id="quick-start"></a>

## Quick Start - [Back to Top](#table-of-contents)

```bash
pip install gui_do
```

```python
import pygame
from pygame import Rect

from gui_do import GuiApplication, UiEngine, LabelControl

pygame.init()
surface = pygame.display.set_mode((800, 600))

app = GuiApplication(surface)
app.scene.add(LabelControl("hello", Rect(24, 24, 280, 32), "Hello, gui_do"))

UiEngine(app, target_fps=60).run()
pygame.quit()
```

---

<a id="overview"></a>

## Overview - [Back to Top](#table-of-contents)

gui_do centers around a strict scene runtime. `GuiApplication` owns all managers and exposes one active scene at a time, while each scene carries its own scheduler, timers, tweens, overlay, drag-drop service, and theme context. This lets multi-screen apps isolate behavior by scene without custom plumbing.

Controls are all `UiNode` subclasses with consistent event/update/draw semantics. Input enters through normalized `GuiEvent` objects, then routes through event dispatch, focus traversal, actions, and per-control handlers. This keeps keyboard and pointer behavior deterministic across control types.

State and logic are first-class citizens. `ObservableValue`, `PresentationModel`, `FormModel`, `CommandHistory`, and `Feature`/`FeatureManager` let developers separate domain logic from UI widgets cleanly. Overlay-oriented services (`OverlayManager`, `DialogManager`, `ToastManager`, `ContextMenuManager`, `DragDropManager`) integrate with the same scene runtime and event contracts.

gui_do is best suited for tooling, editors, dashboards, simulation frontends, and app-style UIs where composability, predictable behavior, and explicit APIs matter more than browser/web deployment.

---

<a id="minimal-runnable-example"></a>

## Minimal Runnable Example - [Back to Top](#table-of-contents)

```python
import pygame
from pygame import Rect

from gui_do import GuiApplication, UiEngine, ButtonControl, LabelControl


def main() -> None:
    pygame.init()
    surface = pygame.display.set_mode((640, 480))
    app = GuiApplication(surface)

    label = app.scene.add(LabelControl("status", Rect(20, 20, 280, 30), "Ready"))

    def on_click() -> None:
        label.text = "Clicked"

    app.scene.add(ButtonControl("click", Rect(20, 64, 120, 32), "Click", on_click=on_click))

    UiEngine(app, target_fps=60).run()
    pygame.quit()


if __name__ == "__main__":
    main()
```

---

<a id="package-management"></a>

## Package Management - [Back to Top](#table-of-contents)

`gui_do` ships with `scripts/manage.py` for repository bootstrap/update workflows. The command supports `init`, `apply`, `verify`, `check`, and `update`.

<a id="start-a-new-project"></a>

### Start a New Project - [Back to Top](#table-of-contents)

Use this when you cloned/downloaded the gui_do repository and want a clean, library-first base:

```bash
python scripts/manage.py init --verify
```

Optional starter scaffold:

```bash
python scripts/manage.py init --scaffold --scaffold-file myapp.py --scaffold-package features --verify
```

Useful flags:

- `--dry-run` previews changes
- `--skip-doc-sync` skips README/docs parity rewrites
- `--skip-workflow-sync` skips CI workflow sync

<a id="add-to-or-update-an-existing-project"></a>

### Add to or Update an Existing Project - [Back to Top](#table-of-contents)

Validate a target project first:

```bash
python scripts/manage.py check --target D:/Code/my_app
```

Then update/copy library assets into that project:

```bash
python scripts/manage.py update --target D:/Code/my_app --verify
```

`update` syncs library-only directories/files and runs `apply` in the target.

---

<a id="application-bootstrap"></a>

## Application Bootstrap - [Back to Top](#table-of-contents)

<a id="guiapplication"></a>

### GuiApplication - [Back to Top](#table-of-contents)

`GuiApplication(surface)` is the runtime root. It hosts scenes, controls, managers, and rendering.

```python
import pygame
from gui_do import GuiApplication

pygame.init()
surface = pygame.display.set_mode((1024, 720))
app = GuiApplication(surface)
```

Important app-level public services include:

- Scene/runtime: `scene`, `create_scene`, `switch_scene`, `scene_names`
- Lifecycle loop: `process_event`, `update`, `draw`, `run`, `shutdown`
- Interaction/services: `focus`, `events`, `actions`, `overlay`, `toasts`, `dialogs`, `drag_drop`
- State/services: `scheduler`, `timers`, `tweens`, `features`, `window_tiling`, `layout`
- Theme/graphics: `theme`, `graphics_factory`

<a id="uiengine"></a>

### UiEngine - [Back to Top](#table-of-contents)

`UiEngine(app, target_fps=60)` runs the main loop and calls app lifecycle methods.

```python
from gui_do import UiEngine

engine = UiEngine(app, target_fps=60)
engine.run(max_frames=None)
```

<a id="scene-management"></a>

### Scene Management - [Back to Top](#table-of-contents)

```python
app.create_scene("main")
app.create_scene("settings")
app.switch_scene("settings")

print(app.active_scene_name)
print(app.scene_names())
```

Only the active scene receives updates/input. Scene-local runtime systems are isolated by design.

---

<a id="controls"></a>

## Controls - [Back to Top](#table-of-contents)

<a id="uinode-pattern"></a>

### UiNode Pattern - [Back to Top](#table-of-contents)

All built-in controls inherit from `UiNode` and share:

- identity and geometry: `control_id`, `rect`
- visibility and interaction: `visible`, `enabled`, `tab_index`
- tree operations: `add(child)`, `remove(child)`, `children`, `parent`
- invalidation and accessibility: `invalidate()`, `set_accessibility(...)`

<a id="basic-controls"></a>

### Basic Controls - [Back to Top](#table-of-contents)

- `PanelControl(control_id, rect, draw_background=True, constraints=None)`
- `LabelControl(control_id, rect, text, align="left")`
- `ButtonControl(control_id, rect, text, on_click=None, style="box", font_role="body")`
- `ToggleControl(control_id, rect, text_on, text_off=None, pushed=False, on_toggle=None, style="box", font_role="body")`
- `ArrowBoxControl(control_id, rect, direction, on_activate=None, repeat_interval_seconds=0.08)`
- `ButtonGroupControl(control_id, rect, group, text, selected=False, style="box", on_activate=None, font_role="body")`

```python
from pygame import Rect
from gui_do import ButtonControl, ToggleControl, ArrowBoxControl

app.scene.add(ButtonControl("save", Rect(20, 20, 120, 32), "Save"))
app.scene.add(ToggleControl("power", Rect(20, 60, 140, 32), "On", "Off", pushed=False))
app.scene.add(ArrowBoxControl("right", Rect(20, 100, 32, 32), 0))
```

<a id="value-and-data-controls"></a>

### Value and Data Controls - [Back to Top](#table-of-contents)

- `SliderControl(control_id, rect, axis, minimum, maximum, value, on_change=None)`
- `ScrollbarControl(control_id, rect, axis, content_size, viewport_size, offset=0, step=16, on_change=None)`
- `ListViewControl(control_id, rect, items=None, *, row_height=28, selected_index=-1, on_select=None, multi_select=False, show_scrollbar=True, font_role="medium")`
- `DropdownControl(control_id, rect, options=None, *, selected_index=-1, on_change=None, placeholder="Select...", font_role="medium", max_visible_items=8)`
- `DataGridControl(control_id, rect, columns=None, rows=None, *, row_height=26, show_scrollbar=True, font_role="medium", on_select=None, on_sort=None)`

```python
from pygame import Rect
from gui_do import LayoutAxis, SliderControl, GridColumn, GridRow, DataGridControl

app.scene.add(SliderControl("zoom", Rect(20, 150, 240, 24), LayoutAxis.HORIZONTAL, 0.0, 100.0, 25.0))
app.scene.add(
    DataGridControl(
        "grid",
        Rect(20, 190, 420, 180),
        columns=[GridColumn("name", "Name"), GridColumn("value", "Value")],
        rows=[GridRow({"name": "Alpha", "value": 1})],
    )
)
```

<a id="text-controls"></a>

### Text Controls - [Back to Top](#table-of-contents)

- `TextInputControl(control_id, rect, value="", placeholder="", max_length=None, masked=False, on_change=None, on_submit=None, font_role="body")`
- `TextAreaControl(control_id, rect, value="", placeholder="", max_length=None, read_only=False, on_change=None, font_role="body", font_size=16)`
- `RichLabelControl(control_id, rect, text="", font_role="body", font_size=16, align="left", color=None)`

`RichLabelControl` supports inline style markers in text:

- `**bold**`
- `_italic_`
- `` `code` ``
- nested `**_bold+italic_**`

<a id="container-controls"></a>

### Container Controls - [Back to Top](#table-of-contents)

- `CanvasControl(control_id, rect, max_events=256)`
- `FrameControl(control_id, rect, border_width=1)`
- `ImageControl(control_id, rect, image_path, scale=True)` (`image_path` accepts `str | Path | pygame.Surface`)
- `WindowControl(...)` for draggable titled windows
- `SplitterControl(...)` for two-pane layouts
- `TaskPanelControl(...)` for auto-hide task strips
- `OverlayPanelControl(control_id, rect, draw_background=True, constraints=None)`
- `TabControl(control_id, rect, items=None, selected_key=None, on_change=None, font_role="body", font_size=16)` with `TabItem`

---

<a id="layout"></a>

## Layout - [Back to Top](#table-of-contents)

<a id="layoutaxis"></a>

### LayoutAxis - [Back to Top](#table-of-contents)

`LayoutAxis.HORIZONTAL` and `LayoutAxis.VERTICAL` are used by controls and layout helpers.

<a id="layoutmanager"></a>

### LayoutManager - [Back to Top](#table-of-contents)

`app.layout` provides linear/grid placement helpers.

```python
app.layout.set_grid_properties(anchor=(20, 20), item_width=120, item_height=32, column_spacing=8, row_spacing=8)
rect = app.layout.grid(1, 2)
```

<a id="windowtilingmanager"></a>

### WindowTilingManager - [Back to Top](#table-of-contents)

`app.window_tiling` manages window registration and tiling behavior for scene windows.

<a id="constraintlayout"></a>

### ConstraintLayout - [Back to Top](#table-of-contents)

`ConstraintLayout` and `AnchorConstraint` support anchor-driven constraints for container-child positioning.

---

<a id="events-and-input"></a>

## Events and Input - [Back to Top](#table-of-contents)

<a id="guievent-and-eventmanager"></a>

### GuiEvent and EventManager - [Back to Top](#table-of-contents)

Raw pygame events are normalized into `GuiEvent` at ingress. Use semantic helpers like:

- `event.is_key_down(...)`
- `event.is_mouse_down(...)`
- `event.is_mouse_up(...)`
- `event.is_mouse_motion()`
- `event.is_mouse_wheel()`

<a id="eventbus-and-actionmanager"></a>

### EventBus and ActionManager - [Back to Top](#table-of-contents)

- `EventBus` provides scoped publish/subscribe messaging.
- `ActionManager` binds keyboard inputs to named actions.

<a id="focusmanager"></a>

### FocusManager - [Back to Top](#table-of-contents)

`FocusManager` owns keyboard focus and Tab traversal order by `tab_index`.

---

<a id="data-and-state"></a>

## Data and State - [Back to Top](#table-of-contents)

<a id="observablevalue-and-presentationmodel"></a>

### ObservableValue and PresentationModel - [Back to Top](#table-of-contents)

Use `ObservableValue` for reactive fields and `PresentationModel` as a model base.

<a id="formmodel"></a>

### FormModel - [Back to Top](#table-of-contents)

`FormModel`, `FormField`, `ValidationRule`, and `FieldError` provide form-state and validation workflows.

<a id="statemachine-and-router"></a>

### StateMachine and Router - [Back to Top](#table-of-contents)

- `StateMachine(initial_state)` coordinates explicit state transitions.
- `Router` with `RouteEntry` supports route/table-style navigation logic.

<a id="settingsregistry"></a>

### SettingsRegistry - [Back to Top](#table-of-contents)

`SettingsRegistry` with `SettingDescriptor` stores and loads namespaced settings.

---

<a id="scheduling-and-animation"></a>

## Scheduling and Animation - [Back to Top](#table-of-contents)

<a id="taskscheduler"></a>

### TaskScheduler - [Back to Top](#table-of-contents)

`TaskScheduler(max_workers=4)` executes background work and emits `TaskEvent` updates back to UI runtime.

<a id="timers"></a>

### Timers - [Back to Top](#table-of-contents)

`Timers` schedules one-shot and repeating callbacks in frame time.

<a id="tweenmanager"></a>

### TweenManager - [Back to Top](#table-of-contents)

`TweenManager` animates properties via `TweenHandle` and `Easing` curves.

---

<a id="overlay-dialog-and-interaction-services"></a>

## Overlay, Dialog, and Interaction Services - [Back to Top](#table-of-contents)

<a id="overlaymanager-and-overlaypanelcontrol"></a>

### OverlayManager and OverlayPanelControl - [Back to Top](#table-of-contents)

Use `OverlayManager` with `OverlayHandle` to show/dismiss floating UI nodes (often `OverlayPanelControl`).

<a id="toastmanager"></a>

### ToastManager - [Back to Top](#table-of-contents)

`ToastManager` handles transient notifications with `ToastHandle` and `ToastSeverity`.

<a id="dialogmanager"></a>

### DialogManager - [Back to Top](#table-of-contents)

`DialogManager` and `DialogHandle` provide modal alert/confirm/prompt flows.

<a id="dragdropmanager"></a>

### DragDropManager - [Back to Top](#table-of-contents)

`DragDropManager` coordinates drag sessions using typed `DragPayload` objects.

<a id="contextmenumanager"></a>

### ContextMenuManager - [Back to Top](#table-of-contents)

`ContextMenuManager` displays context menus via `ContextMenuItem` and `ContextMenuHandle`.

<a id="resizemanager"></a>

### ResizeManager - [Back to Top](#table-of-contents)

`ResizeManager` centralizes resize handling callbacks for app and scene geometry changes.

---

<a id="feature-system"></a>

## Feature System - [Back to Top](#table-of-contents)

<a id="feature-types"></a>

### Feature Types - [Back to Top](#table-of-contents)

- `Feature`
- `DirectFeature`
- `LogicFeature`
- `RoutedFeature`
- `FeatureMessage`

These types organize UI logic by lifecycle and message routing contracts.

<a id="featuremanager"></a>

### FeatureManager - [Back to Top](#table-of-contents)

`FeatureManager` registers features, dispatches lifecycle hooks, and supports feature-to-feature messaging and bindings.

---

<a id="theme-and-graphics"></a>

## Theme and Graphics - [Back to Top](#table-of-contents)

<a id="colortheme-and-thememanager"></a>

### ColorTheme and ThemeManager - [Back to Top](#table-of-contents)

- `ColorTheme` supplies colors and text rendering.
- `ThemeManager` and `DesignTokens` provide theme switching/token workflows.

<a id="builtingraphicsfactory"></a>

### BuiltInGraphicsFactory - [Back to Top](#table-of-contents)

`BuiltInGraphicsFactory` constructs cached control visuals used across built-in controls.

<a id="fontmanager"></a>

### FontManager - [Back to Top](#table-of-contents)

`FontManager` defines role-based fonts and renders text by role.

---

<a id="telemetry"></a>

## Telemetry - [Back to Top](#table-of-contents)

Public telemetry exports:

- `TelemetryCollector`
- `TelemetrySample`
- `configure_telemetry`
- `telemetry_collector`
- `analyze_telemetry_records`
- `analyze_telemetry_log_file`
- `load_telemetry_log_file`
- `render_telemetry_report`

These support runtime metrics capture and post-run analysis/report generation.

---

<a id="public-api-index"></a>

## Public API Index - [Back to Top](#table-of-contents)

The following is the current public export surface from `gui_do.__all__`.

### Application and Loop

- `GuiApplication`
- `UiEngine`

### Controls

- `PanelControl`
- `LabelControl`
- `ButtonControl`
- `ArrowBoxControl`
- `ButtonGroupControl`
- `CanvasControl`
- `CanvasEventPacket`
- `FrameControl`
- `ImageControl`
- `SliderControl`
- `ScrollbarControl`
- `TaskPanelControl`
- `ToggleControl`
- `WindowControl`
- `TextInputControl`
- `OverlayPanelControl`
- `ListViewControl`
- `ListItem`
- `DropdownControl`
- `DropdownOption`
- `DataGridControl`
- `GridColumn`
- `GridRow`
- `SplitterControl`
- `TextAreaControl`
- `RichLabelControl`
- `TabControl`
- `TabItem`

### Layout

- `LayoutAxis`
- `LayoutManager`
- `WindowTilingManager`
- `ConstraintLayout`
- `AnchorConstraint`

### Events, Focus, and Input

- `ActionManager`
- `EventManager`
- `EventBus`
- `FocusManager`
- `FontManager`
- `EventPhase`
- `EventType`
- `GuiEvent`

### Value Change Contracts

- `ValueChangeCallback`
- `ValueChangeReason`

### Core Runtime Services

- `InvalidationTracker`
- `ObservableValue`
- `PresentationModel`
- `TaskEvent`
- `TaskScheduler`
- `Timers`
- `OverlayManager`
- `OverlayHandle`
- `ToastManager`
- `ToastHandle`
- `ToastSeverity`
- `DialogManager`
- `DialogHandle`
- `DragDropManager`
- `DragPayload`
- `FormModel`
- `FormField`
- `ValidationRule`
- `FieldError`
- `CommandHistory`
- `Command`
- `CommandTransaction`
- `ContextMenuManager`
- `ContextMenuItem`
- `ContextMenuHandle`
- `StateMachine`
- `SettingsRegistry`
- `SettingDescriptor`
- `Router`
- `RouteEntry`
- `ResizeManager`

### Features

- `Feature`
- `DirectFeature`
- `LogicFeature`
- `RoutedFeature`
- `FeatureMessage`
- `FeatureManager`

### Animation

- `TweenManager`
- `TweenHandle`
- `Easing`

### Theme and Graphics

- `BuiltInGraphicsFactory`
- `ColorTheme`
- `ThemeManager`
- `DesignTokens`

### Telemetry and Analysis

- `TelemetryCollector`
- `TelemetrySample`
- `configure_telemetry`
- `telemetry_collector`
- `analyze_telemetry_records`
- `analyze_telemetry_log_file`
- `load_telemetry_log_file`
- `render_telemetry_report`

