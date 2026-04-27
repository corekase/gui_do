[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

# gui_do

gui_do is a pygame GUI framework for building scene-driven desktop interfaces with reusable controls, runtime services, and feature composition. It gives developers a public API that combines UI controls, event and focus routing, state and data management, overlays, scheduling, animation, file dialogs, menus, notifications, and telemetry in one coherent runtime. The package targets tools, editors, dashboards, simulation frontends, and application UIs where composability, predictable behavior, and explicit architecture boundaries matter.

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
  - [Text Controls](#text-controls)
  - [Value and Selection Controls](#value-and-selection-controls)
  - [Data Grid](#data-grid)
  - [Container and Tab Controls](#container-and-tab-controls)
  - [Navigation and Hierarchy Controls](#navigation-and-hierarchy-controls)
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
- [Data and State](#data-and-state)
  - [ObservableValue and PresentationModel](#observablevalue-and-presentationmodel)
  - [InvalidationTracker](#invalidationtracker)
  - [FormModel](#formmodel)
  - [CommandHistory](#commandhistory)
  - [StateMachine and Router](#statemachine-and-router)
  - [SettingsRegistry](#settingsregistry)
- [Value Change Contracts](#value-change-contracts)
  - [ValueChangeReason and ValueChangeCallback](#valuechangereason-and-valuechangecallback)
- [Scheduling and Animation](#scheduling-and-animation)
  - [TaskScheduler](#taskscheduler)
  - [Timers](#timers)
  - [TweenManager](#tweenmanager)
- [Overlay and Dialog Services](#overlay-and-dialog-services)
  - [OverlayManager and OverlayPanelControl](#overlaymanager-and-overlaypanelcontrol)
  - [ToastManager](#toastmanager)
  - [DialogManager](#dialogmanager)
  - [ContextMenuManager](#contextmenumanager)
  - [DragDropManager](#dragdropmanager)
  - [FileDialogManager](#filedialogmanager)
  - [ResizeManager](#resizemanager)
- [Menu System](#menu-system)
  - [MenuBarControl and MenuEntry](#menubarcontrol-and-menuentry)
  - [MenuBarManager](#menubarmanager)
- [Notification System](#notification-system)
  - [NotificationCenter](#notificationcenter)
  - [NotificationPanelControl](#notificationpanelcontrol)
- [Scene Transitions](#scene-transitions)
  - [SceneTransitionManager](#scenetransitionmanager)
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

## Quick Start — [Back to Top](#table-of-contents)

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

## Overview — [Back to Top](#table-of-contents)

gui_do is built around a **scene runtime**. `GuiApplication` is the top-level host: it owns the display surface, manages a collection of named scenes, and exposes every runtime service — focus, event routing, scheduling, overlays, dialogs, drag-drop, tweens, window tiling, and theme — through a stable public API. Only one scene is active at a time; each scene carries its own scheduler, timers, tween manager, overlay stack, and event context. This makes multi-screen apps naturally isolated without any custom plumbing between scenes.

**Controls** are all `UiNode` subclasses. They live in a scene tree, share a consistent event/update/draw contract, and respond to normalized `GuiEvent` objects. The control library covers: labels, buttons, toggles, sliders, scrollbars, list views, dropdowns, data grids, text inputs, text areas, rich labels, canvases, frames, images, tab controls, splitters, windows, task panels, menu bars, tree views, and notification panels.

**Layout** systems include a grid-placement `LayoutManager`, anchor-driven `ConstraintLayout`, a CSS-flex-style `FlexLayout`, and a `WindowTilingManager` that registers and tiles floating windows within a scene.

**Events** flow from pygame through `EventManager`, which normalizes raw events into `GuiEvent` objects before dispatch. `FocusManager` owns keyboard focus and Tab traversal. `EventBus` carries typed pub/sub messages between decoupled components. `ActionManager` maps keyboard chords to named actions.

**State and data** are handled by `ObservableValue` and `PresentationModel` for reactive bindings, `FormModel`/`FormField`/`ValidationRule` for validated form state, `CommandHistory` with undo/redo and transactions, `StateMachine` for explicit state transitions, `Router`/`RouteEntry` for navigation tables, and `SettingsRegistry` for namespaced persistent settings.

**Value change contracts** are explicit: slider and scrollbar `on_change` callbacks receive the new value and optionally a `ValueChangeReason` enum tag (`KEYBOARD`, `PROGRAMMATIC`, `MOUSE_DRAG`, `WHEEL`). The `ValueChangeCallback` type alias and `ValueChangeReason` are first-class public exports.

**Background work** uses `TaskScheduler`, which runs tasks in a thread pool and delivers `TaskEvent` progress/completion/error updates back to the UI via the event bus. Scene-local `Timers` schedule one-shot and repeating callbacks in frame time. `TweenManager` with `TweenHandle` and `Easing` curves animates numeric properties.

**Overlay and dialog services** integrate cleanly with the scene runtime: `OverlayManager` shows and dismisses floating `OverlayPanelControl` nodes, `ToastManager` manages transient notification banners with severity levels, `DialogManager` provides modal alert/confirm/prompt flows, `ContextMenuManager` shows pointer-anchored menus, `DragDropManager` coordinates typed drag sessions, `FileDialogManager` provides modal file-open and file-save dialogs with filters and multi-select, and `ResizeManager` centralizes app/scene geometry change callbacks.

**Menu system**: `MenuBarControl` renders a horizontal menu bar with flyout sub-menus. `MenuBarManager` lets independently developed features register their own top-level menus and items before a merged `MenuBarControl` is built and added to the scene.

**Notification system**: `NotificationCenter` subscribes to one or more `EventBus` topics and stores bounded `NotificationRecord` entries with reactive `unread_count` and `records` `ObservableValue` fields. `NotificationPanelControl` is an overlay that renders the center's log sorted by recency with severity-colored stripes and a "Mark all read" action.

**Scene transitions**: `SceneTransitionManager` wraps `switch_scene` with animated cross-scene transitions — `FADE`, `SLIDE_LEFT`, `SLIDE_RIGHT`, `SLIDE_UP`, `SLIDE_DOWN`, or `NONE` — driven by the active scene's `TweenManager`.

**Feature system**: `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature` are lifecycle base classes for composing reusable behavior units. `FeatureManager` registers features, validates host-field contracts, calls lifecycle hooks (`build`, `bind_runtime`, `configure_accessibility`, `on_update`, `handle_event`, `shutdown_runtime`), and routes `FeatureMessage` envelopes between features.

**Theme and graphics**: `ColorTheme` supplies semantic color tokens and text rendering. `ThemeManager` and `DesignTokens` enable runtime theme switching. `FontManager` provides role-based font access and rendering. `BuiltInGraphicsFactory` constructs cached visual surfaces for all built-in controls.

**Telemetry**: A structured opt-in metrics system (`configure_telemetry`, `telemetry_collector`, `TelemetryCollector`, `TelemetrySample`) and offline analysis tools (`analyze_telemetry_records`, `analyze_telemetry_log_file`, `load_telemetry_log_file`, `render_telemetry_report`) for performance profiling and feature hotspot detection.

---

<a id="minimal-runnable-example"></a>

## Minimal Runnable Example — [Back to Top](#table-of-contents)

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

## Package Management — [Back to Top](#table-of-contents)

`gui_do` ships with `scripts/manage.py` for repository bootstrap and update workflows. The script supports `init`, `apply`, `verify`, `check`, and `update` commands.

<a id="start-a-new-project"></a>

### Start a New Project — [Back to Top](#table-of-contents)

Use this when you have cloned or downloaded the gui_do repository and want a clean, library-first base without demo content:

```bash
python scripts/manage.py init --verify
```

Optional starter scaffold:

```bash
python scripts/manage.py init --scaffold --scaffold-file myapp.py --scaffold-package features --verify
```

Useful flags:

- `--dry-run` — preview changes without writing anything
- `--skip-doc-sync` — skip README and docs parity rewrites
- `--skip-workflow-sync` — skip CI workflow synchronization

<a id="add-to-or-update-an-existing-project"></a>

### Add to or Update an Existing Project — [Back to Top](#table-of-contents)

Validate a target project before copying library assets into it:

```bash
python scripts/manage.py check --target D:/Code/my_app
```

Then update the target project with the current library version:

```bash
python scripts/manage.py update --target D:/Code/my_app --verify
```

`update` syncs library-only directories and files (`gui_do/`, `scripts/`, `tests/`, `docs/`, `pyproject.toml`, and related root files) then runs `apply` in the target to maintain contract parity.

---

<a id="application-bootstrap"></a>

## Application Bootstrap — [Back to Top](#table-of-contents)

<a id="guiapplication"></a>

### GuiApplication — [Back to Top](#table-of-contents)

`GuiApplication(surface)` is the runtime root. It owns scenes, controls, managers, and rendering. Pass the pygame display surface created with `pygame.display.set_mode(...)`.

```python
import pygame
from gui_do import GuiApplication

pygame.init()
surface = pygame.display.set_mode((1024, 720))
app = GuiApplication(surface)
```

Key public services on `app`:

| Attribute | Description |
|---|---|
| `app.scene` | Active scene root node |
| `app.focus` | `FocusManager` |
| `app.events` | `EventBus` |
| `app.actions` | `ActionManager` |
| `app.overlay` | `OverlayManager` |
| `app.toasts` | `ToastManager` |
| `app.dialogs` | `DialogManager` |
| `app.drag_drop` | `DragDropManager` |
| `app.scheduler` | `TaskScheduler` |
| `app.timers` | `Timers` |
| `app.tweens` | `TweenManager` |
| `app.features` | `FeatureManager` |
| `app.window_tiling` | `WindowTilingManager` |
| `app.layout` | `LayoutManager` |
| `app.theme` | `ColorTheme` |
| `app.graphics_factory` | `BuiltInGraphicsFactory` |

Key lifecycle methods:

- `app.process_event(event)` — normalize and dispatch one pygame event
- `app.update(dt)` — update all runtime systems
- `app.draw()` — render the active scene
- `app.create_scene(name)` — register a new scene
- `app.switch_scene(name)` — activate a scene by name
- `app.scene_names()` — list all registered scene names
- `app.shutdown()` — tear down all runtime systems

<a id="uiengine"></a>

### UiEngine — [Back to Top](#table-of-contents)

`UiEngine(app, target_fps=60)` runs the main event loop, calling `process_event`, `update`, and `draw` each frame.

```python
from gui_do import UiEngine

engine = UiEngine(app, target_fps=60)
engine.run()               # runs until the window closes
engine.run(max_frames=300) # bounded run useful for testing
```

<a id="scene-management"></a>

### Scene Management — [Back to Top](#table-of-contents)

Each named scene carries its own isolated runtime context. Only the active scene receives updates and input events.

```python
app.create_scene("main")
app.create_scene("settings")

app.switch_scene("settings")
print(app.active_scene_name)   # "settings"
print(app.scene_names())       # ["main", "settings"]
```

Scene-local systems (scheduler, timers, tweens, overlay stack) are automatically suspended and resumed on scene switches.

---

<a id="controls"></a>

## Controls — [Back to Top](#table-of-contents)

<a id="uinode-pattern"></a>

### UiNode Pattern — [Back to Top](#table-of-contents)

All built-in controls inherit from `UiNode` and share a consistent contract:

- **Identity and geometry**: `control_id`, `rect`
- **Visibility and interaction**: `visible`, `enabled`, `tab_index`
- **Tree management**: `add(child)`, `remove(child)`, `children`, `parent`
- **Lifecycle**: `invalidate()`, `show()`, `hide()`, `enable()`, `disable()`
- **Geometry helpers**: `set_pos(x, y)`, `resize(w, h)`, `set_rect(rect)`
- **Accessibility**: `set_accessibility(role=..., label=...)`

Controls are added to a scene or to another container node via `parent.add(child)`.

```python
from pygame import Rect
from gui_do import PanelControl, LabelControl

panel = app.scene.add(PanelControl("panel", Rect(20, 20, 400, 300)))
panel.add(LabelControl("title", Rect(8, 8, 200, 28), "My Panel"))
```

<a id="basic-controls"></a>

### Basic Controls — [Back to Top](#table-of-contents)

**PanelControl** — rectangular container, optionally draws a background fill.

```python
PanelControl(control_id, rect, draw_background=True, constraints=None)
```

**LabelControl** — single-line text display with alignment.

```python
LabelControl(control_id, rect, text, align="left")
label.text = "Updated text"
label.title = True   # use title font role
```

**ButtonControl** — clickable button with optional keyboard activation on focus.

```python
ButtonControl(control_id, rect, text, on_click=None, style="box", font_role="body")
```

**ToggleControl** — two-state toggle button with distinct on/off labels.

```python
ToggleControl(control_id, rect, text_on, text_off=None, pushed=False,
              on_toggle=None, style="box", font_role="body")
toggle.pushed   # current state
```

**ArrowBoxControl** — directional arrow button with configurable hold-repeat.

```python
ArrowBoxControl(control_id, rect, direction, on_activate=None,
                repeat_interval_seconds=0.08)
```

**ButtonGroupControl** — radio-style group button: selecting one peer deselects others sharing the same group name.

```python
ButtonGroupControl(control_id, rect, group, text, selected=False,
                   style="box", on_activate=None, font_role="body")
```

**FrameControl** — thin bordered rectangle for visual grouping.

```python
FrameControl(control_id, rect, border_width=1)
frame.border_width = 2
```

**ImageControl** — displays an image from a file path, `Path`, or an existing `pygame.Surface`. Rescales to fill rect by default.

```python
ImageControl(control_id, rect, image_path, scale=True)
ctrl.set_image("assets/logo.png")
```

<a id="text-controls"></a>

### Text Controls — [Back to Top](#table-of-contents)

**TextInputControl** — single-line editable text field with placeholder, masking, and submission callback.

```python
TextInputControl(control_id, rect, value="", placeholder="", max_length=None,
                 masked=False, on_change=None, on_submit=None, font_role="body")
ctrl.value = "initial text"
ctrl.set_value("new text")
```

**TextAreaControl** — multi-line editable text area with word wrap and optional read-only mode.

```python
TextAreaControl(control_id, rect, value="", placeholder="", max_length=None,
                read_only=False, on_change=None, font_role="body", font_size=16)
ctrl.value
ctrl.cursor_pos
ctrl.selection_range
ctrl.select_all()
```

**RichLabelControl** — multi-line text with inline style markers: `**bold**`, `_italic_`, `` `code` ``, and nested combinations such as `**_bold italic_**`.

```python
RichLabelControl(control_id, rect, text="", font_role="body", font_size=16,
                 align="left", color=None)
ctrl.text = "**Warning:** _check your input_"
```

<a id="value-and-selection-controls"></a>

### Value and Selection Controls — [Back to Top](#table-of-contents)

**SliderControl** — draggable value control. Keyboard-accessible: arrow keys nudge by 5% of range, Home/End jump to bounds.

```python
from gui_do import LayoutAxis, SliderControl, ValueChangeReason

def on_zoom(value, reason=None):
    if reason == ValueChangeReason.KEYBOARD:
        print(f"Keyboard adjusted zoom to {value}")

slider = SliderControl("zoom", Rect(20, 20, 240, 24),
                       LayoutAxis.HORIZONTAL, 0.0, 100.0, 50.0,
                       on_change=on_zoom)
slider.set_value(75.0)
slider.adjust_value(5.0)
```

**ScrollbarControl** — scroll offset control. Keyboard-accessible: arrow keys step by `step`, Page Up/Down step by 90% of viewport, Home/End jump to bounds.

```python
ScrollbarControl(control_id, rect, axis, content_size, viewport_size,
                 offset=0, step=16, on_change=None)
bar.set_offset(120)
bar.adjust_offset(16)
```

**ListViewControl** — scrollable list of `ListItem` rows with optional multi-select.

```python
from gui_do import ListViewControl, ListItem

items = [ListItem("alpha"), ListItem("beta"), ListItem("gamma")]
lv = ListViewControl("list", Rect(20, 60, 240, 180), items=items,
                     row_height=28, on_select=lambda idx, item: print(item.label))
lv.set_items(new_items)
lv.selected_index
```

**DropdownControl** — collapsed selection control that expands to a popup list.

```python
from gui_do import DropdownControl, DropdownOption

options = [DropdownOption("Red", value="red"), DropdownOption("Blue", value="blue")]
dd = DropdownControl("color", Rect(20, 60, 180, 28), options=options,
                     on_change=lambda idx, opt: print(opt.value))
dd.selected_index
dd.selected_option   # DropdownOption or None
```

<a id="data-grid"></a>

### Data Grid — [Back to Top](#table-of-contents)

`DataGridControl` renders a sortable, scrollable table. Columns are resizable by dragging header separators. Clicking a sortable column header cycles ascending/descending sort.

```python
from gui_do import DataGridControl, GridColumn, GridRow

columns = [
    GridColumn(key="name",  title="Name",  width=160, sortable=True),
    GridColumn(key="value", title="Value", width=80,  sortable=True),
    GridColumn(key="note",  title="Note",  width=200),
]
rows = [
    GridRow({"name": "Alpha", "value": 1, "note": "first"}),
    GridRow({"name": "Beta",  "value": 2, "note": "second"}),
]
grid = DataGridControl("grid", Rect(20, 20, 480, 220),
                       columns=columns, rows=rows,
                       on_select=lambda idx, row: print(row.data),
                       on_sort=lambda col_key, asc: print(col_key, asc))
grid.set_rows(updated_rows)
grid.selected_index
```

<a id="container-and-tab-controls"></a>

### Container and Tab Controls — [Back to Top](#table-of-contents)

**CanvasControl** — custom-rendered drawing surface with a bounded event queue. Delivers `CanvasEventPacket` objects including a `local_pos` field (canvas-relative coordinates).

```python
from gui_do import CanvasControl

canvas = CanvasControl("canvas", Rect(20, 20, 400, 300), max_events=256)
# Read packets each frame:
packets = canvas.drain()
for pkt in packets:
    print(pkt.local_pos, pkt.event.type)
```

**WindowControl** — draggable titled floating window, managed by the parent `PanelControl`.

```python
WindowControl(control_id, rect, title, *, use_frame_backdrop=False)
win.visible = True    # activates the window
win.visible = False   # hides and demotes active state
```

**SplitterControl** — two-pane resizable split container.

```python
SplitterControl(control_id, rect, axis, split_pos=None)
```

**TaskPanelControl** — auto-hide slide-in/out task strip for persistent bottom-bar or side-bar controls.

```python
TaskPanelControl(control_id, rect)
```

**OverlayPanelControl** — floating overlay container used directly or via overlay services.

```python
OverlayPanelControl(control_id, rect, draw_background=True, constraints=None)
```

**TabControl** — tabbed panel switcher. Each `TabItem` carries a `key`, `label`, and optional `content` node.

```python
from gui_do import TabControl, TabItem

tabs = TabControl("tabs", Rect(20, 20, 400, 300),
                  items=[TabItem("a", "Files"), TabItem("b", "Search")],
                  selected_key="a",
                  on_change=lambda key: print(key))
tabs.selected_key
```

<a id="navigation-and-hierarchy-controls"></a>

### Navigation and Hierarchy Controls — [Back to Top](#table-of-contents)

**MenuBarControl** — horizontal application menu bar with flyout sub-menus. See [Menu System](#menu-system).

**TreeControl** — virtualized hierarchical tree view with expand/collapse.

```python
from gui_do import TreeControl, TreeNode

root_nodes = [
    TreeNode("Folder A", children=[
        TreeNode("File 1"),
        TreeNode("File 2"),
    ], expanded=True),
    TreeNode("Folder B", children=[TreeNode("File 3")]),
]
tree = TreeControl("tree", Rect(20, 20, 240, 300), nodes=root_nodes,
                   on_select=lambda node, idx: print(node.label),
                   on_expand=lambda node, expanded: None)
tree.set_nodes(new_nodes)
tree.selected_node
```

`TreeNode` fields: `label`, `children`, `expanded`, `enabled`, `data` (any application payload), `icon` (reserved), `is_leaf`.

**NotificationPanelControl** — overlay log panel backed by a `NotificationCenter`. See [Notification System](#notification-system).

---

<a id="layout"></a>

## Layout — [Back to Top](#table-of-contents)

<a id="layoutaxis"></a>

### LayoutAxis — [Back to Top](#table-of-contents)

`LayoutAxis.HORIZONTAL` and `LayoutAxis.VERTICAL` are used by `SliderControl`, `ScrollbarControl`, `SplitterControl`, and layout helpers.

<a id="layoutmanager"></a>

### LayoutManager — [Back to Top](#table-of-contents)

`app.layout` provides grid-based placement helpers for evenly spaced controls.

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

<a id="constraintlayout"></a>

### ConstraintLayout — [Back to Top](#table-of-contents)

`ConstraintLayout` and `AnchorConstraint` enable anchor-relative positioning of child controls within a container.

```python
from gui_do import ConstraintLayout, AnchorConstraint

layout = ConstraintLayout(container_rect)
layout.add(AnchorConstraint(child_ctrl, left=8, right=8, top=8, height=32))
layout.apply()
```

<a id="flexlayout"></a>

### FlexLayout — [Back to Top](#table-of-contents)

`FlexLayout` computes CSS-flex-style row or column arrangements and mutates child rects in place. Wrap each child node in a `FlexItem` to configure grow, shrink, and basis.

```python
from gui_do import FlexLayout, FlexItem, FlexDirection, FlexAlign, FlexJustify

layout = FlexLayout(
    direction=FlexDirection.ROW,
    gap=8,
    align=FlexAlign.CENTER,
    justify=FlexJustify.START,
)
items = [
    FlexItem(label_ctrl, grow=0, basis=120),
    FlexItem(input_ctrl, grow=1),
    FlexItem(btn_ctrl,   grow=0, basis=80),
]
layout.apply(items, container_rect)
for item in items:
    item.node.invalidate()
```

`FlexDirection`: `ROW`, `COLUMN`.
`FlexAlign` (cross-axis): `START`, `CENTER`, `END`, `STRETCH`.
`FlexJustify` (main-axis): `START`, `CENTER`, `END`, `SPACE_BETWEEN`, `SPACE_AROUND`.

`FlexItem` options: `grow` (surplus space factor), `shrink` (shrink factor), `basis` (base size in pixels or `None` to use current rect), `min_size`, `max_size`, `align_self` (override container `align` for this item).

<a id="windowtilingmanager"></a>

### WindowTilingManager — [Back to Top](#table-of-contents)

`app.window_tiling` manages registration and automatic tiling of floating `WindowControl` nodes within a scene. `GuiApplication.build_parts(...)` primes tiling registrations automatically at startup.

---

<a id="events-and-input"></a>

## Events and Input — [Back to Top](#table-of-contents)

<a id="guievent-and-eventmanager"></a>

### GuiEvent and EventManager — [Back to Top](#table-of-contents)

All raw pygame events are normalized to `GuiEvent` by `EventManager` before dispatch. `GuiEvent` exposes semantic helpers:

```python
event.is_key_down(pygame.K_RETURN)
event.is_mouse_down(button=1)
event.is_mouse_up(button=1)
event.is_mouse_motion()
event.is_mouse_wheel()
event.wheel_delta()       # int: +1 up, -1 down
event.collides(rect)      # True if event position is inside rect
event.type                # raw pygame event type int
event.kind                # EventType enum
event.pos                 # (x, y) tuple
event.key                 # int key code (key events)
event.mod                 # modifier flags
```

`EventType` and `EventPhase` are public enums used in routing contracts.

<a id="eventbus"></a>

### EventBus — [Back to Top](#table-of-contents)

`EventBus` carries typed pub/sub messages between decoupled components. Subscriptions receive the published payload dict.

```python
bus = app.events   # scene-local EventBus, or EventBus() for a standalone instance

token = bus.subscribe("task.done", lambda payload: print(payload))
bus.publish("task.done", {"result": 42})
bus.unsubscribe(token)
```

<a id="actionmanager"></a>

### ActionManager — [Back to Top](#table-of-contents)

`ActionManager` maps keyboard input chords to named actions.

```python
actions = app.actions
actions.bind("save", pygame.K_s, mods=pygame.KMOD_CTRL,
             callback=lambda: save_file())
```

<a id="focusmanager"></a>

### FocusManager — [Back to Top](#table-of-contents)

`FocusManager` owns keyboard focus. Tab traversal follows ascending `tab_index` values. Mouse clicks transfer focus to a control when it returns `True` from `accepts_mouse_focus()`.

```python
focus = app.focus
focus.set_focus(my_ctrl, via_keyboard=False)
focus.current   # currently focused UiNode or None
```

Set `ctrl.tab_index = N` (any non-negative integer) to include a control in keyboard Tab traversal. Controls with `tab_index == -1` are excluded.

---

<a id="data-and-state"></a>

## Data and State — [Back to Top](#table-of-contents)

<a id="observablevalue-and-presentationmodel"></a>

### ObservableValue and PresentationModel — [Back to Top](#table-of-contents)

`ObservableValue[T]` is a reactive value holder. Subscribers receive the new value on every change.

```python
from gui_do import ObservableValue

count = ObservableValue(0)
count.on_change(lambda v: label.__setattr__("text", str(v)))
count.value = 5    # triggers all listeners
print(count.value) # 5
```

`PresentationModel` is a base class for view models that aggregate multiple `ObservableValue` fields.

```python
from gui_do import PresentationModel, ObservableValue

class AppModel(PresentationModel):
    def __init__(self):
        self.status = ObservableValue("idle")
        self.count  = ObservableValue(0)
```

<a id="invalidationtracker"></a>

### InvalidationTracker — [Back to Top](#table-of-contents)

`InvalidationTracker` monitors a set of `ObservableValue` fields and fires a combined callback when any of them changes.

```python
from gui_do import InvalidationTracker, ObservableValue

a = ObservableValue(1)
b = ObservableValue("x")
tracker = InvalidationTracker([a, b], on_invalidate=lambda: rebuild_ui())
```

<a id="formmodel"></a>

### FormModel — [Back to Top](#table-of-contents)

`FormModel`, `FormField`, `ValidationRule`, and `FieldError` provide form-state management with per-field validation, dirty tracking, commit, and reset.

```python
from gui_do import FormModel, FormField

def not_empty(v):
    return None if v.strip() else "Required"

form = FormModel()
name_field = form.add_field(FormField("name", "", validators=[not_empty], required=True))
email_field = form.add_field(FormField("email", ""))

name_field.value.value = "Alice"
is_ok = form.validate()    # True/False
errors = form.errors()      # list[FieldError]
form.commit()               # mark all as committed
form.reset()                # revert to committed values
```

<a id="commandhistory"></a>

### CommandHistory — [Back to Top](#table-of-contents)

`CommandHistory` manages an undo/redo stack. Any object satisfying the `Command` protocol (`description` property, `execute()`, `undo()`) can be pushed. `CommandTransaction` groups multiple commands into a single undoable unit.

```python
from gui_do import CommandHistory, CommandTransaction

history = CommandHistory(max_size=100)
history.push(my_command)   # executes and records
history.undo()
history.redo()

with history.transaction("Bulk edit") as tx:
    tx.add(cmd_a)
    tx.add(cmd_b)
```

<a id="statemachine-and-router"></a>

### StateMachine and Router — [Back to Top](#table-of-contents)

`StateMachine(initial_state)` coordinates explicit state transitions with optional enter/exit callbacks.

```python
from gui_do import StateMachine

sm = StateMachine("idle")
sm.add_transition("idle", "running", trigger="start",
                  on_enter=lambda: print("started"))
sm.trigger("start")
print(sm.state)   # "running"
```

`Router` and `RouteEntry` support path-style navigation tables for multi-screen apps.

```python
from gui_do import Router, RouteEntry

router = Router()
router.add(RouteEntry("/home",     handler=show_home))
router.add(RouteEntry("/settings", handler=show_settings))
router.navigate("/settings")
```

<a id="settingsregistry"></a>

### SettingsRegistry — [Back to Top](#table-of-contents)

`SettingsRegistry` stores and loads namespaced settings backed by a JSON file. `SettingDescriptor` carries name, default value, and optional validation.

```python
from gui_do import SettingsRegistry, SettingDescriptor

reg = SettingsRegistry("myapp.settings.json")
reg.declare(SettingDescriptor("theme", default="dark"))
reg.set("theme", "light")
value = reg.get("theme")   # "light"
reg.save()
reg.load()
```

---

<a id="value-change-contracts"></a>

## Value Change Contracts — [Back to Top](#table-of-contents)

<a id="valuechangereason-and-valuechangecallback"></a>

### ValueChangeReason and ValueChangeCallback — [Back to Top](#table-of-contents)

`ValueChangeReason` is a `str` enum that tags the source of a slider or scrollbar value change. It is passed as the optional second argument to `on_change` callbacks.

```python
from gui_do import ValueChangeReason

# Members:
ValueChangeReason.KEYBOARD       # arrow key or Page/Home/End
ValueChangeReason.PROGRAMMATIC   # set_value / adjust_value
ValueChangeReason.MOUSE_DRAG     # pointer drag
ValueChangeReason.WHEEL          # mouse wheel
```

`ValueChangeCallback` is a type alias for `on_change` callbacks. Both one-argument (`value`) and two-argument (`value, reason`) signatures are accepted by default (compat mode). Pass `on_change_mode="reason-required"` to enforce the two-argument form at construction time.

```python
from gui_do import SliderControl, ValueChangeReason

def on_change(value: float, reason: ValueChangeReason | None = None) -> None:
    print(f"{value} via {reason}")

slider = SliderControl("s", rect, axis, 0, 100, 50, on_change=on_change)
slider.set_on_change_mode("reason-required")
slider.set_on_change_callback(on_change)
```

---

<a id="scheduling-and-animation"></a>

## Scheduling and Animation — [Back to Top](#table-of-contents)

<a id="taskscheduler"></a>

### TaskScheduler — [Back to Top](#table-of-contents)

`TaskScheduler` runs background tasks in a thread pool and delivers `TaskEvent` progress, completion, and error updates back to the UI through the event bus.

```python
scheduler = app.scheduler   # scene-local instance

task_id = scheduler.submit(
    "render",
    work_fn=lambda: heavy_computation(),
    on_progress=lambda pct: update_progress(pct),
    on_done=lambda result: show_result(result),
    on_error=lambda exc: show_error(str(exc)),
)
scheduler.cancel(task_id)
```

<a id="timers"></a>

### Timers — [Back to Top](#table-of-contents)

`Timers` schedules one-shot and repeating callbacks in frame time. Scene-local timers are suspended when the scene is inactive.

```python
timers = app.timers

token = timers.after(2.0, lambda: print("two seconds later"))
repeat_token = timers.every(0.5, lambda: tick())
timers.cancel(token)
```

<a id="tweenmanager"></a>

### TweenManager — [Back to Top](#table-of-contents)

`TweenManager` animates numeric properties over time. `TweenHandle` allows cancelling in-flight tweens. `Easing` provides standard curves.

```python
from gui_do import Easing

tweens = app.tweens

handle = tweens.tween(
    target=my_ctrl,
    attr="rect.x",
    end=200,
    duration=0.4,
    easing=Easing.EASE_IN_OUT,
    on_done=lambda: print("done"),
)
handle.cancel()

# Easing members: LINEAR, EASE_IN, EASE_OUT, EASE_IN_OUT, BOUNCE, ELASTIC
```

---

<a id="overlay-and-dialog-services"></a>

## Overlay and Dialog Services — [Back to Top](#table-of-contents)

<a id="overlaymanager-and-overlaypanelcontrol"></a>

### OverlayManager and OverlayPanelControl — [Back to Top](#table-of-contents)

`OverlayManager` shows and dismisses floating overlay nodes above the main scene. The returned `OverlayHandle` tracks the overlay lifetime.

```python
from gui_do import OverlayPanelControl

panel = OverlayPanelControl("popup", Rect(100, 100, 300, 200))
panel.add(LabelControl("msg", Rect(8, 8, 284, 28), "Hello from overlay"))

handle = app.overlay.show("popup", panel, dismiss_on_outside_click=True)
handle.dismiss()
```

<a id="toastmanager"></a>

### ToastManager — [Back to Top](#table-of-contents)

`ToastManager` displays transient notification banners with severity classification.

```python
from gui_do import ToastSeverity

app.toasts.show("File saved",  severity=ToastSeverity.SUCCESS, duration=3.0)
app.toasts.show("Low memory",  severity=ToastSeverity.WARNING)
app.toasts.show("Write error", severity=ToastSeverity.ERROR)
app.toasts.show("Tip",         severity=ToastSeverity.INFO)

# ToastSeverity members: INFO, SUCCESS, WARNING, ERROR
```

<a id="dialogmanager"></a>

### DialogManager — [Back to Top](#table-of-contents)

`DialogManager` presents modal alert, confirm, and prompt dialogs. The returned `DialogHandle` can be used to dismiss programmatically.

```python
handle = app.dialogs.alert("Operation complete", title="Done")
handle = app.dialogs.confirm("Delete file?",
                             on_confirm=lambda: do_delete(),
                             on_cancel=lambda: None)
handle = app.dialogs.prompt("Enter name:", on_submit=lambda v: use_name(v))
handle.dismiss()
```

<a id="contextmenumanager"></a>

### ContextMenuManager — [Back to Top](#table-of-contents)

`ContextMenuManager` displays a pointer-anchored context menu from a list of `ContextMenuItem` entries. Use `separator=True` to insert a visual divider.

```python
from gui_do import ContextMenuItem

items = [
    ContextMenuItem("Cut",   action=do_cut),
    ContextMenuItem("Copy",  action=do_copy),
    ContextMenuItem(separator=True),
    ContextMenuItem("Paste", action=do_paste, enabled=False),
]
handle = app.context_menus.show(items, anchor_pos=(x, y))
```

<a id="dragdropmanager"></a>

### DragDropManager — [Back to Top](#table-of-contents)

`DragDropManager` coordinates typed drag sessions between source and target controls using `DragPayload`.

```python
from gui_do import DragPayload

drag_drop = app.drag_drop

drag_drop.begin_drag(DragPayload(kind="file", data={"path": "/tmp/x.txt"}))
drag_drop.register_drop_target(
    drop_zone_ctrl,
    accepts=lambda payload: payload.kind == "file",
    on_drop=lambda payload: handle_drop(payload.data),
)
```

<a id="filedialogmanager"></a>

### FileDialogManager — [Back to Top](#table-of-contents)

`FileDialogManager` presents modal file-open and file-save dialogs. Configure with `FileDialogOptions`. The returned `FileDialogHandle` resolves asynchronously via the `on_close` callback.

```python
from gui_do import FileDialogManager, FileDialogOptions

mgr = FileDialogManager(app)

# Open dialog:
opts = FileDialogOptions(
    title="Open Image",
    filters=[("Images", [".png", ".jpg", ".bmp"]), ("All", ["*"])],
    allow_new_file=False,
    multi_select=False,
)
handle = mgr.open(opts, on_close=lambda paths: load_image(paths[0]) if paths else None)

# Save dialog:
save_opts = FileDialogOptions(title="Save As", allow_new_file=True)
handle = mgr.open(save_opts, on_close=lambda paths: save_to(paths[0]) if paths else None)

handle.is_open   # True until closed
handle.result    # None while open; list[str] of selected paths after close
```

`FileDialogOptions` fields: `title`, `start_dir` (defaults to CWD), `filters` (list of `(label, [ext, ...])` pairs), `allow_new_file` (editable filename for save dialogs), `multi_select`.

<a id="resizemanager"></a>

### ResizeManager — [Back to Top](#table-of-contents)

`ResizeManager` centralizes callbacks for application window and scene geometry changes.

```python
from gui_do import ResizeManager

resize = ResizeManager(app)
resize.on_resize(lambda new_rect: relayout(new_rect))
```

---

<a id="menu-system"></a>

## Menu System — [Back to Top](#table-of-contents)

<a id="menubarcontrol-and-menuentry"></a>

### MenuBarControl and MenuEntry — [Back to Top](#table-of-contents)

`MenuBarControl` renders a horizontal application menu bar with flyout sub-menus. Each top-level menu is a `MenuEntry` (a `label` plus a list of `ContextMenuItem` items). It is most commonly constructed via `MenuBarManager.build(...)` rather than directly.

```python
from gui_do import MenuBarControl, MenuEntry, ContextMenuItem

bar = MenuBarControl(
    "menubar",
    Rect(0, 0, 800, 28),
    entries=[
        MenuEntry("File", items=[
            ContextMenuItem("New",  action=on_new),
            ContextMenuItem("Open", action=on_open),
            ContextMenuItem(separator=True),
            ContextMenuItem("Exit", action=on_exit),
        ]),
        MenuEntry("Edit", items=[
            ContextMenuItem("Undo", action=on_undo),
            ContextMenuItem("Redo", action=on_redo),
        ]),
    ],
)
app.scene.add(bar)
```

<a id="menubarmanager"></a>

### MenuBarManager — [Back to Top](#table-of-contents)

`MenuBarManager` lets independently developed features register their own top-level menus before a single merged `MenuBarControl` is built. Multiple `register_menu` calls with the same label append items to that menu, which is useful for shared menus like File or Edit.

```python
from gui_do import MenuBarManager, ContextMenuItem

mgr = MenuBarManager()

# Feature A:
mgr.register_menu("File", [
    ContextMenuItem("New",  action=on_new),
    ContextMenuItem("Open", action=on_open),
])

# Feature B appends to File and adds its own menu:
mgr.register_menu("File", [ContextMenuItem("Save", action=on_save)])
mgr.register_menu("View", [ContextMenuItem("Zoom In", action=zoom_in)])

# Build once and add to the scene:
bar = mgr.build("menubar", Rect(0, 0, app_width, 28), app)
app.scene.add(bar)
```

---

<a id="notification-system"></a>

## Notification System — [Back to Top](#table-of-contents)

<a id="notificationcenter"></a>

### NotificationCenter — [Back to Top](#table-of-contents)

`NotificationCenter` subscribes to `EventBus` topics and accumulates `NotificationRecord` entries. The `unread_count` and `records` properties are `ObservableValue` instances that can drive badge labels or list views reactively.

```python
from gui_do import NotificationCenter, NotificationRecord, ToastSeverity

nc = NotificationCenter(app.events, max_records=200)
nc.subscribe("build.done",   severity=ToastSeverity.SUCCESS)
nc.subscribe("build.failed", severity=ToastSeverity.ERROR, title="Build Error")

# Reactive badge:
nc.unread_count.on_change(lambda v: badge_label.__setattr__("text", str(v)))

# Manual record:
nc.add(NotificationRecord("Deployment complete", severity=ToastSeverity.SUCCESS))

nc.mark_all_read()
nc.clear()
nc.records.value       # list[NotificationRecord]
nc.unread_count.value  # int
```

`NotificationRecord` fields: `message`, `title`, `severity` (`ToastSeverity`), `topic`, `timestamp` (ISO-8601 string), `read`, `data`.

<a id="notificationpanelcontrol"></a>

### NotificationPanelControl — [Back to Top](#table-of-contents)

`NotificationPanelControl` is an overlay panel that renders the `NotificationCenter` log in reverse-chronological order. Each entry shows a severity-colored stripe, title, message, and timestamp. A "Mark all read" button appears in the header when unread items exist.

```python
from gui_do import NotificationPanelControl

panel = NotificationPanelControl("notif", Rect(600, 30, 320, 460), nc)
handle = app.overlay.show("notif", panel, dismiss_on_outside_click=True)
```

---

<a id="scene-transitions"></a>

## Scene Transitions — [Back to Top](#table-of-contents)

<a id="scenetransitionmanager"></a>

### SceneTransitionManager — [Back to Top](#table-of-contents)

`SceneTransitionManager` wraps `app.switch_scene(...)` with animated transitions. Call `go(scene_name)` instead of `switch_scene(...)` to get the animation. The transition snapshots the current scene, switches immediately, then uses the new scene's `TweenManager` to animate the snapshot away.

```python
from gui_do import SceneTransitionManager, SceneTransitionStyle

transitions = SceneTransitionManager(
    app,
    default_style=SceneTransitionStyle.FADE,
    default_duration=0.35,
)
transitions.set_style("editor", SceneTransitionStyle.SLIDE_LEFT, duration=0.25)
transitions.set_style("home",   SceneTransitionStyle.SLIDE_RIGHT)

transitions.go("editor")
transitions.go("home")
```

`SceneTransitionStyle` members: `NONE`, `FADE`, `SLIDE_LEFT`, `SLIDE_RIGHT`, `SLIDE_UP`, `SLIDE_DOWN`.

---

<a id="feature-system"></a>

## Feature System — [Back to Top](#table-of-contents)

<a id="feature-types"></a>

### Feature Types — [Back to Top](#table-of-contents)

Features are the primary unit of composable, lifecycle-managed behavior. All types inherit from `Feature`.

| Type | Purpose |
|---|---|
| `Feature` | Base class. Override any lifecycle hook. |
| `DirectFeature` | Owns UI construction and handles rendering directly. |
| `LogicFeature` | Pure computation, no direct UI. Receives commands and returns results. |
| `RoutedFeature` | Dispatches `FeatureMessage` payloads by topic or command key. |

`FeatureMessage` is the structured inter-feature envelope: `sender`, `target`, `payload` dict, plus `.topic`, `.command`, and `.event` convenience properties.

Lifecycle hooks (all optional):

```python
class MyFeature(Feature):
    def build(self, host) -> None:
        """Create controls and attach them to host.scene."""

    def bind_runtime(self, host) -> None:
        """Wire callbacks, subscribe to event bus, bind actions."""

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        """Assign tab_index values; return the next available index."""

    def on_update(self, host) -> None:
        """Called each frame while the feature's scene is active."""

    def handle_event(self, host, event) -> bool:
        """Return True if the event was consumed."""

    def draw(self, host, surface, theme) -> None:
        """Custom rendering pass."""

    def shutdown_runtime(self, host) -> None:
        """Release resources on unregister or app shutdown."""
```

Inter-feature messaging:

```python
# Send from within a feature:
self.send_message("other_feature", {"command": "refresh", "data": 42})

# Logic feature binding and command:
self.bind_logic("my_logic_feature", alias="calc")
self.send_logic_message({"command": "compute", "input": x}, alias="calc")
```

<a id="featuremanager"></a>

### FeatureManager — [Back to Top](#table-of-contents)

`FeatureManager` registers features, validates `HOST_REQUIREMENTS` field contracts, dispatches lifecycle hooks in order, and routes `FeatureMessage` envelopes between features.

```python
features = app.features

features.register(MyFeature("my_feature", scene_name="main"))
features.build_all(host)
features.bind_runtime_all(host)
features.configure_accessibility_all(host, tab_index_start=10)

features.send_message("sender_name", "receiver_name", {"command": "ping"})
features.unregister("my_feature")
```

---

<a id="theme-and-graphics"></a>

## Theme and Graphics — [Back to Top](#table-of-contents)

<a id="colortheme-and-thememanager"></a>

### ColorTheme and ThemeManager — [Back to Top](#table-of-contents)

`ColorTheme` supplies semantic color tokens and text rendering. Access it through `app.theme`.

```python
theme = app.theme
color = theme.accent   # pygame Color
theme.render_text(surface, "Hello", rect, role="body", align="left")
```

`ThemeManager` and `DesignTokens` enable runtime theme switching and token-level customization.

```python
from gui_do import ThemeManager, DesignTokens

tokens = DesignTokens(accent=(80, 140, 255), background=(20, 20, 28))
tm = ThemeManager(app)
tm.apply(tokens)
```

<a id="builtingraphicsfactory"></a>

### BuiltInGraphicsFactory — [Back to Top](#table-of-contents)

`BuiltInGraphicsFactory` constructs cached visual surfaces used by all built-in controls (`InteractiveVisuals`, `ToggleVisuals`, `FrameVisuals`, `WindowChromeVisuals`). Access it through `app.graphics_factory`. After a theme or font change, incrementing `font_revision()` signals controls to rebuild their cached visuals.

<a id="fontmanager"></a>

### FontManager — [Back to Top](#table-of-contents)

`FontManager` provides role-based font access. Built-in roles are `"body"`, `"title"`, and `"display"`. Access it through `app.theme.fonts`.

```python
font = app.theme.fonts.font_instance("body", size=16)
font.text_size("Hello")   # (width, height)
font.line_height           # int
```

---

<a id="telemetry"></a>

## Telemetry — [Back to Top](#table-of-contents)

gui_do includes an opt-in structured metrics system for runtime profiling and post-run hotspot analysis.

**Configuration and collection**:

```python
from gui_do import configure_telemetry, telemetry_collector, TelemetrySample

configure_telemetry(enabled=True, log_file="telemetry.jsonl", max_samples=10_000)
collector = telemetry_collector()   # TelemetryCollector singleton

collector.record(TelemetrySample(feature_name="render", duration_ms=12.4))
```

**Offline analysis**:

```python
from gui_do import (
    load_telemetry_log_file,
    analyze_telemetry_records,
    analyze_telemetry_log_file,
    render_telemetry_report,
)

records = load_telemetry_log_file("telemetry.jsonl")
analysis = analyze_telemetry_records(records)
# or equivalently:
analysis = analyze_telemetry_log_file("telemetry.jsonl")

print(render_telemetry_report(analysis))
# analysis.feature_hotspots — per-feature aggregated breakdown
```

---

<a id="public-api-index"></a>

## Public API Index — [Back to Top](#table-of-contents)

The following is the complete public export surface of `gui_do.__all__`.

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
- `MenuBarControl`
- `MenuEntry`
- `TreeControl`
- `TreeNode`
- `NotificationPanelControl`

### Layout

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

### Events, Focus, and Input

- `ActionManager`
- `EventManager`
- `EventBus`
- `FocusManager`
- `EventPhase`
- `EventType`
- `GuiEvent`

### Value Change Contracts

- `ValueChangeCallback`
- `ValueChangeReason`

### Data and State

- `InvalidationTracker`
- `ObservableValue`
- `PresentationModel`
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

### Runtime Services

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
- `ContextMenuManager`
- `ContextMenuItem`
- `ContextMenuHandle`
- `ResizeManager`
- `MenuBarManager`
- `FileDialogManager`
- `FileDialogOptions`
- `FileDialogHandle`
- `NotificationCenter`
- `NotificationRecord`
- `SceneTransitionManager`
- `SceneTransitionStyle`
- `FontManager`

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

### Telemetry

- `TelemetryCollector`
- `TelemetrySample`
- `configure_telemetry`
- `telemetry_collector`
- `analyze_telemetry_records`
- `analyze_telemetry_log_file`
- `load_telemetry_log_file`
- `render_telemetry_report`
