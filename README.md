[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

# gui_do

gui_do is a pygame GUI framework built around strict scene isolation, a composable Feature lifecycle, and a normalized event pipeline. It provides controls, layout, focus management, background task scheduling, pub-sub messaging, observable data binding, themes, and built-in telemetry — organized so that application logic and GUI structure stay separate by design.

<a id="table-of-contents"></a>

## Table of Contents

- [Quick Start](#quick-start)
- [Overview](#overview)
- [Minimal Runnable Example](#minimal-runnable-example)
- [Package Management](#package-management)
  - [Start a New Project](#start-a-new-project)
  - [Add to or Update an Existing Project](#add-to-or-update-an-existing-project)
- [Application Setup](#application-setup)
  - [GuiApplication](#guiapplication)
  - [Scene Management](#scene-management)
  - [The Run Loop](#the-run-loop)
  - [Cursor Management](#cursor-management)
- [Control Widgets](#control-widgets)
  - [Common Pattern and UiNode API](#common-pattern-and-uinode-api)
  - [PanelControl](#panelcontrol)
  - [ButtonControl](#buttoncontrol)
  - [ToggleControl](#togglecontrol)
  - [LabelControl](#labelcontrol)
  - [SliderControl](#slidercontrol)
  - [ScrollbarControl](#scrollbarcontrol)
  - [ButtonGroupControl](#buttongroupcontrol)
  - [ArrowBoxControl](#arrowboxcontrol)
  - [CanvasControl](#canvascontrol)
  - [ImageControl](#imagecontrol)
  - [FrameControl](#framecontrol)
  - [WindowControl](#windowcontrol)
  - [TaskPanelControl](#taskpanelcontrol)
- [Layout](#layout)
  - [LayoutManager](#layoutmanager)
  - [Window Tiling](#window-tiling)
- [Event Handling and Propagation](#event-handling-and-propagation)
  - [GuiEvent](#guievent)
  - [Event Dispatch](#event-dispatch)
  - [EventType and EventPhase](#eventtype-and-eventphase)
  - [Actions and Key Bindings](#actions-and-key-bindings)
- [Focus and Keyboard Input](#focus-and-keyboard-input)
  - [Tab Traversal](#tab-traversal)
  - [FocusManager](#focusmanager)
  - [Focus Visualization](#focus-visualization)
  - [Accessibility](#accessibility)
- [Features](#features)
  - [Feature Lifecycle Overview](#feature-lifecycle-overview)
  - [Feature — General-Purpose](#feature--general-purpose)
  - [DirectFeature — Screen Drawing](#directfeature--screen-drawing)
  - [LogicFeature — Domain Logic Service](#logicfeature--domain-logic-service)
  - [RoutedFeature — Topic-Routed Dispatch](#routedfeature--topic-routed-dispatch)
  - [Choosing a Feature Type](#choosing-a-feature-type)
  - [FeatureManager](#featuremanager)
  - [Feature Messaging](#feature-messaging)
  - [Feature Font Roles](#feature-font-roles)
  - [LogicFeature Runnables](#logicfeature-runnables)
  - [Screen Lifecycle Composition](#screen-lifecycle-composition)
  - [Scene Prewarm and First-Open Profiling](#scene-prewarm-and-first-open-profiling)
- [Background Services](#background-services)
  - [TaskScheduler](#taskscheduler)
  - [Timers](#timers)
  - [EventBus](#eventbus)
- [Observable Values and Data Binding](#observable-values-and-data-binding)
- [Themes, Styling, and Fonts](#themes-styling-and-fonts)
  - [ColorTheme](#colortheme)
  - [FontManager](#fontmanager)
  - [BuiltInGraphicsFactory](#builtingraphicsfactory)
- [Telemetry](#telemetry)
- [Advanced Patterns](#advanced-patterns)
  - [Pointer and Input Lock](#pointer-and-input-lock)
  - [InvalidationTracker](#invalidationtracker)
  - [Pristine Backgrounds](#pristine-backgrounds)
  - [EventManager](#eventmanager)
  - [GuiApplication Helpers Reference](#guiapplication-helpers-reference)

---

<a id="quick-start"></a>

## Quick Start — [Back to Top](#table-of-contents)

### Installation

```bash
# Run from a checkout (tests and demo included)
pip install pygame numpy

# Install the package into your environment from this checkout
pip install -e .
```

### Minimal Test Run

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

<a id="overview"></a>

## Overview — [Back to Top](#table-of-contents)

gui_do is organized around a small set of cooperating systems. Understanding how they relate is the key to using the package effectively.

**GuiApplication and Scenes.** `GuiApplication` is the central coordinator. It owns one or more named scenes, each of which is an isolated runtime: its own node graph, scheduler, timers, color theme, and graphics factory. Switching scenes with `switch_scene(name)` swaps all of these services atomically. Controls are added to scenes, not to the application directly.

**Controls and the UiNode Tree.** Every visible widget — buttons, labels, sliders, canvases, windows, panels — extends `UiNode`. Controls are composed into a tree: a `PanelControl` holds child controls, a `WindowControl` holds its own sub-tree. The tree is walked during event dispatch and rendering. You add controls with `parent.add(child)`.

**Events.** Raw pygame events enter through `app.process_event(event)`, are normalized into `GuiEvent` objects, and dispatched through the scene graph in three phases: capture (root → target), target, and bubble (target → root). `GuiEvent` carries semantic kind, position, key codes, and propagation state. Applications intercept events via screen lifecycle callbacks, Feature handlers, or per-control `handle_routed_event` overrides.

**Features.** The Feature system is how application logic is attached to the GUI. A `Feature` is a managed object with lifecycle hooks (`build`, `bind_runtime`, `on_update`, `draw`, `shutdown_runtime`, and more). Features are registered with the application, built in one pass, bound to runtime services in another, and updated each frame. There are four subtypes: the base `Feature` for controls and wiring; `RoutedFeature` which adds topic-keyed message dispatch; `LogicFeature` for headless domain logic services that respond to command messages; and `DirectFeature` for fullscreen animation or raw per-frame drawing that bypasses the widget pipeline.

**Scheduler and Timers.** `TaskScheduler` runs background work in a thread pool and delivers completion messages and progress payloads back to the main thread during `update()`. Each scene has its own scheduler, suspended automatically when the scene is not active. `Timers` provides one-shot and repeating frame callbacks, also per-scene.

**EventBus.** `EventBus` (accessible as `app.events`) is a scoped pub-sub channel for non-input application events: status changes, data-ready signals, and cross-Feature notifications that do not need the strict Feature messaging queue.

**Themes and Fonts.** Each scene has a `ColorTheme` with a palette and a `FontManager`. Font roles (named sizes and typefaces, e.g. `"body"`, `"title"`) are registered per-scene. Controls reference roles by name; changing a role invalidates all controls that use it. `BuiltInGraphicsFactory` renders the visual bitmaps used by every built-in control.

**Layout.** `LayoutManager` computes anchor-based, linear-strip, and grid positions. `WindowTilingManager` automatically tiles floating windows within the work area, respecting task panel boundaries.

**Focus.** `FocusManager` tracks the focused control, manages tab-index traversal, scopes focus to active windows, and drives the `FocusVisualizer` which renders a dashed hint ring around the focused control.

**Observable Values.** `ObservableValue` and `PresentationModel` provide reactive data: subscribers receive the new value whenever it changes, and `PresentationModel` tracks subscriptions for bulk disposal.

**What it is best suited for.** gui_do is well suited for desktop tools, data visualization dashboards, simulation front-ends, and any application that needs multiple independent scenes, background computation with main-thread result delivery, and a clean separation between UI structure and application logic. It is not a layout-engine-first or styling-engine-first framework; it trades declarative layout for explicit, code-driven control over scene isolation and Feature composition.

---

<a id="minimal-runnable-example"></a>

## Minimal Runnable Example — [Back to Top](#table-of-contents)

```python
import pygame
from pygame import Rect

from gui_do import GuiApplication, PanelControl, LabelControl, ButtonControl

pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("gui_do minimal app")

app = GuiApplication(screen)
app.create_scene("main")
app.switch_scene("main")
app.layout.set_anchor_bounds(screen.get_rect())

root = app.add(
    PanelControl("root", Rect(0, 0, screen.get_width(), screen.get_height())),
    scene_name="main",
)

label = root.add(LabelControl("hello", Rect(20, 20, 420, 32), "Hello, gui_do"))
app.style_label(label, size=20, role="body")

button = root.add(
    ButtonControl("quit", Rect(20, 64, 120, 32), "Quit", on_click=app.quit)
)
button.set_tab_index(0)

import pygame as pg
app.actions.register_action("exit", lambda _event: (app.quit() or True))
app.actions.bind_key(pg.K_ESCAPE, "exit", scene="main")

app.run(target_fps=60)
pygame.quit()
```

---

<a id="package-management"></a>

## Package Management — [Back to Top](#table-of-contents)

<a id="start-a-new-project"></a>

### Start a New Project — [Back to Top](#table-of-contents)

This is a current-folder workflow. Open a terminal in the folder that contains `scripts/manage.py` and run commands from there. It strips bundled demo content and produces a clean gui_do library base ready for your application.

```bash
# Preview what init would do without changing any files
python scripts/manage.py init --dry-run

# Apply: strip demo content, scaffold a starter app, and verify contracts
python scripts/manage.py init --scaffold --verify
```

What `init` does:

- Sets `DEMO_CONTRACTS_ENABLED = False` in `tests/contract_test_catalog.py`
- Removes `*_demo.py` entrypoints from the repo root
- Removes the `demo_features/` tree and all tests that import from it
- Updates docs and CI workflow
- Creates a starter `myapp.py` and `features/` package when `--scaffold` is passed

After running `init`, open `myapp.py` and adapt the Minimal Runnable Example to your project.

To apply the same policy steps to a folder that already had `init` run (safe to repeat):

```bash
python scripts/manage.py apply --verify
```

To run only the contract verification without changing files:

```bash
python scripts/manage.py verify
```

<a id="add-to-or-update-an-existing-project"></a>

### Add to or Update an Existing Project — [Back to Top](#table-of-contents)

Use `update` both when adding gui_do to an existing project for the first time and when upgrading to a newer version. Think in terms of a source folder (where you run the command) and a target project (passed via `--target`).

Run `update` from the root of the package files you want to copy — the folder containing `scripts/manage.py`, `README.md`, `pyproject.toml`, and the top-level `gui_do/` directory.

```bash
# Optional: check for conflicts before copying
python scripts/manage.py check --target /path/to/your/project

# Copy package files and apply contract parity in one pass
python scripts/manage.py update --target /path/to/your/project --verify

# Preview what would change without writing anything
python scripts/manage.py update --target /path/to/your/project --dry-run
```

`update` copies these items from source into the target: `gui_do/`, `scripts/`, `tests/`, `docs/`, `README.md`, `pyproject.toml`, `MANIFEST.in`, `LICENSE`, `requirements-ci.txt`.

If the updated package files are already in your project folder (no separate source needed):

```bash
python scripts/manage.py apply --verify
```

---

<a id="application-setup"></a>

## Application Setup — [Back to Top](#table-of-contents)

<a id="guiapplication"></a>

### GuiApplication — [Back to Top](#table-of-contents)

`GuiApplication` is constructed with a pygame surface and coordinates all GUI services.

```python
import pygame
from gui_do import GuiApplication

pygame.init()
screen = pygame.display.set_mode((1280, 720))
app = GuiApplication(screen)
```

Key attributes available after construction:

| Attribute | Type | Description |
|---|---|---|
| `app.surface` | `pygame.Surface` | The display surface |
| `app.scene` | `Scene` | Active scene graph |
| `app.theme` | `ColorTheme` | Active scene theme |
| `app.scheduler` | `TaskScheduler` | Active scene scheduler |
| `app.timers` | `Timers` | Active scene timer service |
| `app.window_tiling` | `WindowTilingManager` | Active scene tiling manager |
| `app.graphics_factory` | `BuiltInGraphicsFactory` | Active scene graphics factory |
| `app.focus` | `FocusManager` | Application focus manager |
| `app.focus_visualizer` | `FocusVisualizer` | Focus hint renderer |
| `app.actions` | `ActionManager` | Key-to-action binding registry |
| `app.events` | `EventBus` | Application-wide pub-sub bus |
| `app.event_manager` | `EventManager` | Raw-to-GuiEvent converter |
| `app.invalidation` | `InvalidationTracker` | Redraw tracking |
| `app.layout` | `LayoutManager` | Layout computation helpers |
| `app.features` | `FeatureManager` | Feature lifecycle coordinator |
| `app.active_scene_name` | `str` | Name of the currently active scene |
| `app.logical_pointer_pos` | `tuple` | Current lock-adjusted pointer position |
| `app.mouse_point_locked` | `bool` | True when point-lock is active |
| `app.lock_point_pos` | `tuple\|None` | Point-lock anchor position |
| `app.running` | `bool` | Set to False to exit the run loop |

The main loop calls three methods each frame:

```python
app.process_event(event)   # normalize and dispatch one pygame event
app.update(dt_seconds)     # advance scene timers, scheduler, features, and focus
app.draw()                 # render the active scene
```

`app.quit()` sets `app.running = False` to exit the loop gracefully.

<a id="scene-management"></a>

### Scene Management — [Back to Top](#table-of-contents)

Each scene is an isolated runtime (node graph, scheduler, timers, theme, graphics factory). Switching scenes swaps all these services atomically.

```python
# Create scenes (does NOT make them active)
app.create_scene("main")
app.create_scene("settings")

# Activate the startup scene
app.switch_scene("main")

# Query scenes
names = app.scene_names()           # list of all registered scene names
exists = app.has_scene("settings")  # True/False
active = app.active_scene_name      # name of the active scene

# Remove a non-active scene (returns False if active or not found)
removed = app.remove_scene("settings")

# Add a node to a specific scene without switching to it
app.add(my_control, scene_name="settings")

# Access a scene's services directly by name
scheduler = app.get_scene_scheduler("settings")
factory   = app.get_scene_graphics_factory("settings")

# Configure tiling for a non-active scene (no switch needed)
app.configure_window_tiling(
    gap=16, padding=16,
    avoid_task_panel=True,
    center_on_failure=True,
    relayout=False,
    scene_name="settings",
)
app.set_window_tiling_enabled(True, relayout=False, scene_name="settings")
```

When a scene is made inactive, its scheduler is paused and its tasks are suspended automatically. They resume when the scene becomes active again.

**Feature bootstrap order:**

```python
# Register Features (on_register called immediately)
app.register_feature(MyFeature(), host=demo)

# Build all controls (build hook)
app.build_features(demo)   # also primes window tiling registration for all scenes

# Bind runtime services (bind_runtime hook)
app.bind_features_runtime(demo)

# Optional: prewarm one-time setup for heavy scenes before first display
app.prewarm_scene("main")
```

<a id="the-run-loop"></a>

### The Run Loop — [Back to Top](#table-of-contents)

`app.run()` manages the loop internally and is the preferred entry point.

```python
# Standard usage — returns number of frames processed
frames = app.run(target_fps=60)

# Bounded run — exits after at most N frames (useful in tests)
frames = app.run(target_fps=60, max_frames=300)
```

Use `UiEngine` directly only when you need frame-level control from an outer runner:

```python
from gui_do import UiEngine

engine = UiEngine(app, target_fps=60)
frames = engine.run(max_frames=300)
print(f"Average FPS: {engine.current_fps:.1f}")
```

The engine calls `app.process_event`, `app.update`, `app.draw`, and `pygame.display.flip` each frame, then calls `app.shutdown()` when the loop exits.

<a id="cursor-management"></a>

### Cursor Management — [Back to Top](#table-of-contents)

`GuiApplication` hides the system cursor at startup and renders a software cursor each frame. Two built-in cursors are registered by default: `"normal"` and `"hand"`.

```bash
# Register a custom cursor (path is CWD-relative or absolute)
app.register_cursor("crosshair", "assets/cursors/crosshair.png", hotspot=(8, 8))

# Switch the active cursor
app.set_cursor("hand")
app.set_cursor("normal")
app.set_cursor("crosshair")

# Read the active cursor surface (returns None if no cursor is set)
surface = app.get_active_cursor()
```

---

<a id="control-widgets"></a>

## Control Widgets — [Back to Top](#table-of-contents)

<a id="common-pattern-and-uinode-api"></a>

### Common Pattern and UiNode API — [Back to Top](#table-of-contents)

All controls extend `UiNode`. Create a control with a unique `control_id`, a bounding `Rect`, and type-specific options; then add it to a parent with `parent.add(child)`.

**UiNode properties and methods available on every control:**

```python
# Visibility and enabled state
node.visible = False        # hide; triggers on_visibility_changed hook
node.enabled = False        # disable; triggers on_enabled_changed hook
node.show()                 # equivalent to node.visible = True
node.hide()                 # equivalent to node.visible = False
node.enable()               # equivalent to node.enabled = True
node.disable()              # equivalent to node.enabled = False

# Geometry (all mutations call invalidate())
node.set_pos(x, y)          # move top-left corner
node.resize(width, height)  # resize without moving
node.set_rect(rect)         # replace rect entirely
node.rect                   # pygame.Rect; mutable geometry

# Tree traversal
node.parent                 # immediate parent UiNode, or None
node.children               # list of direct children
node.ancestors()            # generator from parent to root
node.is_root()              # True when node has no parent
node.depth()                # int; 0 for root nodes
node.sibling_index()        # position among parent.children
node.find_descendant("id")              # first BFS match by control_id, or None
node.find_descendants(predicate)        # list of all BFS matches by predicate
node.find_descendants_of_type(cls)      # list of all BFS matches by type

# Identity
node.control_id             # str; unique identifier within the scene

# Focus and accessibility
node.tab_index              # int; -1 = not focusable, >= 0 = in Tab order
node.focused                # bool; True when this node holds keyboard focus
node.accepts_focus()        # True when tab_index >= 0
node.accepts_mouse_focus()  # True when a click should transfer focus here
node.set_tab_index(n)       # set the tab order index
node.set_accessibility(role="button", label="Save File")

# Invalidation
node.invalidate()           # mark as dirty for next draw pass
```

<a id="panelcontrol"></a>

### PanelControl — [Back to Top](#table-of-contents)

Base container for child controls. Groups related widgets, manages floating windows, and optionally draws a theme background fill.

```python
from gui_do import PanelControl

# Container with a background fill
panel = root.add(
    PanelControl("sidebar", Rect(0, 0, 240, screen_height), draw_background=True)
)

# Transparent container (common for the root layout panel)
root_panel = app.add(
    PanelControl("root", screen_rect, draw_background=False),
    scene_name="main",
)

# Add and remove children
label  = panel.add(LabelControl("info", Rect(8, 8, 224, 24), "Content"))
button = panel.add(ButtonControl("ok", Rect(8, 40, 100, 32), "OK"))
panel.remove(label)
```

<a id="buttoncontrol"></a>

### ButtonControl — [Back to Top](#table-of-contents)

Clickable push button that fires a callback on activation.

```python
from gui_do import ButtonControl

button = parent.add(
    ButtonControl(
        "button_id",
        rect,
        "Button Text",
        on_click=lambda: print("clicked"),
        style="box",       # "box" (default), "radio", "round", "angle", "check"
        font_role="body",  # registered font role name
    )
)

# Interaction state
button.hovered   # True while pointer is over the button
button.pressed   # True while mouse button is held down

# Mutate at runtime
button.text      = "New Label"
button.style     = "round"
button.font_role = "body"   # empty string raises ValueError

# Replace or remove callback
button.set_on_click(lambda: print("new callback"))
button.set_on_click(None)
```

Keyboard: `Space` or `Return` activates when focused.

<a id="togglecontrol"></a>

### ToggleControl — [Back to Top](#table-of-contents)

Two-state button that tracks a `pushed` boolean and fires `on_toggle(pushed: bool)` on each change.

```python
from gui_do import ToggleControl

toggle = parent.add(
    ToggleControl(
        "toggle_id",
        rect,
        text_on="ON",        # label when pushed=True
        text_off="OFF",      # label when pushed=False (defaults to text_on)
        pushed=False,
        on_toggle=lambda pushed: print(f"State: {pushed}"),
        style="box",         # "box", "radio", "round", "angle", "check"
        font_role="body",
    )
)

# Read / set state
is_on         = toggle.pushed
toggle.pushed = True

# Replace or remove callback
toggle.set_on_toggle(lambda pushed: print(pushed))
toggle.set_on_toggle(None)

toggle.font_role = "body"   # must be a registered role name
```

Keyboard: `Space` or `Return` activates when focused.

<a id="labelcontrol"></a>

### LabelControl — [Back to Top](#table-of-contents)

Read-only text display. Clicking a label never steals keyboard focus.

```python
from gui_do import LabelControl

label = parent.add(
    LabelControl("label_id", rect, "Initial Text", align="left")
)

label.text      = "Updated text"
label.font_role = "body"    # registered font role
label.font_size = 14        # integer point size
label.align     = "center"  # "left", "center", or "right"

# Convenience helper
app.style_label(label, size=14, role="body")
```

<a id="slidercontrol"></a>

### SliderControl — [Back to Top](#table-of-contents)

Numeric input via mouse drag or keyboard. Uses the strict `(value, reason)` callback contract.

```python
from gui_do import SliderControl, LayoutAxis, ValueChangeReason

def on_change(value, reason):
    if reason is ValueChangeReason.MOUSE_DRAG:
        ...
    elif reason is ValueChangeReason.KEYBOARD:
        ...

slider = parent.add(
    SliderControl(
        "slider_id",
        rect,
        axis=LayoutAxis.HORIZONTAL,   # or LayoutAxis.VERTICAL
        minimum=0,
        maximum=100,
        value=50,
        on_change=on_change,
    )
)

slider.set_value(75)           # set absolute value, clamped; returns True if changed
slider.adjust_value(5)         # move by delta, clamped; returns True if changed
slider.set_normalized(0.5)     # set from 0.0-1.0 ratio; returns True if changed
print(slider.value)            # current value
print(slider.normalized)       # current value as 0.0-1.0 ratio

slider.set_on_change_callback(new_callback)
```

`ValueChangeReason` members:

| Member | Trigger |
|---|---|
| `KEYBOARD` | Arrow keys, Home, End, PageUp, PageDown |
| `MOUSE_DRAG` | Thumb drag |
| `WHEEL` | Mouse scroll wheel |
| `PROGRAMMATIC` | `set_value()`, `adjust_value()`, `set_normalized()` |

<a id="scrollbarcontrol"></a>

### ScrollbarControl — [Back to Top](#table-of-contents)

Viewport scrolling. Describes a position within content: `content_size` is the total scrollable length, `viewport_size` is the visible window, `offset` is the current position.

```python
from gui_do import ScrollbarControl, LayoutAxis, ValueChangeReason

scrollbar = parent.add(
    ScrollbarControl(
        "scrollbar_id",
        rect,
        axis=LayoutAxis.VERTICAL,
        content_size=1000,
        viewport_size=200,
        offset=0,
        step=20,
        on_change=lambda offset, reason: print(offset, reason),
    )
)

scrollbar.set_offset(100)      # absolute position, clamped; returns True if changed
scrollbar.adjust_offset(20)    # relative move, clamped; returns True if changed
print(scrollbar.scroll_fraction)   # 0.0-1.0 normalized position

scrollbar.set_on_change_callback(new_callback)
```

`ValueChangeReason` applies the same way as `SliderControl`; `set_offset` and `adjust_offset` trigger `PROGRAMMATIC`.

<a id="buttongroupcontrol"></a>

### ButtonGroupControl — [Back to Top](#table-of-contents)

Mutually exclusive selection (radio button behavior). Each instance is one option in a named group.

```python
from gui_do import ButtonGroupControl

btn_a = parent.add(ButtonGroupControl(
    "option_a", rect_a, group="view_mode", text="List",
    selected=True, on_activate=lambda: print("List"), font_role="body",
))
btn_b = parent.add(ButtonGroupControl("option_b", rect_b, group="view_mode", text="Grid"))
btn_c = parent.add(ButtonGroupControl("option_c", rect_c, group="view_mode", text="Detail"))

# Query state
print(btn_a.pushed)      # True when this button is selected
print(btn_a.button_id)   # control_id of whichever button is currently selected

# Replace or remove activation callback
btn_a.set_on_activate(lambda: print("new callback"))
btn_a.set_on_activate(None)

btn_a.font_role = "body"

# Clear stale group state (useful between independent test instances)
ButtonGroupControl.clear_group_registry("view_mode")
```

Keyboard: `Space` or `Return` activates when focused.

<a id="arrowboxcontrol"></a>

### ArrowBoxControl — [Back to Top](#table-of-contents)

Clickable arrow button with optional hold-repeat. Direction in degrees: 0 = right, 90 = down, 180 = left, 270 = up.

```python
from gui_do import ArrowBoxControl

up_arrow = parent.add(
    ArrowBoxControl(
        "up_arrow",
        rect,
        direction=270,
        on_activate=lambda: print("Up"),
        repeat_interval_seconds=0.08,
    )
)

up_arrow.set_on_activate(lambda: print("new callback"))
up_arrow.set_on_activate(None)
```

<a id="canvascontrol"></a>

### CanvasControl — [Back to Top](#table-of-contents)

High-performance drawable surface with an internal event queue. Mouse events are queued as `CanvasEventPacket` objects and drained by the caller each frame.

```python
from gui_do import CanvasControl, CanvasEventPacket

canvas = parent.add(
    CanvasControl("canvas_id", rect, max_events=256)
)

# Configure overflow behavior
canvas.set_overflow_mode("drop_oldest")   # default; also "drop_newest"
canvas.set_overflow_handler(
    lambda dropped, size: print(f"Dropped {dropped} events, queue={size}")
)
canvas.set_motion_coalescing(True)   # merge consecutive motion events (default True)

# Drain events each frame (e.g., in Feature.on_update)
packet = canvas.read_event()
while packet is not None:
    if packet.is_left_down():
        lx, ly = packet.local_pos   # canvas-local coordinates
    elif packet.is_mouse_motion():
        print(packet.pos, packet.local_pos, packet.rel)
    elif packet.is_mouse_wheel():
        print(packet.wheel_delta)
    packet = canvas.read_event()

# Draw to the backing surface
surface = canvas.get_canvas_surface()
pygame.draw.circle(surface, (255, 0, 0), (100, 100), 50)
```

`CanvasEventPacket` helper methods: `is_mouse_motion()`, `is_mouse_wheel()`, `is_mouse_down(button)`, `is_mouse_up(button)`, `is_left_down()`, `is_left_up()`, `is_right_down()`, `is_right_up()`, `is_middle_down()`, `is_middle_up()`.

Fields: `kind`, `pos` (screen coordinates), `local_pos` (canvas-relative), `rel`, `button`, `wheel_delta`.

<a id="imagecontrol"></a>

### ImageControl — [Back to Top](#table-of-contents)

Displays a PNG/JPG image scaled to fit its rect.

```python
from gui_do import ImageControl

image = parent.add(ImageControl("image_id", rect, image_path="assets/backdrop.jpg"))
image.set_image("assets/new_image.png")
```

<a id="framecontrol"></a>

### FrameControl — [Back to Top](#table-of-contents)

Decorative border frame that groups content visually.

```python
from gui_do import FrameControl

frame = parent.add(FrameControl("frame_id", rect, border_width=2))
label = frame.add(LabelControl("content", inner_rect, "Framed Content"))
frame.border_width = 3   # update at runtime (triggers invalidation)
```

<a id="windowcontrol"></a>

### WindowControl — [Back to Top](#table-of-contents)

Floating, draggable window with a title bar and frame. Add to a `PanelControl`, which manages z-order and activation.

```python
from gui_do import WindowControl

window = panel.add(
    WindowControl(
        "window_id",
        rect,
        "Window Title",
        titlebar_height=24,
        title_font_role="title",
        preamble=None,            # optional: called before each event dispatch cycle
        event_handler=None,       # optional: custom event handler
        postamble=None,           # optional: called after each event dispatch cycle
        use_frame_backdrop=True,  # True = factory backdrop; False = plain black
    )
)

# Add controls inside
button = window.add(ButtonControl("btn", inner_rect, "Click me"))

# Query / mutate
is_active    = window.active           # bool; read/write
window_rect  = window.rect
content      = window.content_rect()   # excludes title bar
title_bar    = window.title_bar_rect()
window.close()                         # hide and release active state
window.move_by(dx=10, dy=0)           # move by a pixel delta

# Pristine backdrop inside the window
window.set_pristine(my_surface)
window.restore_pristine(surface)
```

<a id="taskpanelcontrol"></a>

### TaskPanelControl — [Back to Top](#table-of-contents)

Slide-in/slide-out panel along a screen edge, typically for application-level action buttons.

```python
from gui_do import TaskPanelControl, ButtonControl
from pygame import Rect

task_panel = root.add(
    TaskPanelControl(
        "task_panel",
        Rect(0, 0, screen_width, 48),
        auto_hide=True,          # slide out when not hovered
        hidden_peek_pixels=4,    # pixels visible when hidden (hover target)
        animation_step_px=4,     # pixels per frame while animating
        dock_bottom=False,       # True = dock to bottom edge
    )
)

exit_btn = task_panel.add(
    ButtonControl("exit_btn", Rect(8, 8, 100, 32), "Exit", on_click=app.quit)
)

# Mutate at runtime
task_panel.set_auto_hide(False)
task_panel.set_hidden_peek_pixels(8)
task_panel.set_animation_step_px(6)
```

---

<a id="layout"></a>

## Layout — [Back to Top](#table-of-contents)

<a id="layoutmanager"></a>

### LayoutManager — [Back to Top](#table-of-contents)

`LayoutManager` is available as `app.layout`. It computes rects for anchor-based, linear-strip, and grid arrangements.

```python
from gui_do import LayoutAxis

# Set anchor bounds (usually the screen rect)
app.layout.set_anchor_bounds(screen.get_rect())

# Anchor-based positioning
rect = app.layout.anchored(
    size=(200, 100),
    anchor="top_right",   # top_left | top_center | top_right
                          # center_left | center | center_right
                          # bottom_left | bottom_center | bottom_right
    margin=(20, 20),      # (horizontal margin, vertical margin)
    use_rect=True,        # True = return Rect; False = return (x, y)
)

# Linear layout (auto-advancing cursor)
app.layout.set_linear_properties(
    anchor=(100, 100),
    item_width=120,
    item_height=32,
    spacing=10,
    horizontal=True,
    wrap_count=0,     # wrap after N items (0 = no wrap)
    use_rect=True,
)
rect1 = app.layout.next_linear()   # advances cursor
rect2 = app.layout.next_linear()
rect_at_3 = app.layout.linear(3)   # by index, does not advance cursor

# Grid layout
app.layout.set_grid_properties(
    anchor=(40, 40),
    item_width=160,
    item_height=120,
    column_spacing=12,
    row_spacing=12,
    use_rect=True,
)
rect_0_0  = app.layout.gridded(column=0, row=0)
rect_wide = app.layout.gridded(column=1, row=0, column_span=2)
rect_a    = app.layout.next_gridded(columns=3)   # auto-advance; pass column count for wrapping
rect_b    = app.layout.next_gridded(columns=3)
```

<a id="window-tiling"></a>

### Window Tiling — [Back to Top](#table-of-contents)

`WindowTilingManager` automatically tiles floating windows within the screen work area. `build_features(host)` primes registration order for all scenes automatically.

```python
app.configure_window_tiling(
    gap=16,
    padding=16,
    avoid_task_panel=True,    # exclude the task panel area from the work region
    center_on_failure=True,   # center window when tiling cannot fit all windows
    relayout=False,           # trigger immediate relayout when True
    scene_name="main",        # optional: target a non-active scene
)

app.set_window_tiling_enabled(True, relayout=False, scene_name="main")

# Trigger relayout after visibility changes
app.tile_windows()                        # relayout all visible windows
app.tile_windows(newly_visible=[window])  # hint: only place the newly shown window

# Read current tiling settings
settings = app.read_window_tiling_settings()

# Disable tiling
app.set_window_tiling_enabled(False)

# Access the active scene's tiling manager directly
tiler = app.window_tiling
tiler.prime_registration()   # stamp registration order now; idempotent for existing windows
```

---

<a id="event-handling-and-propagation"></a>

## Event Handling and Propagation — [Back to Top](#table-of-contents)

<a id="guievent"></a>

### GuiEvent — [Back to Top](#table-of-contents)

`GuiEvent` is the normalized event type produced by `EventManager.to_gui_event()` and dispatched through every part of the framework.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `kind` | `EventType` | Semantic event type enum |
| `type` | `int` | Raw pygame event type integer |
| `key` | `Optional[int]` | Keyboard key code (key events only) |
| `mod` | `int` | Keyboard modifier bitmask |
| `pos` | `Optional[tuple]` | Logical pointer position (lock-adjusted) |
| `rel` | `Optional[tuple]` | Logical motion delta |
| `raw_pos` | `Optional[tuple]` | Raw pygame position before lock adjustment |
| `raw_rel` | `Optional[tuple]` | Raw pygame motion delta |
| `button` | `Optional[int]` | Mouse button index (1=left, 2=middle, 3=right) |
| `wheel_x` | `int` | Horizontal wheel delta |
| `wheel_y` | `int` | Vertical wheel delta |
| `text` | `Optional[str]` | Text input character (TEXT_INPUT events) |
| `widget_id` | `Optional[str]` | Widget control_id for widget events |
| `task_panel` | `bool` | True when event originates from the task panel |
| `task_id` | `Optional[Hashable]` | Scheduler task id for task events |
| `error` | `Optional[str]` | Error message for failed task events |
| `phase` | `EventPhase` | Current dispatch phase (CAPTURE/TARGET/BUBBLE) |
| `propagation_stopped` | `bool` | True after `stop_propagation()` |
| `default_prevented` | `bool` | True after `prevent_default()` |

**Helper methods:**

```python
from gui_do import GuiEvent, EventPhase, EventType
import pygame

def handle(event: GuiEvent) -> bool:
    # Type checks
    event.is_quit()
    event.is_kind(EventType.KEY_DOWN, EventType.KEY_UP)

    # Key events
    event.is_key_down()
    event.is_key_down(pygame.K_ESCAPE)
    event.is_key_up(pygame.K_RETURN)
    event.is_text_event()            # TEXT_INPUT or TEXT_EDITING

    # Modifier bitmask
    if event.mod & pygame.KMOD_SHIFT: ...
    if event.mod & pygame.KMOD_CTRL:  ...

    # Mouse buttons
    event.is_mouse_down()            # any button down
    event.is_mouse_down(1)           # left button down
    event.is_mouse_up(3)             # right button up
    event.is_left_down()
    event.is_left_up()
    event.is_right_down()
    event.is_right_up()
    event.is_middle_down()
    event.is_middle_up()

    # Motion / wheel
    event.is_mouse_motion()
    event.is_mouse_wheel()
    event.wheel_delta                # int; vertical wheel delta

    # Geometry
    event.collides(rect)             # True if pos is inside rect

    # Propagation
    event.stop_propagation()         # halt dispatch to parent containers
    event.prevent_default()          # suppress default framework behavior

    # Cloning
    copy = event.clone()             # shallow copy with independent propagation state

    return True
```

<a id="event-dispatch"></a>

### Event Dispatch — [Back to Top](#table-of-contents)

Events traverse the scene graph in three phases per `scene.dispatch()`:

1. **CAPTURE** (`EventPhase.CAPTURE`): Root to target (top-down)
2. **TARGET** (`EventPhase.TARGET`): Direct target handling
3. **BUBBLE** (`EventPhase.BUBBLE`): Target to root (bottom-up)

`with_phase(phase)` returns a new `GuiEvent` copy with the given phase set. Call `stop_propagation()` on an event to halt traversal at the current node. Call `prevent_default()` to suppress the framework's default behavior for that event.

<a id="eventtype-and-eventphase"></a>

### EventType and EventPhase — [Back to Top](#table-of-contents)

`EventType` members:

| Member | Description |
|---|---|
| `QUIT` | Window close / system quit |
| `KEY_DOWN` | Key pressed |
| `KEY_UP` | Key released |
| `MOUSE_BUTTON_DOWN` | Mouse button pressed |
| `MOUSE_BUTTON_UP` | Mouse button released |
| `MOUSE_MOTION` | Pointer moved |
| `MOUSE_WHEEL` | Mouse wheel scrolled |
| `TEXT_INPUT` | Character text input |
| `TEXT_EDITING` | IME text editing |
| `WIDGET` | Internal widget event |
| `TASK` | Scheduler task notification |
| `PASS` | No-op / unrecognised raw event |

`EventPhase` members: `CAPTURE`, `TARGET`, `BUBBLE`.

<a id="actions-and-key-bindings"></a>

### Actions and Key Bindings — [Back to Top](#table-of-contents)

`ActionManager` maps key presses to named action callbacks. Accessible as `app.actions`.

```python
import pygame

# Register actions
app.actions.register_action("zoom_in", lambda event: True)
app.actions.unregister_action("zoom_in")

# Check and enumerate
if app.actions.has_action("zoom_in"):
    print("registered")
names = app.actions.registered_actions()   # sorted list

# Bind keys (scene-scoped or global)
app.actions.bind_key(pygame.K_PLUS,  "zoom_in",  scene="main")
app.actions.bind_key(pygame.K_MINUS, "zoom_out", scene="main")

# window_only=True: only fires when a window has keyboard focus
app.actions.bind_key(pygame.K_DELETE, "delete_item", scene="main", window_only=True)

# Remove a binding (returns True if removed)
app.actions.unbind_key(pygame.K_MINUS, "zoom_out", scene="main")

# Inspect bindings for an action
for binding in app.actions.bindings_for_action("zoom_in"):
    print(binding.key, binding.scene, binding.window_only)
```

---

<a id="focus-and-keyboard-input"></a>

## Focus and Keyboard Input — [Back to Top](#table-of-contents)

<a id="tab-traversal"></a>

### Tab Traversal — [Back to Top](#table-of-contents)

Set `tab_index` on controls to define the keyboard navigation order. `Tab` advances forward; `Shift+Tab` goes backward. The focus ring wraps at boundaries.

```python
button1.set_tab_index(0)
button2.set_tab_index(1)
slider.set_tab_index(2)
```

**First-Tab behavior:** the first `Tab` press establishes focus context and shows the hint ring on the current (or first) focusable node without moving focus. Subsequent presses cycle in tab-index order.

**Active-window scope:** Tab traversal is scoped to the active window. Controls inside inactive windows are excluded. If the focused control is inside a window that becomes inactive, focus is cleared automatically.

<a id="focusmanager"></a>

### FocusManager — [Back to Top](#table-of-contents)

`FocusManager` is available as `app.focus`.

```python
from gui_do import FocusManager

fm = app.focus

# Query
current_node = fm.focused_node          # currently focused UiNode, or None
current_id   = fm.focused_control_id    # control_id string, or None
has_any      = fm.has_focus             # bool

# Set focus
fm.set_focus(node, show_hint=True)
fm.set_focus_by_id(app.scene, "my_button")   # returns bool

# Clear
fm.clear_focus()

# Cycle (Tab-style); returns True when focus moved
fm.cycle_focus(app.scene, forward=True)          # forward = Tab
fm.cycle_focus(app.scene, forward=False)         # backward = Shift+Tab
fm.cycle_focus(app.scene, forward=True, window=my_window)  # scoped to window

# Count focusable nodes
count = fm.focusable_count(app.scene)
count = fm.focusable_count(app.scene, window=my_window)
```

<a id="focus-visualization"></a>

### Focus Visualization — [Back to Top](#table-of-contents)

`FocusVisualizer` renders a dashed hint ring around the focused control and fades it after a timeout. Accessible as `app.focus_visualizer`.

```python
vis = app.focus_visualizer

vis.set_focus_hint(node)                    # show hint
vis.set_focus_hint(node, show_hint=False)   # suppress hint (e.g., mouse-click focus)
vis.clear_focus_hint()

vis.refresh_focus_hint(node)   # restart timer for a node; returns True if refreshed
vis.refresh_focus_hint()       # refresh current hint node

vis.has_active_hint()          # True when hint is visible or fading
```

`ButtonControl`, `ToggleControl`, and `ButtonGroupControl` call `refresh_focus_hint` automatically on keyboard activation so the hint stays visible during the activation.

<a id="accessibility"></a>

### Accessibility — [Back to Top](#table-of-contents)

```python
widget.set_accessibility(role="button", label="Save File")
```

`configure_features_accessibility` calls the optional `configure_accessibility(host, tab_index_start) -> int` hook on all registered Features in registration order:

```python
next_idx = app.configure_features_accessibility(demo, tab_index_start=0)
```

---

<a id="features"></a>

## Features — [Back to Top](#table-of-contents)

<a id="feature-lifecycle-overview"></a>

### Feature Lifecycle Overview — [Back to Top](#table-of-contents)

A Feature is a managed object with declared lifecycle hooks. `FeatureManager` calls each hook in registration order.

**Lifecycle sequence:**

| Hook | Called by | Purpose |
|---|---|---|
| `on_register(host)` | `app.register_feature(...)` | One-time setup; scene may not be active yet |
| `build(host)` | `app.build_features(host)` | Create controls and wire static structure |
| `bind_runtime(host)` | `app.bind_features_runtime(host)` | Acquire runtime services (scheduler, bus, etc.) |
| `configure_accessibility(host, idx) -> int` | `app.configure_features_accessibility(host, idx)` | Assign tab indices; return next available index |
| `prewarm(host, surface, theme)` | `app.prewarm_scene(...)` | One-time first-open warm-up (font loads, bitmaps) |
| `handle_event(host, event) -> bool` | `app.process_event(...)` | Intercept events before scene dispatch |
| `on_update(host)` | `app.update(...)` | Per-frame logic; drain message queue |
| `draw(host, surface, theme)` | `app.draw()` | Render into owned controls |
| `shutdown_runtime(host)` | `app.shutdown()` | Release resources |
| `on_unregister(host)` | `app.unregister_feature(...)` | Final cleanup after shutdown_runtime |

Declare host field requirements in `HOST_REQUIREMENTS`:

```python
class MyFeature(Feature):
    HOST_REQUIREMENTS = {
        "build":        ("app", "root"),
        "bind_runtime": ("app",),
    }
```

<a id="feature--general-purpose"></a>

### Feature — General-Purpose — [Back to Top](#table-of-contents)

The base class for Features that own controls on a scene.

```python
from gui_do import Feature

class StatusFeature(Feature):
    HOST_REQUIREMENTS = {
        "build":        ("app", "root"),
        "bind_runtime": ("app",),
    }

    def __init__(self):
        super().__init__("status_feature", scene_name="main")
        self.label = None

    def on_register(self, host) -> None:
        pass   # called immediately on registration

    def build(self, host) -> None:
        self.label = host.root.add(LabelControl("status", Rect(8, 8, 200, 24), "Ready"))

    def bind_runtime(self, host) -> None:
        self.scheduler = host.app.get_scene_scheduler("main")

    def on_update(self, host) -> None:
        pass   # called each frame

    def on_unregister(self, host) -> None:
        pass   # called on removal


# Bootstrap
app.register_feature(StatusFeature(), host=demo)
app.build_features(demo)
app.bind_features_runtime(demo)
```

<a id="directfeature--screen-drawing"></a>

### DirectFeature — Screen Drawing — [Back to Top](#table-of-contents)

`DirectFeature` adds three hooks that run via the screen lifecycle layer rather than the widget pipeline, bypassing hit-testing, invalidation tracking, and compositor layering:

| Hook | Description |
|---|---|
| `handle_direct_event(host, event) -> bool` | Receives events before controls |
| `on_direct_update(host, dt_seconds)` | Per-frame with elapsed time |
| `draw_direct(host, surface, theme)` | Blits directly onto the restored pristine surface |

Use `DirectFeature` for fullscreen animations, large animated backdrops, or anything that blits many surfaces every frame and must avoid per-frame widget pipeline overhead.

```python
from gui_do import DirectFeature

class BackdropFeature(DirectFeature):
    HOST_REQUIREMENTS = {"bind_runtime": ("app", "screen_rect")}

    def __init__(self):
        super().__init__("backdrop", scene_name=None)   # scene_name=None = shared

    def bind_runtime(self, host) -> None:
        self._screen_rect = host.screen_rect

    def on_direct_update(self, host, dt_seconds: float) -> None:
        pass   # advance animation state

    def draw_direct(self, host, surface, theme) -> None:
        pass   # blit pre-rendered sprites onto surface
```

<a id="logicfeature--domain-logic-service"></a>

### LogicFeature — Domain Logic Service — [Back to Top](#table-of-contents)

`LogicFeature` is for headless domain logic that responds to command messages and sends back result messages. It extends `Feature` with `on_logic_command(host, message)`, called automatically for each message whose `command` field is set.

```python
from gui_do import FeatureMessage, LogicFeature

TOPIC = "counter"

class CounterLogicFeature(LogicFeature):
    def __init__(self):
        super().__init__("counter_logic", scene_name="main")
        self.value = 0

    def on_logic_command(self, host, message: FeatureMessage) -> None:
        if message.command == "inc":
            self.value += 1
        elif message.command == "reset":
            self.value = 0
        else:
            return
        self.send_message(message.sender, {"topic": TOPIC, "event": "state", "value": self.value})
```

<a id="routedfeature--topic-routed-dispatch"></a>

### RoutedFeature — Topic-Routed Dispatch — [Back to Top](#table-of-contents)

`RoutedFeature` extends `Feature` with topic-based message dispatch. Override `message_handlers()` to return a `{topic: handler}` dict. `on_update` drains the queue and calls the appropriate handler automatically.

```python
from gui_do import RoutedFeature, FeatureMessage

TOPIC = "counter"

class CounterFeature(RoutedFeature):
    LOGIC_ALIAS = "counter"

    def __init__(self):
        super().__init__("counter", scene_name="main")
        self.value = 0

    def on_register(self, host) -> None:
        self._feature_manager.register(CounterLogicFeature(), host)

    def bind_runtime(self, host) -> None:
        if self.bound_logic_name(alias=self.LOGIC_ALIAS) is None:
            self.bind_logic("counter_logic", alias=self.LOGIC_ALIAS)
        self.send_logic_message({"topic": TOPIC, "command": "reset"}, alias=self.LOGIC_ALIAS)

    def message_handlers(self):
        return {TOPIC: self._on_counter_message}

    def _on_counter_message(self, host, message: FeatureMessage) -> None:
        if message.event == "state":
            self.value = int(message.get("value", 0))

    def increment(self) -> None:
        self.send_logic_message({"topic": TOPIC, "command": "inc"}, alias=self.LOGIC_ALIAS)


# Only register the owning Feature; it self-registers its logic in on_register
app.register_feature(CounterFeature(), host=demo)
app.build_features(demo)
app.bind_features_runtime(demo)
```

`MESSAGE_TOPIC_KEY` (default `"topic"`) can be overridden if the sending party uses a different field name.

<a id="choosing-a-feature-type"></a>

### Choosing a Feature Type — [Back to Top](#table-of-contents)

| Scenario | Use |
|---|---|
| Owns windows, buttons, or other controls on the scene | `Feature` |
| Routes incoming messages to handlers by topic | `RoutedFeature` |
| Encapsulates reusable domain logic behind command messages | `LogicFeature` |
| Shared as a logic service by multiple Features | `LogicFeature` |
| Draws a fullscreen animation or large background every frame | `DirectFeature` |
| Needs raw per-frame `dt_seconds` for physics or animation | `DirectFeature` |
| Requires bypassing the widget pipeline for performance | `DirectFeature` |

<a id="featuremanager"></a>

### FeatureManager — [Back to Top](#table-of-contents)

`FeatureManager` is exported primarily for type annotation. In application code, use the `GuiApplication` helpers. Feature subclasses may access the manager via `self._feature_manager`:

| Method | Description |
|---|---|
| `register(feature, host)` | Register and call `on_register` |
| `unregister(name, host)` | Unregister; calls `on_unregister` + `shutdown_runtime` |
| `get(name)` | Return Feature by name, or None |
| `names()` | Tuple of names in registration order |
| `send_message(sender, target, payload)` | Enqueue a message |
| `bind_logic(consumer, provider, alias)` | Bind a LogicFeature alias |
| `unbind_logic(consumer, alias)` | Remove alias; returns bool |
| `bound_logic_name(consumer, alias)` | Provider name, or None |
| `send_logic_message(consumer, payload, alias)` | Route command to bound logic |

Use the `Feature` convenience methods (`self.send_message(...)`, `self.bind_logic(...)`, etc.) rather than calling the manager directly.

<a id="feature-messaging"></a>

### Feature Messaging — [Back to Top](#table-of-contents)

Features communicate by sending `dict` payloads to named targets. The receiving Feature drains its queue in `on_update`.

```python
from gui_do import Feature, FeatureMessage

class ProducerFeature(Feature):
    def on_update(self, host) -> None:
        self.send_message("consumer", {"topic": "data_update", "value": 42})


class ConsumerFeature(Feature):
    def on_update(self, host) -> None:
        while self.has_messages():
            msg = self.pop_message()
            if msg.topic == "data_update":
                print(msg["value"])

        # Other queue helpers:
        # self.peek_message()    -> next message without removing
        # self.message_count()   -> int queue length
        # self.clear_messages()  -> discard all
```

`FeatureMessage` fields: `sender` (str), `target` (str), `payload` (dict). Access payload keys via `message["key"]` or `message.get("key", default)`. Convenience properties: `message.topic`, `message.command`, `message.event`.

<a id="feature-font-roles"></a>

### Feature Font Roles — [Back to Top](#table-of-contents)

Features can register their own namespaced font roles (stored as `feature.<name>.<role>`) that do not collide with application roles.

```python
from gui_do import Feature

class MyFeature(Feature):
    def build(self, host) -> None:
        self.register_font_role(
            host, "heading",
            size=20, file_path="assets/fonts/Ubuntu-B.ttf",
            system_name="arial", bold=True, scene_name="main",
        )

        self.register_font_roles(
            host,
            {
                "body":    {"size": 14, "system_name": "arial"},
                "caption": {"size": 11, "system_name": "arial", "italic": True},
            },
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        heading_role = self.font_role("heading")   # "feature.my_feature.heading"
        app.style_label(self.title_label, size=20, role=heading_role)
```

<a id="logicfeature-runnables"></a>

### LogicFeature Runnables — [Back to Top](#table-of-contents)

Expose compute-heavy worker entrypoints as named runnables from a `LogicFeature` and invoke them via scheduler tasks.

```python
from gui_do import LogicFeature

class WorkLogicFeature(LogicFeature):
    def bind_runtime(self, host) -> None:
        host.app.register_feature_runnable(self.name, "compute", self.run_compute)

    def run_compute(self, scheduler, task_id, params):
        result = heavy_computation(params)
        scheduler.send_message(task_id, {"result": result})
```

```python
# From a consumer Feature or host:
host.app.run_feature_runnable("work_logic", "compute", scheduler, task_id, params)
```

<a id="screen-lifecycle-composition"></a>

### Screen Lifecycle Composition — [Back to Top](#table-of-contents)

Screen lifecycle callbacks run at the scene level, outside the widget tree. Use them for scene-level preambles, global event interception, and postambles.

```python
# Set the base lifecycle (replaces any existing base; clears all layers)
app.set_screen_lifecycle(
    preamble=on_scene_start,
    event_handler=on_screen_event,
    postamble=on_scene_end,
    scene_name="main",
)

# Add a composable layer; returns a disposer callable
dispose_layer = app.chain_screen_lifecycle(
    preamble=feature_preamble,
    event_handler=feature_event_handler,
    postamble=feature_postamble,
    scene_name="main",
)

# Remove this layer
dispose_layer()
```

`event_handler` receives a `GuiEvent` and should return `True` to consume it. Multiple handlers are called in registration order; the first `True` return short-circuits the rest.

<a id="scene-prewarm-and-first-open-profiling"></a>

### Scene Prewarm and First-Open Profiling — [Back to Top](#table-of-contents)

`prewarm_scene` runs each Feature's `prewarm(host, surface, theme)` hook once per `(Feature, scene)` pair to front-load font loads, bitmap generation, and text rasterization before the first user-visible frame.

```python
app.build_features(demo)
app.bind_features_runtime(demo)

# Prewarm before switching to the scene for the first time
app.prewarm_scene("main")
app.prewarm_scene("control_showcase")

# Force re-run even if already warmed (e.g., after a style change)
app.prewarm_scene("main", force=True)
```

When `host` is omitted, each Feature's registered host context is used, allowing one call to prewarm all scene Features safely.

**First-open profiling** measures one-time expensive operations (font loads, bitmap generation) and logs `[gui_do][first-open]` entries:

```python
app.configure_first_frame_profiling(enabled=True, min_ms=0.25)
# or with a custom logger
app.configure_first_frame_profiling(enabled=True, logger=lambda msg: print(msg))
```

Environment shortcut (no code change needed):

```bash
set GUI_DO_PROFILE_FIRST_OPEN=1
```

---

<a id="background-services"></a>

## Background Services — [Back to Top](#table-of-contents)

<a id="taskscheduler"></a>

### TaskScheduler — [Back to Top](#table-of-contents)

`TaskScheduler` runs tasks in a thread pool and delivers results and progress payloads to the main thread during `update()`. Each scene has its own scheduler; access the active scene's via `app.scheduler`.

```python
from gui_do import TaskScheduler, TaskEvent

scheduler = app.scheduler

# Add a task
def logic(task_id, params):
    for i in range(params["count"]):
        scheduler.send_message(task_id, {"step": i})
    return {"ok": True}

def on_progress(payload):
    print("step", payload["step"])

scheduler.add_task("demo", logic, parameters={"count": 8}, message_method=on_progress)

# In your update loop
scheduler.update()
for event in scheduler.get_finished_events():
    print("done", event.task_id)
for event in scheduler.get_failed_events():
    print("failed", event.task_id, event.error)
scheduler.clear_events()

# Task lifecycle
scheduler.remove_tasks("demo")         # cancel by id
scheduler.remove_all()                 # cancel all

# Suspend / resume individual tasks
scheduler.suspend_tasks("task_a", "task_b")
scheduler.resume_tasks("task_a")
scheduler.suspend_all()
ids   = scheduler.read_suspended()     # list of suspended task ids
count = scheduler.read_suspended_len()

# Pause / resume the executor
scheduler.set_execution_paused(True)
scheduler.is_execution_paused()
scheduler.set_execution_paused(False)

# Delivery throttle
scheduler.set_message_dispatch_limit(50)          # max messages per update()
scheduler.set_message_dispatch_time_budget_ms(4)  # stop after 4 ms
scheduler.set_message_dispatch_limit(None)        # no limit

# Worker count
workers   = TaskScheduler.recommended_worker_count()
scheduler = TaskScheduler(max_workers=workers)

# Access a non-active scene's scheduler
sched = app.get_scene_scheduler("settings")
```

<a id="timers"></a>

### Timers — [Back to Top](#table-of-contents)

`Timers` schedules one-shot and repeating callbacks per scene. Accessible as `app.timers`.

```python
timers = app.timers

# One-shot: fires once after delay, then removes itself
timers.add_once("my_timer", delay_seconds=1.0, callback=lambda: print("1 s elapsed"))

# Repeating
timers.add_timer("heartbeat", interval_seconds=0.5, callback=lambda: print("tick"))

# Reschedule an existing timer
timers.reschedule("heartbeat", new_interval_seconds=0.25)

# Cancel
if timers.has_timer("my_timer"):
    timers.remove_timer("my_timer")

# Introspect
ids = timers.timer_ids()
cancelled = timers.cancel_all()   # returns count removed
```

<a id="eventbus"></a>

### EventBus — [Back to Top](#table-of-contents)

`EventBus` provides scoped publish-subscribe delivery for non-input application events. Accessible as `app.events`.

```python
from gui_do import EventBus

bus = app.events

# Subscribe; returns a Subscription object
sub  = bus.subscribe("status_changed", lambda payload: print(payload))
sub2 = bus.subscribe("data_ready", handler, scope="main_scene")

# Publish
bus.publish("status_changed", {"message": "Ready"})
# With scope: delivers to unscoped AND scope-matched subscribers
bus.publish("data_ready", result, scope="main_scene")

# Unsubscribe one
bus.unsubscribe(sub)

# Unsubscribe all with a scope tag; returns count removed
removed = bus.unsubscribe_scope("main_scene")

# Subscribe for exactly one delivery
bus.once("startup_done", lambda _: print("done"))

# Introspect
total     = bus.subscriber_count()
for_topic = bus.subscriber_count("status_changed")
```

---

<a id="observable-values-and-data-binding"></a>

## Observable Values and Data Binding — [Back to Top](#table-of-contents)

`ObservableValue` holds a single value and notifies subscribers whenever it changes. `PresentationModel` groups related values and tracks subscriptions for bulk disposal.

```python
from gui_do import ObservableValue, PresentationModel

count = ObservableValue(0)

# Subscribe; returns an unsubscribe callable
unsub = count.subscribe(lambda new_val: print(f"Count: {new_val}"))

count.value = 5        # triggers all subscribers
count.set_silently(10) # update without notifying
count.force_notify()   # notify all with current value even if unchanged
n = count.observer_count

unsub()   # unsubscribe


class SceneViewModel(PresentationModel):
    def __init__(self):
        super().__init__()
        self.zoom       = ObservableValue(1.0)
        self.is_playing = ObservableValue(False)

vm = SceneViewModel()
vm.bind(vm.zoom,       lambda z: print(f"Zoom: {z}"))
vm.bind(vm.is_playing, lambda p: print(f"Playing: {p}"))

vm.zoom.value       = 2.0
vm.is_playing.value = True

vm.dispose()   # unregister all managed subscriptions
```

---

<a id="themes-styling-and-fonts"></a>

## Themes, Styling, and Fonts — [Back to Top](#table-of-contents)

<a id="colortheme"></a>

### ColorTheme — [Back to Top](#table-of-contents)

Each scene has a `ColorTheme` with a built-in palette. Access the active scene's theme as `app.theme`.

```python
theme = app.theme

bg     = theme.background   # scene fill color
text   = theme.text         # primary text color
light  = theme.light        # lightest widget surface
medium = theme.medium       # mid-tone (disabled states)
dark   = theme.dark         # darkest border/shadow accent
high   = theme.highlight    # selection / focus accent
shadow = theme.shadow       # text drop-shadow color
```

Register font roles per-scene:

```python
app.register_font_role(
    role_name="body",
    size=14,
    file_path="assets/fonts/Ubuntu-B.ttf",   # CWD-relative or absolute
    system_name="arial",                      # pygame system font fallback
    bold=False,
    italic=False,
    scene_name="main",                        # omit = active scene
)

# Query registered roles for a scene
roles = app.font_roles()                  # active scene
roles = app.font_roles(scene_name="main")
```

Apply a font role to a label:

```python
app.style_label(label, size=14, role="body")

# For other controls, set the font_role attribute directly:
button.font_role = "body"
toggle.font_role = "body"
```

<a id="fontmanager"></a>

### FontManager — [Back to Top](#table-of-contents)

`FontManager` manages named font roles and caches loaded `pygame.font.Font` objects. Access the active scene's instance via `app.theme.fonts`.

Three roles are pre-registered for every scene:

| Role | Default size |
|---|---|
| `"body"` | 16 |
| `"title"` | 14 |
| `"display"` | 72 |

```python
from gui_do import FontManager

fonts = app.theme.fonts

fonts.register_role("heading", size=24, file_path="assets/Ubuntu-B.ttf",
                    system_name="arial", bold=True, italic=False)

font    = fonts.get_font("heading")          # pygame.font.Font at the role's size
font_32 = fonts.get_font("heading", size=32) # at an overridden size
names   = fonts.role_names()                 # tuple of registered role names
exists  = fonts.has_role("heading")
rev     = fonts.revision                     # int; increments when any role changes
```

**FontInstance — text measurement:**

```python
fi = fonts.font_instance("heading")           # at the role's registered size
fi = fonts.font_instance("heading", size=48)  # at an explicit size

fi.point_size    # int; effective point size
fi.line_height   # int; pygame font.get_height()

w, h = fi.text_size("Hello")                              # width and height in pixels
w, h = fi.text_surface_size("Hello", shadow=True)         # including shadow padding
w, h = fi.text_surface_size("Hello", shadow=True, shadow_offset=(2, 2))
```

Example — size a label to exactly fit its text:

```python
label = root.add(LabelControl("title", Rect(24, 24, 1, 1), "gui_do"))
app.style_label(label, size=64, role="display")
fi = app.theme.fonts.font_instance(label.font_role, size=label.font_size)
label.rect.size = fi.text_surface_size(label.text, shadow=True)
```

<a id="builtingraphicsfactory"></a>

### BuiltInGraphicsFactory — [Back to Top](#table-of-contents)

`BuiltInGraphicsFactory` renders the visual bitmaps used by every built-in control. Each scene has one attached to its theme. Access it as `app.theme.graphics_factory` or `app.graphics_factory`.

```python
from gui_do import BuiltInGraphicsFactory

factory = app.theme.graphics_factory
surface = factory.render_text("Hello", role_name="body")   # themed text surface
rev     = factory.font_revision()                          # int; increments when fonts change
```

Access a non-active scene's factory:

```python
factory = app.get_scene_graphics_factory("settings")
```

---

<a id="telemetry"></a>

## Telemetry — [Back to Top](#table-of-contents)

gui_do includes a built-in telemetry system for GUI loop timing, scheduler throughput, Feature lifecycle, and messaging hotspots. Capture is disabled by default.

```python
from gui_do import (
    configure_telemetry, telemetry_collector,
    TelemetryCollector, TelemetrySample,
    analyze_telemetry_records, analyze_telemetry_log_file,
    load_telemetry_log_file, render_telemetry_report,
)

# Configure (all parameters optional)
app.configure_telemetry(
    enabled=True,
    live_analysis_enabled=True,
    file_logging_enabled=False,
    min_duration_ms=0.0,
    log_directory=None,   # defaults to project root
)

# Narrow focus to one system or point
app.set_telemetry_system_enabled("event_bus", False)
app.set_telemetry_point_enabled("task_scheduler", "message_callback", True)

# Run your app normally, then analyze
app.run(target_fps=60)

summary = app.telemetry_summary(top_n=10)
for hotspot in summary.hotspots[:3]:
    print(hotspot.key, hotspot.total_ms, hotspot.p95_ms)

# Write a text report and return the file path
report_path = app.write_telemetry_report(top_n=12)

# Analyze an offline log
analysis = analyze_telemetry_log_file("gui_do_telemetry_20260427_171200_samples.jsonl", top_n=20)
print(render_telemetry_report(analysis, source="offline-log"))
```

**Automatic file naming:**
- Sample logs (JSONL): `gui_do_telemetry_YYYYMMDD_HHMMSS_samples.jsonl`
- Analyzer reports (text): `gui_do_telemetry_YYYYMMDD_HHMMSS_report.txt`

**Shutdown behavior:** if telemetry and live analysis are both enabled and samples exist, `app.shutdown()` writes a hotspot report automatically.

---

<a id="advanced-patterns"></a>

## Advanced Patterns — [Back to Top](#table-of-contents)

<a id="pointer-and-input-lock"></a>

### Pointer and Input Lock — [Back to Top](#table-of-contents)

Two lock modes support pointer-intensive interactions (canvas dragging, first-person input).

**Area lock** — clamp the pointer inside a rectangle:

```python
app.set_lock_area(some_rect)   # confine pointer; clamped in process_event
app.set_lock_area(None)        # release
```

**Point lock** — stationary logical cursor with relative motion deltas:

```python
# Engage; pointer renders at lock_point_pos; motion reported as deltas
app.set_lock_point(locking_object, point=(cx, cy))   # point defaults to screen center

# Read motion delta from a motion event while locked
delta = app.get_lock_point_motion_delta(event)   # (dx, dy) or None

# Release; hardware cursor warps back to lock_point_pos
app.set_lock_point(None)

# Query
if app.mouse_point_locked:
    cx, cy = app.lock_point_pos

# Read the lock-adjusted logical pointer position
x, y = app.logical_pointer_pos
```

**Logical position management:**

```python
# Set logical pointer position with optional constraint enforcement
app.set_logical_pointer_position((x, y), apply_constraints=True)

# Align logical state and hardware cursor (use after drag release)
app.sync_pointer_to_logical_position((x, y))
```

<a id="invalidationtracker"></a>

### InvalidationTracker — [Back to Top](#table-of-contents)

`InvalidationTracker` tracks whether a full redraw is needed. The renderer manages it internally; force a full redraw from application code when you change something the renderer cannot detect automatically.

```python
app.invalidation.invalidate_all()    # force full redraw on next frame
```

<a id="pristine-backgrounds"></a>

### Pristine Backgrounds — [Back to Top](#table-of-contents)

Each scene has an optional background image that is restored (blitted) before each frame's draw pass.

```python
# Set pristine from a path, an existing Surface, or None to clear
app.set_pristine("assets/backdrop.jpg", scene_name="main")
app.set_pristine(my_surface, scene_name="main")
app.set_pristine(None, scene_name="main")

# Blit the active scene's pristine to the display surface
app.restore_pristine()

# Blit to a specific surface (e.g., an offscreen buffer)
app.restore_pristine(scene_name="main", surface=my_surface)
```

`WindowControl` also has its own per-window pristine for window-scoped background restoration:

```python
window.set_pristine(my_surface)
window.restore_pristine(surface)
```

<a id="eventmanager"></a>

### EventManager — [Back to Top](#table-of-contents)

`EventManager` converts raw pygame events to canonical `GuiEvent` objects. `app.process_event` calls it automatically. Use it directly when you need a standalone conversion outside the main loop.

```python
from gui_do import EventManager, GuiEvent

manager = EventManager()
event: GuiEvent = manager.to_gui_event(raw_pygame_event)
event = manager.to_gui_event(raw_event, pointer_pos=(x, y))
```

<a id="guiapplication-helpers-reference"></a>

### GuiApplication Helpers Reference — [Back to Top](#table-of-contents)

Quick-reference for helpers not covered in dedicated sections above:

```python
# Node search in the active (or named) scene
node  = app.find("my_button")
node  = app.find("my_button", scene_name="settings")
nodes = app.find_all(lambda n: n.visible and isinstance(n, ButtonControl))

# Focus by control_id; returns True when found and focused
focused = app.focus_on("my_button")
focused = app.focus_on("my_button", scene_name="settings")

# Feature logic bindings (convenience wrappers for FeatureManager)
app.bind_feature_logic("consumer", "logic_feature")
app.unbind_feature_logic("consumer", alias="default")   # returns bool
name = app.get_feature_logic("consumer", alias="default")
app.send_feature_logic_message("consumer", {"command": "reset"})

# Feature UI type registry — portable constructor access for Feature build routines
ui = app.read_feature_ui_types()
win    = host.root.add(ui.window_control_cls("win", rect, "Title"))
label  = win.add(ui.label_control_cls("status", inner_rect, "Ready"))
toggle = win.add(ui.toggle_control_cls("flag", inner_rect, "On", "Off"))
# Available: window_control_cls, label_control_cls, button_control_cls,
#            canvas_control_cls, slider_control_cls, toggle_control_cls,
#            layout_axis_cls, button_group_control_cls, arrow_box_control_cls,
#            frame_control_cls, image_control_cls, scrollbar_control_cls,
#            panel_control_cls

# Direct screen features (called by the renderer each frame)
app.draw_screen_features(app.surface, app.theme)
```
