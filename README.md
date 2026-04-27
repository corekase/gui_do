[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

# gui_do

gui_do is a pygame GUI toolkit for building scene-driven desktop applications with one package-level public API for controls, layout, input routing, background work, overlays, theming, state, and feature composition. It is designed for tools, editors, dashboards, simulation frontends, and other application UIs that benefit from explicit runtime services and reusable widgets. The exported surface in `gui_do.__all__` is the authoritative public boundary.

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
  - [Display and Container Controls](#display-and-container-controls)
  - [Text Controls](#text-controls)
  - [Selection, Range, and Data Controls](#selection-range-and-data-controls)
  - [Canvas, Scroll, and Advanced Inputs](#canvas-scroll-and-advanced-inputs)
- [Layout](#layout)
  - [LayoutAxis](#layoutaxis)
  - [LayoutManager](#layoutmanager)
  - [ConstraintLayout](#constraintlayout)
  - [FlexLayout](#flexlayout)
  - [WindowTilingManager](#windowtilingmanager)
- [Events and Input](#events-and-input)
  - [GuiEvent and EventManager](#guievent-and-eventmanager)
  - [EventBus](#eventbus)
  - [ActionManager](#actionmanager)
  - [FocusManager](#focusmanager)
  - [ValueChangeReason and ValueChangeCallback](#valuechangereason-and-valuechangecallback)
- [Data and State](#data-and-state)
  - [ObservableValue, ComputedValue, and PresentationModel](#observablevalue-computedvalue-and-presentationmodel)
  - [InvalidationTracker](#invalidationtracker)
  - [FormModel](#formmodel)
  - [CommandHistory](#commandhistory)
  - [StateMachine and Router](#statemachine-and-router)
  - [SettingsRegistry](#settingsregistry)
- [Scheduling and Animation](#scheduling-and-animation)
  - [TaskScheduler](#taskscheduler)
  - [Timers](#timers)
  - [TweenManager](#tweenmanager)
  - [AnimationSequence](#animationsequence)
- [Overlay and Runtime Services](#overlay-and-runtime-services)
  - [OverlayManager and OverlayHandle](#overlaymanager-and-overlayhandle)
  - [ToastManager and ToastHandle](#toastmanager-and-toasthandle)
  - [DialogManager and DialogHandle](#dialogmanager-and-dialoghandle)
  - [ContextMenuManager and ContextMenuHandle](#contextmenumanager-and-contextmenuhandle)
  - [DragDropManager and DragPayload](#dragdropmanager-and-dragpayload)
  - [FileDialogManager, FileDialogOptions, and FileDialogHandle](#filedialogmanager-filedialogoptions-and-filedialoghandle)
  - [ResizeManager](#resizemanager)
  - [ClipboardManager](#clipboardmanager)
  - [CommandPaletteManager, CommandEntry, and CommandPaletteHandle](#commandpalettemanager-commandentry-and-commandpalettehandle)
- [Menu System](#menu-system)
  - [MenuBarControl and MenuEntry](#menubarcontrol-and-menuentry)
  - [MenuBarManager](#menubarmanager)
- [Notification System](#notification-system)
  - [NotificationCenter and NotificationRecord](#notificationcenter-and-notificationrecord)
  - [NotificationPanelControl](#notificationpanelcontrol)
- [Scene Transitions](#scene-transitions)
  - [SceneTransitionManager and SceneTransitionStyle](#scenetransitionmanager-and-scenetransitionstyle)
- [Feature System](#feature-system)
  - [Feature Types and FeatureMessage](#feature-types-and-featuremessage)
  - [FeatureManager](#featuremanager)
- [Theme and Graphics](#theme-and-graphics)
  - [ColorTheme](#colortheme)
  - [ThemeManager and DesignTokens](#thememanager-and-designtokens)
  - [BuiltInGraphicsFactory](#builtingraphicsfactory)
  - [FontManager](#fontmanager)
- [Telemetry](#telemetry)
- [Public API Index](#public-api-index)

---

## Quick Start [Back to Top](#table-of-contents)

```bash
pip install gui_do
```

```python
import pygame
from pygame import Rect
from gui_do import GuiApplication, LabelControl, UiEngine

pygame.init()
surface = pygame.display.set_mode((800, 600))
app = GuiApplication(surface)
app.scene.add(LabelControl("hello", Rect(24, 24, 280, 32), "Hello, gui_do"))
UiEngine(app, target_fps=60).run()
pygame.quit()
```

---

## Overview [Back to Top](#table-of-contents)

gui_do centers everything around a `GuiApplication` and one active scene. The application owns scene-local services such as scheduling, timers, tweens, overlays, drag-drop, and window tiling, while controls form a scene graph that receives normalized `GuiEvent` input and renders against a `ColorTheme` plus `BuiltInGraphicsFactory`.

The exported package surface combines four layers that are often split across separate libraries: controls and layout primitives, runtime services and overlays, data/state helpers, and lifecycle-managed feature composition. That makes gui_do a good fit for desktop-style interfaces where predictable event routing, reusable widgets, and explicit application structure matter more than document-style layout.

---

## Minimal Runnable Example [Back to Top](#table-of-contents)

```python
import pygame
from pygame import Rect
from gui_do import ButtonControl, GuiApplication, LabelControl, UiEngine


def main() -> None:
    pygame.init()
    surface = pygame.display.set_mode((640, 480))
    app = GuiApplication(surface)

    status = app.scene.add(LabelControl("status", Rect(20, 20, 220, 30), "Ready"))

    def on_click() -> None:
        status.text = "Clicked"

    app.scene.add(ButtonControl("go", Rect(20, 64, 120, 32), "Click", on_click=on_click))
    UiEngine(app, target_fps=60).run()
    pygame.quit()


if __name__ == "__main__":
    main()
```

---

## Package Management [Back to Top](#table-of-contents)

The repository includes `scripts/manage.py` for consumer-project bootstrap and upgrade flows. The tool supports `init`, `apply`, `verify`, `check`, and `update` so a developer can start from a clean library-first checkout or sync a newer gui_do version into an existing project.

### Start a New Project [Back to Top](#table-of-contents)

Use `init` in a cloned or downloaded gui_do repository when you want to strip bundled demo content and keep the library plus its support files:

```bash
python scripts/manage.py init --verify
```

Optional scaffold generation:

```bash
python scripts/manage.py init --scaffold --scaffold-file myapp.py --scaffold-package features --verify
```

Useful flags:

- `--dry-run` previews changes.
- `--skip-doc-sync` skips README and docs synchronization.
- `--skip-workflow-sync` skips CI workflow synchronization.

### Add to or Update an Existing Project [Back to Top](#table-of-contents)

Use `check` before copying gui_do into another project:

```bash
python scripts/manage.py check --target D:/Code/my_app
```

Then use `update` to copy the current library-only directories and root files into the target project and run `apply` there:

```bash
python scripts/manage.py update --target D:/Code/my_app --verify
```

The update flow copies `gui_do/`, `scripts/`, `tests/`, `docs/`, `README.md`, and the packaging files that define the public package contract.

---

## Application Bootstrap [Back to Top](#table-of-contents)

### GuiApplication [Back to Top](#table-of-contents)

`GuiApplication(surface)` is the runtime root. It owns the active scene, scene-local services, event normalization, rendering orchestration, and feature coordination.

```python
import pygame
from gui_do import GuiApplication

pygame.init()
surface = pygame.display.set_mode((1024, 720))
app = GuiApplication(surface)
```

Common application properties:

| Attribute | Type | Notes |
|---|---|---|
| `app.scene` | scene root | Active scene graph root |
| `app.focus` | `FocusManager` | Keyboard focus and traversal |
| `app.actions` | `ActionManager` | Key-to-action routing |
| `app.events` | `EventBus` | Pub/sub messaging |
| `app.scheduler` | `TaskScheduler` | Scene-local background tasks |
| `app.timers` | `Timers` | Scene-local frame timers |
| `app.tweens` | `TweenManager` | Scene-local tween animation |
| `app.overlay` | `OverlayManager` | Overlay stack |
| `app.drag_drop` | `DragDropManager` | Drag session state |
| `app.layout` | `LayoutManager` | Grid placement helper |
| `app.window_tiling` | `WindowTilingManager` | Floating-window tiling |
| `app.theme` | `ColorTheme` | Active theme object |
| `app.graphics_factory` | `BuiltInGraphicsFactory` | Cached built-in visuals |
| `app.features` | `FeatureManager` | Feature registration and lifecycle |
| `app.toasts` | `ToastManager` | App-level toast banners |
| `app.dialogs` | `DialogManager` | Lazy modal dialog service |

Common application methods:

- `app.add(node, scene_name=None)` adds a root node to the active or named scene.
- `app.create_scene(name)` creates or returns a named scene.
- `app.switch_scene(name)` activates a scene.
- `app.scene_names()` lists registered scenes.
- `app.has_scene(name)` checks whether a scene exists.
- `app.remove_scene(name)` removes a non-active scene.
- `app.process_event(event)`, `app.update(dt_seconds)`, and `app.draw()` form the low-level runtime loop.

### UiEngine [Back to Top](#table-of-contents)

`UiEngine` is the packaged event loop. It forwards pygame events through `GuiApplication.process_event(...)`, advances scene-local services, and draws each frame.

```python
from gui_do import UiEngine

engine = UiEngine(app, target_fps=60)
engine.run()
```

Use `max_frames=` when you want a bounded run for tests or deterministic demos.

### Scene Management [Back to Top](#table-of-contents)

Each scene has its own scheduler, timers, tween manager, overlay manager, drag-drop manager, tiling manager, and theme/graphics bundle. That keeps multi-screen applications isolated without custom bookkeeping.

```python
app.create_scene("main")
app.create_scene("settings")

app.switch_scene("settings")
print(app.active_scene_name)
print(app.scene_names())
```

Standalone helpers such as `ContextMenuManager`, `FileDialogManager`, `SceneTransitionManager`, `ResizeManager`, `ThemeManager`, and `CommandPaletteManager` are instantiated explicitly and composed with the current application or scene services as needed.

---

## Controls [Back to Top](#table-of-contents)

All built-in controls are added to a scene or container with `parent.add(child)` and expose geometry, visibility, enable/disable, focus, and draw/update behavior through the public control classes exported at the package root.

### Display and Container Controls [Back to Top](#table-of-contents)

Use these for structure, chrome, and general interaction:

- `PanelControl` is the general-purpose rectangular container.
- `LabelControl` renders single-line text with `align="left"`, `"center"`, or `"right"`.
- `ButtonControl` exposes click and focused keyboard activation.
- `ToggleControl` holds a boolean pushed state.
- `ButtonGroupControl` gives radio-style mutually exclusive selection by group name.
- `ArrowBoxControl` is a directional button with repeat support.
- `FrameControl` draws a decorative border.
- `ImageControl` displays a file path, `Path`, or `pygame.Surface`.
- `WindowControl` is a floating draggable titled window.
- `TaskPanelControl` is an auto-hide task strip.
- `OverlayPanelControl` is the overlay-safe panel used by services such as dialogs and menus.

```python
from pygame import Rect
from gui_do import ButtonControl, LabelControl, PanelControl, ToggleControl

panel = app.scene.add(PanelControl("panel", Rect(20, 20, 340, 180)))
panel.add(LabelControl("title", Rect(12, 12, 200, 24), "Settings"))
panel.add(ButtonControl("save", Rect(12, 48, 100, 28), "Save", on_click=lambda: None))
panel.add(ToggleControl("autosave", Rect(12, 84, 140, 28), "On", "Off", pushed=True))
```

### Text Controls [Back to Top](#table-of-contents)

`TextInputControl`, `TextAreaControl`, and `RichLabelControl` cover editable single-line input, editable multi-line input, and styled rich text.

```python
from gui_do import RichLabelControl, TextAreaControl, TextInputControl

name_input = TextInputControl(
    "name",
    Rect(20, 20, 240, 28),
    placeholder="Project name",
    on_submit=lambda value: print("submit", value),
)

notes = TextAreaControl(
    "notes",
    Rect(20, 60, 320, 140),
    value="Initial text",
    read_only=False,
)

hint = RichLabelControl(
    "hint",
    Rect(20, 210, 320, 60),
    text="**Bold**, _italic_, and `code` spans are supported.",
)
```

### Selection, Range, and Data Controls [Back to Top](#table-of-contents)

gui_do includes small-value widgets and larger selection/data widgets in the same public surface:

- `SliderControl` and `ScrollbarControl` report a new value plus optional `ValueChangeReason`.
- `SpinnerControl` is numeric input with buttons, keyboard input, and wheel support.
- `RangeSliderControl` exposes `low_value` and `high_value`.
- `DropdownControl` selects one `DropdownOption` and calls `on_change(value, index)`.
- `ListViewControl` renders `ListItem` rows with single or multi-select.
- `DataGridControl` displays `GridColumn` and `GridRow` tables.
- `TreeControl` renders hierarchical `TreeNode` data.
- `TabControl` switches among `TabItem` definitions.
- `SplitterControl` provides two resizable panes.

```python
from gui_do import (
    DropdownControl,
    DropdownOption,
    ListItem,
    ListViewControl,
    RangeSliderControl,
    SpinnerControl,
)

spinner = SpinnerControl("count", Rect(20, 20, 120, 28), value=5, min_value=0, max_value=20)
price = RangeSliderControl("range", Rect(20, 60, 260, 28), min_value=0, max_value=100, low_value=20, high_value=80)

choices = DropdownControl(
    "color",
    Rect(20, 100, 180, 28),
    options=[DropdownOption("Red", "red"), DropdownOption("Blue", "blue")],
    on_change=lambda value, index: print(value, index),
)

items = [ListItem("Alpha"), ListItem("Beta"), ListItem("Gamma")]
listing = ListViewControl("list", Rect(20, 140, 220, 150), items=items, on_select=lambda index, item: print(item.label))
```

### Canvas, Scroll, and Advanced Inputs [Back to Top](#table-of-contents)

Use these controls when the built-in list/form widgets are not enough:

- `CanvasControl` gives you a bounded event queue of `CanvasEventPacket` values for custom drawing and interaction.
- `ScrollViewControl` hosts child controls in content-local coordinates and clips them to a viewport.
- `ColorPickerControl` provides inline HSV picking plus hex text entry.

```python
from gui_do import CanvasControl, ColorPickerControl, LabelControl, ScrollViewControl

canvas = CanvasControl("canvas", Rect(20, 20, 300, 180), max_events=256)

scroll = ScrollViewControl("scroll", Rect(340, 20, 220, 180), content_height=400, scroll_y=True)
scroll.add(LabelControl("row1", Rect(0, 0, 180, 24), "Scrollable row"), 0, 0)
scroll.add(LabelControl("row2", Rect(0, 0, 180, 24), "Another row"), 0, 36)

picker = ColorPickerControl("picker", Rect(20, 220, 220, 200), color=(255, 128, 0))
```

---

## Layout [Back to Top](#table-of-contents)

### LayoutAxis [Back to Top](#table-of-contents)

`LayoutAxis.HORIZONTAL` and `LayoutAxis.VERTICAL` are the axis enums used by `SliderControl`, `ScrollbarControl`, `SplitterControl`, and related layout helpers.

### LayoutManager [Back to Top](#table-of-contents)

`LayoutManager` is a small grid-placement helper for consistent row/column spacing.

```python
app.layout.set_grid_properties(
    anchor=(20, 20),
    item_width=120,
    item_height=32,
    column_spacing=8,
    row_spacing=8,
)
rect = app.layout.grid(col=1, row=2)
```

### ConstraintLayout [Back to Top](#table-of-contents)

`ConstraintLayout` and `AnchorConstraint` support anchor-relative positioning inside a container or window-sized parent rect.

```python
from gui_do import AnchorConstraint, ConstraintLayout

layout = ConstraintLayout()
layout.add(AnchorConstraint(save_button, left=12, bottom=12, width=100, height=28))
layout.apply(Rect(0, 0, 640, 480))
```

### FlexLayout [Back to Top](#table-of-contents)

`FlexLayout` computes row or column layouts using `FlexItem`, `FlexDirection`, `FlexAlign`, and `FlexJustify`.

```python
from gui_do import FlexAlign, FlexDirection, FlexItem, FlexJustify, FlexLayout

layout = FlexLayout(direction=FlexDirection.ROW, gap=8, align=FlexAlign.CENTER, justify=FlexJustify.START)
items = [
    FlexItem(name_input, basis=180, grow=1),
    FlexItem(save_button, basis=100, grow=0),
]
layout.apply(items, Rect(20, 20, 420, 32))
```

### WindowTilingManager [Back to Top](#table-of-contents)

`WindowTilingManager` arranges visible `WindowControl` nodes without overlap inside the active scene. It is scene-local through `app.window_tiling`.

```python
tiling = app.window_tiling
tiling.prime_registration()
tiling.configure(gap=12, padding=12, avoid_task_panel=True, relayout=False)
tiling.set_enabled(True)
tiling.arrange_windows()
print(tiling.read_settings())
```

---

## Events and Input [Back to Top](#table-of-contents)

### GuiEvent and EventManager [Back to Top](#table-of-contents)

`EventManager` normalizes raw pygame input into `GuiEvent`. Controls and services consume `GuiEvent`, not raw pygame events.

```python
event.is_key_down(pygame.K_RETURN)
event.is_mouse_down(button=1)
event.is_mouse_up(button=1)
event.is_mouse_motion()
event.is_mouse_wheel()
event.pos
event.rel
event.raw_pos
event.raw_rel
event.kind
```

`EventType` and `EventPhase` are also exported for routing-aware code.

### EventBus [Back to Top](#table-of-contents)

`EventBus` is a scoped publish/subscribe channel for non-input runtime events.

```python
bus = app.events
subscription = bus.subscribe("task.done", lambda payload: print(payload), scope="main")
bus.publish("task.done", {"result": 42}, scope="main")
bus.unsubscribe(subscription)
```

Use `once(...)` for one-shot subscriptions and `unsubscribe_scope(...)` to remove all handlers in one scope.

### ActionManager [Back to Top](#table-of-contents)

`ActionManager` maps keys to named actions with optional scene and active-window scoping.

```python
import pygame

actions = app.actions
actions.register_action("save", lambda event: (print("save"), True)[1])
actions.bind_key(pygame.K_s, "save", scene="editor", window_only=False)
```

For a one-call setup, use `register_and_bind(...)`.

### FocusManager [Back to Top](#table-of-contents)

`FocusManager` controls keyboard focus. Controls participate by exposing `tab_index >= 0` and accepting focus.

```python
focus = app.focus
focus.set_focus(name_input, via_keyboard=False)
print(focus.current)
```

### ValueChangeReason and ValueChangeCallback [Back to Top](#table-of-contents)

`ValueChangeReason` tags slider- and scrollbar-style callbacks with the source of the change.

```python
from gui_do import SliderControl, ValueChangeReason

def on_change(value: float, reason: ValueChangeReason) -> None:
    print(value, reason)

slider = SliderControl("zoom", Rect(20, 20, 240, 24), LayoutAxis.HORIZONTAL, 0.0, 100.0, 50.0, on_change=on_change)
```

Members are `KEYBOARD`, `PROGRAMMATIC`, `MOUSE_DRAG`, and `WHEEL`.

---

## Data and State [Back to Top](#table-of-contents)

### ObservableValue, ComputedValue, and PresentationModel [Back to Top](#table-of-contents)

`ObservableValue` is the base reactive primitive. `ComputedValue` derives a read-only value from other observables. `PresentationModel` is a small subscription-owning base class for view-model style objects.

```python
from gui_do import ComputedValue, ObservableValue, PresentationModel

a = ObservableValue(2)
b = ObservableValue(3)
total = ComputedValue(lambda: a.value + b.value, deps=[a, b])
total.subscribe(lambda value: print("total", value))


class CounterModel(PresentationModel):
    def __init__(self) -> None:
        super().__init__()
        self.count = ObservableValue(0)


a.value = 10
```

### InvalidationTracker [Back to Top](#table-of-contents)

`InvalidationTracker` collects dirty regions and can promote to full redraw when necessary.

```python
tracker = app.invalidation
tracker.set_screen_size((800, 600))
tracker.invalidate_rect(Rect(20, 20, 100, 40))
is_full, dirty_rects = tracker.begin_frame()
tracker.end_frame()
```

### FormModel [Back to Top](#table-of-contents)

`FormModel` manages named `FormField` instances, per-field validation, cross-field validation, dirty tracking, and commit/reset behavior.

```python
from gui_do import FieldError, FormModel

form = FormModel()
name = form.add_field("name", "", required=True)
email = form.add_field("email", "")

name.value.value = "Alice"
form.add_cross_validator(
    lambda model: None if model.field("email").value.value else [FieldError("email", "Email required")]
)

ok = form.validate_all()
print(ok, form.get_errors())
form.commit_all()
```

`ValidationRule` is the callable type exported for field validators, and `FieldError` is the exported error record type.

### CommandHistory [Back to Top](#table-of-contents)

`CommandHistory` implements bounded undo/redo stacks and `CommandTransaction` grouping for objects matching the exported `Command` protocol.

```python
history = CommandHistory(max_size=100)
history.push(my_command)
history.undo()
history.redo()

with history.transaction("Bulk edit") as tx:
    tx.add(cmd_a)
    tx.add(cmd_b)
```

### StateMachine and Router [Back to Top](#table-of-contents)

`StateMachine` models finite-state transitions with observable current state. `Router` models application navigation history and can switch scenes when supplied with a `GuiApplication`.

```python
from gui_do import Router, StateMachine

sm = StateMachine("idle")
sm.add_state("running")
sm.add_transition("idle", "running", trigger="start")
sm.current.subscribe(lambda value: print("state", value))
sm.trigger("start")

router = Router()
router.register("/home", "home_scene")
router.register("/settings", "settings_scene")
router.push("/home", app=app)
router.push("/settings", app=app)
router.pop(app=app)
```

### SettingsRegistry [Back to Top](#table-of-contents)

`SettingsRegistry` is a namespaced settings store where each declared setting is backed by an `ObservableValue`. `SettingDescriptor` is the exported metadata object used for introspection.

```python
from gui_do import SettingsRegistry

settings = SettingsRegistry("settings.json")
volume = settings.declare("audio", "volume", 1.0, label="Master Volume")
volume.subscribe(lambda value: print("volume", value))

settings.load()
settings.set_value("audio", "volume", 0.5)
settings.save()
```

---

## Scheduling and Animation [Back to Top](#table-of-contents)

### TaskScheduler [Back to Top](#table-of-contents)

`TaskScheduler` runs background callables in a thread pool and lets the UI poll for completions, failures, and task messages during `update()`.

```python
def work(task_id, payload):
    return payload * 2


app.scheduler.add_task("double", work, parameters=21)
finished = app.scheduler.update()
if "double" in finished:
    print(app.scheduler.pop_result("double"))
```

Use `send_message(...)` for in-flight task progress, `get_failed_tasks()` for errors, and `clear_events()` after consuming finished/failed event lists.

### Timers [Back to Top](#table-of-contents)

`Timers` is a frame-driven repeating and one-shot timer registry.

```python
timers = app.timers
timers.add_timer("blink", 0.5, lambda: print("tick"))
timers.add_once("intro", 2.0, lambda: print("ready"))
timers.remove_timer("blink")
```

### TweenManager [Back to Top](#table-of-contents)

`TweenManager` animates numeric attributes or arbitrary functions over time. `TweenHandle` lets you cancel a tween or inspect completion.

```python
from gui_do import Easing

handle = app.tweens.tween(button.rect, "x", 240, 0.25, easing=Easing.EASE_IN_OUT)
print(handle.elapsed_fraction())
handle.cancel()
```

Use `tween_fn(...)` when you want eased callback-driven animation instead of direct attribute interpolation.

### AnimationSequence [Back to Top](#table-of-contents)

`AnimationSequence` builds sequential and parallel animation flows on top of `TweenManager`. `AnimationHandle` cancels remaining steps.

```python
from gui_do import AnimationSequence

sequence = AnimationSequence(app.tweens)
handle = (
    sequence
    .then(target=button.rect, attr="x", end_value=200, duration_seconds=0.2)
    .wait(0.1)
    .parallel([
        {"target": button.rect, "attr": "x", "end_value": 260, "duration_seconds": 0.2},
        {"target": button.rect, "attr": "y", "end_value": 140, "duration_seconds": 0.2},
    ])
    .start()
)
```

---

## Overlay and Runtime Services [Back to Top](#table-of-contents)

### OverlayManager and OverlayHandle [Back to Top](#table-of-contents)

`OverlayManager` owns transient overlay controls drawn above the scene graph. `OverlayHandle` dismisses a specific overlay and reports whether it is still open.

```python
from gui_do import LabelControl, OverlayPanelControl

panel = OverlayPanelControl("popup_panel", Rect(120, 120, 260, 120))
panel.add(LabelControl("msg", Rect(12, 12, 220, 24), "Hello from overlay"))
handle = app.overlay.show("popup", panel, dismiss_on_outside_click=True)
print(handle.is_open)
handle.dismiss()
```

### ToastManager and ToastHandle [Back to Top](#table-of-contents)

`ToastManager` shows transient or persistent banners. `ToastHandle` can dismiss a single toast.

```python
from gui_do import ToastSeverity

toast = app.toasts.show(
    "File saved",
    title="Success",
    severity=ToastSeverity.SUCCESS,
    duration_seconds=3.0,
)
```

Use `show_persistent(...)` for a toast that stays open until dismissed.

### DialogManager and DialogHandle [Back to Top](#table-of-contents)

`DialogManager` provides alert, confirm, and prompt modals. `DialogHandle` dismisses a specific modal or reports whether it is open.

```python
app.dialogs.show_alert("Done", "Operation complete")
app.dialogs.show_confirm("Delete", "Delete file?", on_confirm=lambda: print("confirmed"))
app.dialogs.show_prompt("Rename", "New name", on_submit=lambda value: print(value))
```

### ContextMenuManager and ContextMenuHandle [Back to Top](#table-of-contents)

`ContextMenuManager` renders a pointer-anchored menu from `ContextMenuItem` values. `ContextMenuHandle` closes a menu programmatically.

```python
from gui_do import ContextMenuItem, ContextMenuManager

menus = ContextMenuManager(app)
handle = menus.show(
    (x, y),
    [
        ContextMenuItem("Cut", action=lambda: None),
        ContextMenuItem("Copy", action=lambda: None),
        ContextMenuItem("", separator=True),
        ContextMenuItem("Paste", action=lambda: None),
    ],
)
```

### DragDropManager and DragPayload [Back to Top](#table-of-contents)

`DragDropManager` coordinates typed drag sessions between source and target controls. `DragPayload` carries the drag kind and arbitrary data.

```python
from gui_do import DragPayload

payload = DragPayload(kind="file", data={"path": "notes.txt"})
app.drag_drop.begin_drag(payload)
```

### FileDialogManager, FileDialogOptions, and FileDialogHandle [Back to Top](#table-of-contents)

`FileDialogManager` exposes separate open/save flows. `FileDialogOptions` configures title, start directory, filters, and selection rules. `FileDialogHandle` tracks the modal dialog state.

```python
from gui_do import FileDialogManager, FileDialogOptions

files = FileDialogManager(app)

files.show_open(
    FileDialogOptions(title="Open Image", filters=[("Images", [".png", ".jpg"]), ("All", ["*"])]),
    on_close=lambda paths: print(paths),
)

files.show_save(
    FileDialogOptions(title="Save As"),
    on_close=lambda paths: print(paths),
)
```

### ResizeManager [Back to Top](#table-of-contents)

`ResizeManager` updates registered `ConstraintLayout` instances and notifies subscribers when the window size changes.

```python
from gui_do import ResizeManager

resize = ResizeManager(initial_size=(800, 600), event_bus=app.events)
resize.on_resize(lambda width, height: print(width, height))
resize.notify_resize(1024, 768)
```

### ClipboardManager [Back to Top](#table-of-contents)

`ClipboardManager` is a thin wrapper over `pygame.scrap` with safe fallbacks when clipboard access is unavailable.

```python
from gui_do import ClipboardManager

ClipboardManager.copy("hello")
print(ClipboardManager.paste())
```

### CommandPaletteManager, CommandEntry, and CommandPaletteHandle [Back to Top](#table-of-contents)

`CommandPaletteManager` shows a searchable command launcher using the overlay system. `CommandEntry` is the exported command record, and `CommandPaletteHandle` closes an open palette.

```python
from gui_do import CommandEntry, CommandPaletteManager

palette = CommandPaletteManager(app.overlay)
palette.register(CommandEntry("save", "Save File", action=lambda: print("save"), category="File"))
palette.register(CommandEntry("open", "Open File", action=lambda: print("open"), category="File"))
handle = palette.show(app)
print(handle.is_open)
```

---

## Menu System [Back to Top](#table-of-contents)

### MenuBarControl and MenuEntry [Back to Top](#table-of-contents)

`MenuBarControl` renders a horizontal top-level menu bar. Each `MenuEntry` contains a label plus `ContextMenuItem` rows for its flyout.

```python
from gui_do import ContextMenuItem, MenuBarControl, MenuEntry

bar = MenuBarControl(
    "menubar",
    Rect(0, 0, 800, 28),
    entries=[
        MenuEntry("File", items=[ContextMenuItem("Open", action=lambda: None)]),
        MenuEntry("Edit", items=[ContextMenuItem("Undo", action=lambda: None)]),
    ],
)
app.scene.add(bar)
```

### MenuBarManager [Back to Top](#table-of-contents)

`MenuBarManager` is the feature-friendly registration layer for top-level menus. It accumulates menu contributions and builds one `MenuBarControl` in registration order.

```python
from gui_do import ContextMenuItem, MenuBarManager

manager = MenuBarManager()
manager.register_menu("File", [ContextMenuItem("Open", action=lambda: None)])
manager.register_menu("File", [ContextMenuItem("Save", action=lambda: None)])
manager.register_menu("View", [ContextMenuItem("Zoom In", action=lambda: None)])

bar = manager.build("menubar", Rect(0, 0, 800, 28), app)
app.scene.add(bar)
```

---

## Notification System [Back to Top](#table-of-contents)

### NotificationCenter and NotificationRecord [Back to Top](#table-of-contents)

`NotificationCenter` stores an activity log, optionally sourced from `EventBus` topics. `NotificationRecord` is the exported record shape.

```python
from gui_do import NotificationCenter, NotificationRecord, ToastSeverity

notifications = NotificationCenter(app.events, max_records=200)
notifications.subscribe("build.done", severity=ToastSeverity.SUCCESS, title="Build")
notifications.unread_count.subscribe(lambda value: print("unread", value))
notifications.add(NotificationRecord("Deployment complete", severity=ToastSeverity.SUCCESS))
```

### NotificationPanelControl [Back to Top](#table-of-contents)

`NotificationPanelControl` renders a `NotificationCenter` inside an overlay-friendly panel.

```python
from gui_do import NotificationPanelControl

panel = NotificationPanelControl("notifications", Rect(560, 40, 320, 420), notifications)
app.overlay.show("notifications", panel, dismiss_on_outside_click=True)
```

---

## Scene Transitions [Back to Top](#table-of-contents)

### SceneTransitionManager and SceneTransitionStyle [Back to Top](#table-of-contents)

`SceneTransitionManager` animates scene changes instead of switching instantly. `SceneTransitionStyle` enumerates the built-in transition styles.

```python
from gui_do import SceneTransitionManager, SceneTransitionStyle

transitions = SceneTransitionManager(app, default_style=SceneTransitionStyle.FADE, default_duration=0.3)
transitions.set_style("editor", SceneTransitionStyle.SLIDE_LEFT, duration=0.25)
transitions.go("editor")
```

Available styles are `NONE`, `FADE`, `SLIDE_LEFT`, `SLIDE_RIGHT`, `SLIDE_UP`, and `SLIDE_DOWN`.

---

## Feature System [Back to Top](#table-of-contents)

### Feature Types and FeatureMessage [Back to Top](#table-of-contents)

Features are the reusable lifecycle unit for gui_do application composition.

| Type | Purpose |
|---|---|
| `Feature` | Base lifecycle class |
| `DirectFeature` | Owns direct UI and direct draw/update hooks |
| `LogicFeature` | Provides pure logic endpoints for other features |
| `RoutedFeature` | Routes incoming feature messages by topic or command |

`FeatureMessage` is the exported envelope passed between features.

```python
from pygame import Rect
from gui_do import Feature, LabelControl


class StatusFeature(Feature):
    def build(self, host) -> None:
        self.label = host.scene.add(LabelControl("status", Rect(20, 20, 200, 24), "Ready"))

    def handle_event(self, host, event) -> bool:
        return False
```

Within a feature, use `self.send_message(...)`, `self.bind_logic(...)`, and `self.send_logic_message(...)` to communicate with other registered features.

### FeatureManager [Back to Top](#table-of-contents)

`FeatureManager` registers features, validates host requirements, dispatches lifecycle hooks, and routes messages between features.

```python
features = app.features
features.register(StatusFeature("status", scene_name="main"), host=app)
features.build_features(app)
features.bind_runtime(app)
next_tab_index = features.configure_accessibility(app, 10)
features.send_message("status", "other_feature", {"command": "refresh"})
```

It also exposes direct-feature update/draw helpers, feature prewarm support, state save/restore, logic binding, and runnable registration.

---

## Theme and Graphics [Back to Top](#table-of-contents)

### ColorTheme [Back to Top](#table-of-contents)

`ColorTheme` is the built-in semantic palette plus text-rendering helper used by the runtime. The active scene theme is available as `app.theme`.

```python
theme = app.theme
text_surface = theme.render_text("Hello", role="body")
print(theme.font_roles())
```

`ColorTheme` also exposes `register_font_role(...)` for adding or replacing named font roles.

### ThemeManager and DesignTokens [Back to Top](#table-of-contents)

`ThemeManager` manages named token sets and exposes reactive `active_theme` and `active_tokens` observables. `DesignTokens` is the exported token container.

```python
from gui_do import ThemeManager

theme_manager = ThemeManager()
theme_manager.register_theme("contrast", {"primary": (255, 220, 0), "background": (20, 20, 20)})
theme_manager.switch("contrast")
print(theme_manager.token("primary"))
```

### BuiltInGraphicsFactory [Back to Top](#table-of-contents)

`BuiltInGraphicsFactory` builds cached visual surfaces for built-in widgets. It is exposed as `app.graphics_factory` and used internally by control drawing. When the active theme or fonts change, controls can invalidate themselves and rebuild against the current factory output.

### FontManager [Back to Top](#table-of-contents)

`FontManager` is the role-based font registry used by `ColorTheme`. Through `app.theme.fonts`, you can register named roles and resolve font instances by role and size.

```python
fonts = app.theme.fonts
fonts.register_role("caption", size=12, bold=False)
font = fonts.resolve("caption", 12)
print(font.text_size("gui_do"))
```

---

## Telemetry [Back to Top](#table-of-contents)

gui_do includes opt-in runtime telemetry plus offline analysis helpers.

```python
from gui_do import (
    TelemetrySample,
    analyze_telemetry_log_file,
    configure_telemetry,
    render_telemetry_report,
    telemetry_collector,
)

configure_telemetry(enabled=True, log_file="telemetry.jsonl", max_samples=10000)
collector = telemetry_collector()
collector.record(TelemetrySample(feature_name="render", duration_ms=12.4))

analysis = analyze_telemetry_log_file("telemetry.jsonl")
print(render_telemetry_report(analysis))
```

The telemetry exports are `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_records`, `analyze_telemetry_log_file`, `load_telemetry_log_file`, and `render_telemetry_report`.

---

## Public API Index [Back to Top](#table-of-contents)

The following list is the complete public package export surface from `gui_do.__all__`, grouped by concept.

### Application and Loop [Back to Top](#table-of-contents)

- `GuiApplication`
- `UiEngine`

### Controls [Back to Top](#table-of-contents)

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
- `MenuBarControl`
- `MenuEntry`
- `TreeControl`
- `TreeNode`
- `NotificationPanelControl`
- `ScrollViewControl`
- `SpinnerControl`
- `RangeSliderControl`
- `ColorPickerControl`

### Layout [Back to Top](#table-of-contents)

- `LayoutAxis`
- `LayoutManager`
- `WindowTilingManager`
- `ConstraintLayout`
- `AnchorConstraint`
- `FlexLayout`
- `FlexItem`
- `FlexDirection`
- `FlexAlign`
- `FlexJustify`

### Events, Input, and Core Runtime [Back to Top](#table-of-contents)

- `ActionManager`
- `EventManager`
- `EventBus`
- `FocusManager`
- `FontManager`
- `EventPhase`
- `EventType`
- `GuiEvent`
- `ValueChangeCallback`
- `ValueChangeReason`
- `InvalidationTracker`

### Data and State [Back to Top](#table-of-contents)

- `ObservableValue`
- `PresentationModel`
- `ComputedValue`
- `FormModel`
- `FormField`
- `ValidationRule`
- `FieldError`
- `CommandHistory`
- `Command`
- `CommandTransaction`
- `StateMachine`
- `SettingsRegistry`
- `SettingDescriptor`
- `Router`
- `RouteEntry`

### Scheduling and Animation [Back to Top](#table-of-contents)

- `TaskEvent`
- `TaskScheduler`
- `Timers`
- `TweenManager`
- `TweenHandle`
- `Easing`
- `AnimationSequence`
- `AnimationHandle`

### Overlay and Runtime Services [Back to Top](#table-of-contents)

- `OverlayManager`
- `OverlayHandle`
- `ToastManager`
- `ToastHandle`
- `ToastSeverity`
- `DialogManager`
- `DialogHandle`
- `DragDropManager`
- `DragPayload`
- `ContextMenuManager`
- `ContextMenuItem`
- `ContextMenuHandle`
- `FileDialogManager`
- `FileDialogOptions`
- `FileDialogHandle`
- `ResizeManager`
- `ClipboardManager`
- `CommandPaletteManager`
- `CommandEntry`
- `CommandPaletteHandle`

### Menu and Notifications [Back to Top](#table-of-contents)

- `MenuBarManager`
- `NotificationCenter`
- `NotificationRecord`

### Features and Scene Composition [Back to Top](#table-of-contents)

- `Feature`
- `DirectFeature`
- `LogicFeature`
- `RoutedFeature`
- `FeatureMessage`
- `FeatureManager`
- `SceneTransitionManager`
- `SceneTransitionStyle`

### Theme and Graphics [Back to Top](#table-of-contents)

- `BuiltInGraphicsFactory`
- `ColorTheme`
- `ThemeManager`
- `DesignTokens`

### Telemetry [Back to Top](#table-of-contents)

- `TelemetryCollector`
- `TelemetrySample`
- `configure_telemetry`
- `telemetry_collector`
- `analyze_telemetry_records`
- `analyze_telemetry_log_file`
- `load_telemetry_log_file`
- `render_telemetry_report`
