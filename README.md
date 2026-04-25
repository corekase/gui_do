[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

# gui_do

Architecture-first pygame GUI framework focused on strict contracts, scene isolation, and composable feature parts.

## Quick Start

### Installation

```bash
pip install pygame numpy
```

### Run the Demo

```bash
python gui_do_demo.py
```

The demo ships with two scenes:

- `main`: Life + Mandelbrot windows, animated backdrop, task panel (`Exit`, `Showcase`, `Life`, `Mandelbrot`)
- `control_showcase`: dedicated showcase scene with its own backdrop and an `Apps` task-panel button

## Minimal Runnable Example

```python
import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, LabelControl, ButtonControl

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
button.set_accessibility(role="button", label="Quit app")
button.set_tab_index(0)

app.actions.register_action("exit", lambda _event: (app.quit() or True))
app.actions.bind_key(pygame.K_ESCAPE, "exit", scene="main")

app.run(target_fps=60)
pygame.quit()
```

## Core Runtime Concepts

### Scene Model

Each scene owns its own:

- `Scene` graph
- `TaskScheduler`
- `Timers`
- `ColorTheme` + graphics factory
- pristine/backdrop cache

Switching scenes swaps these runtime services through `GuiApplication.switch_scene(...)`.

### Window Tiling Registration

`GuiApplication.build_parts(host)` now primes per-scene window tiling registration order internally.

This means app/demo startup does not need manual pre-registration choreography such as:

- calling `tile_windows()` before first visibility toggles
- switching scenes solely to pre-register tiling order

Registration order is still deterministic by scene graph creation order, and remains stable across hide/show visibility toggles.

### Part Lifecycle

A feature is a `Part` with optional hooks:

- `build(host)`
- `bind_runtime(host)`
- `prewarm(host, surface, theme)`
- `configure_accessibility(host, tab_index_start) -> int`
- `handle_event(host, event) -> bool`
- `on_update(host)`
- `draw(host, surface, theme)`
- `shutdown_runtime(host)`

Host field requirements can be declared per hook using `HOST_REQUIREMENTS` and are validated before invocation.

### Scene Prewarm (One Call Per Scene)

`GuiApplication.prewarm_scene(scene_name)` performs a one-time prewarm pass for all parts active in that scene:

- parts with `part.scene_name == scene_name`
- parts with `part.scene_name is None` (shared/global)

It invokes each part's `prewarm(host, surface, theme)` exactly once per `(part, scene)` unless `force=True` is passed.

```python
# Typical bootstrap ordering
app.build_parts(demo)
app.bind_parts_runtime(demo)

# One prewarm call per scene before first user-visible frame/open
app.prewarm_scene("control_showcase")

# Optional: replay prewarm for the scene if assets/styles changed
app.prewarm_scene("control_showcase", force=True)
```

Host behavior: if `host` is omitted, prewarm uses each part's registered host context (same as runtime hooks). This lets one scene-level call prewarm all scene parts safely, including parts that require richer host state than `GuiApplication` alone.

### First-Open Optimisation Workflow (Instrument -> Confirm -> Prewarm)

Use this sequence to remove first-open stutter caused by one-time lazy work (font loads, text rasterization, control visual generation, and first-draw setup):

1. Enable profiling.
2. Open the target scene/window once and inspect `[gui_do][first-open]` logs.
3. Add one `prewarm_scene(...)` call during startup for that scene.
4. Re-run and confirm first-open hotspots are reduced/shifted to startup.

```python
# 1) Enable first-open profiling
app.configure_first_frame_profiling(enabled=True, min_ms=0.25)

# 2) Build/bind parts as normal
app.build_parts(demo)
app.bind_parts_runtime(demo)

# 3) Prewarm one scene once (recommended per scene)
app.prewarm_scene("control_showcase")

# Optional: re-run prewarm if style/assets changed dynamically
# app.prewarm_scene("control_showcase", force=True)
```

Environment-only toggle (no code change):

```bash
set GUI_DO_PROFILE_FIRST_OPEN=1
python gui_do_demo.py
```

### Runtime Telemetry and Performance Analyzer

`gui_do` now includes a built-in telemetry system for GUI loop timing, scheduler throughput, part lifecycle execution, and part/event messaging hotspots.

Default behavior:

- telemetry capture is disabled
- live analyzer is disabled
- file logging is disabled

Telemetry API (`from gui import ...`):

- `configure_telemetry(...)`
- `telemetry_collector()`
- `TelemetryCollector`, `TelemetrySample`
- `analyze_telemetry_records(...)`
- `analyze_telemetry_log_file(...)`
- `load_telemetry_log_file(...)`
- `render_telemetry_report(...)`

`GuiApplication` convenience helpers:

- `app.configure_telemetry(...)`
- `app.set_telemetry_system_enabled(system, enabled)`
- `app.set_telemetry_point_enabled(system, point, enabled)`
- `app.telemetry_summary(top_n=...)`
- `app.write_telemetry_report(top_n=..., output_path=...)`

#### Quick Telemetry Tutorial

```python
from gui import GuiApplication

app = GuiApplication(screen)

# 1) Turn telemetry on (still in-memory only)
app.configure_telemetry(
    enabled=True,
    live_analysis_enabled=True,
    file_logging_enabled=False,
    min_duration_ms=0.0,
)

# 2) Narrow focus to one subsystem if needed
app.set_telemetry_system_enabled("event_bus", False)
app.set_telemetry_point_enabled("task_scheduler", "message_callback", True)

# 3) Run your normal scenes and part interactions
app.run(target_fps=60)

# 4) Analyze live-captured samples
summary = app.telemetry_summary(top_n=10)
for hotspot in summary.hotspots[:3]:
    print(hotspot.key, hotspot.total_ms, hotspot.p95_ms)

# 5) Optional explicit report write (text)
report_path = app.write_telemetry_report(top_n=12)
print("report:", report_path)
```

Automatic file naming convention:

- sample logs (JSONL): `gui_do_telemetry_YYYYMMDD_HHMMSS_samples.jsonl`
- analyzer report (text): `gui_do_telemetry_YYYYMMDD_HHMMSS_report.txt`

Files are generated in the project root by default. You can set a custom folder through `configure_telemetry(log_directory=...)`.

Live analyzer shutdown behavior:

- if telemetry + live analysis are enabled and samples exist, `GuiApplication.shutdown()` writes a high-level hotspot report automatically
- if live analysis is disabled, no shutdown report is emitted unless requested via `write_telemetry_report(...)`

Analyzer workflow for offline logs:

```python
from gui import analyze_telemetry_log_file
from gui import render_telemetry_report

analysis = analyze_telemetry_log_file("gui_do_telemetry_20260425_171200_samples.jsonl", top_n=20)
print(render_telemetry_report(analysis, source="offline-log"))
```

### Part Types: `Part`, `RoutedMessagePart`, `LogicPart`, and `ScreenPart`

There are four part base classes in `shared.part_lifecycle`. Choosing between them depends on what the feature owns and how it runs.

#### Part Lifecycle Hooks: `on_register` and `on_unregister`

Two additional hooks are called by `PartManager` outside the main lifecycle sequence:

- `on_register(host)` — called immediately when the part is registered via `app.register_part(...)`. Use it for one-time setup that does not depend on the scene being active.
- `on_unregister(host)` — called when the part is removed via `app.unregister_part(...)`, after `shutdown_runtime`. Use it for final cleanup.

```python
from shared.part_lifecycle import Part

class MyFeature(Part):
    def on_register(self, host) -> None:
        # Called once when registered; scene may not be active yet.
        pass

    def on_unregister(self, host) -> None:
        # Called on removal, after shutdown_runtime.
        pass
```

#### `Part` — General-purpose feature unit

`Part` is the standard base for features that build and manage controls (windows, buttons, canvases, sliders, etc.) on a scene. Its lifecycle hooks integrate directly with `GuiApplication` scene management: `build` creates controls, `bind_runtime` wires services, `on_update` runs frame logic, and `draw` renders into its own controls rather than directly onto the screen surface.

Use `Part` for features that:
- own a window or other UI structure on the scene
- coordinate preamble, event routing, and postamble for those controls
- communicate through the scheduler, event bus, or part messaging

The demo's `LifeSimulationFeature` and `MandelbrotRenderFeature` both extend `RoutedMessagePart`. Each owns a `WindowControl` containing `CanvasControl` and control widgets. Their screen-drawing responsibilities are delegated to those controls — the part itself is responsible for wiring and orchestration, not raw pixel output.

```python
from shared.part_lifecycle import RoutedMessagePart

class LifeSimulationFeature(RoutedMessagePart):
    HOST_REQUIREMENTS = {
        "build": ("app", "root"),
        "bind_runtime": ("app",),
    }

    def __init__(self):
        super().__init__("life_simulation", scene_name="main")
        self.scheduler = None
        self.window = None
        self.canvas = None

    def build(self, demo) -> None:
        # Creates a WindowControl with canvas + buttons under demo.root.
        # The Part orchestrates layout and events; the controls handle drawing.
        ...

    def bind_runtime(self, demo) -> None:
        self.scheduler = demo.app.get_scene_scheduler("main")
```

```python
class MandelbrotRenderFeature(RoutedMessagePart):
    HOST_REQUIREMENTS = {
        "build": ("app", "root"),
        "bind_runtime": ("app",),
    }

    def __init__(self):
        super().__init__("mandelbrot_render", scene_name="main")
        # Owns render-mode toggles, status label, scheduler tasks, and
        # a canvas window — all standard controls; no raw screen blitting.
        ...
```

#### `LogicPart` — Domain logic service behind message commands

`LogicPart` is for domain-specific logic that should be reused by one or many UI-facing parts without exposing internal state directly. Consumers send command messages (for example `{"command": "next"}`) and the logic part responds with result/state messages.

This keeps the lifecycle strict and generic: the framework provides only routing and bindings, while each logic part defines its own command/data protocol.

API helpers:

- `Part.bind_logic_part(logic_part_name, alias="default")`
- `Part.send_logic_message(message, alias="default")`
- `GuiApplication.bind_part_logic(...)`
- `GuiApplication.send_part_logic_message(...)`

Private and shared logic are both supported:

- private: bind one consumer to a dedicated logic part
- shared: bind multiple consumers to the same logic part under their own aliases

`LifeSimulationFeature` uses this pattern with `LifeSimulationLogicPart`: UI interactions send commands (`reset`, `toggle_cell`, `next`) and the logic part sends back the updated `life_cells` snapshot.

`MandelbrotRenderFeature` also uses this pattern: scheduler worker algorithms are delegated to `MandelbrotLogicPart` providers (one primary logic part plus split-canvas logic parts), while the render part owns control flow and payload-to-canvas drawing.

#### `RoutedMessagePart` — Topic-routed message dispatch

`RoutedMessagePart` is a `Part` subclass that routes incoming messages by a canonical **topic key** instead of requiring manual `pop_message()` loop inspection. It adds a single override point — `message_handlers()` — which returns a dictionary mapping topic strings to handler callables. `on_update` drains the queue and dispatches each message automatically.

```python
from shared.part_lifecycle import RoutedMessagePart

class StatusConsumerPart(RoutedMessagePart):
    # Override MESSAGE_TOPIC_KEY if the sending party uses a different field name.
    MESSAGE_TOPIC_KEY = "topic"  # default

    def message_handlers(self):
        return {
            "data_update": self._on_data_update,
            "reset":       self._on_reset,
        }

    def _on_data_update(self, host, sender_name: str, payload: dict) -> None:
        print(f"Data from {sender_name}: {payload['value']}")

    def _on_reset(self, host, sender_name: str, payload: dict) -> None:
        print("Reset requested")
```

`on_update` calls `on_message()` for each queued message. Unknown topics are silently ignored by default; override `on_message()` to handle them differently.

#### `ScreenPart` — Direct screen drawing with frame synchronisation

`ScreenPart` is a `Part` subclass that adds three additional lifecycle hooks called by the scene's *screen lifecycle layer* rather than by the normal control tree:

- `handle_screen_event(host, event) -> bool` — receives raw events before controls
- `on_screen_update(host, dt_seconds)` — called once per frame with elapsed time
- `draw_screen(host, surface, theme)` — blits directly onto the full-screen surface

This matters for performance. A standard `Part` drawing onto the screen via `draw(...)` enters the full GUI widget rendering pipeline: hit testing, invalidation tracking, and compositor layering all run even when only a background animation needs to repaint. For an animated backdrop with dozens of sprites updated every frame, that overhead is measurable.

`ScreenPart` bypasses the widget pipeline entirely for its drawing path. `draw_screen` receives the already-restored pristine surface and blits cached sprites directly, keeping the path as thin as a raw pygame `surface.blit` call. The pre-cached sprite approach (surfaces created once at init time) keeps `draw_screen` allocation-free and avoids per-frame `pygame.draw` calls.

The demo's `BouncingShapesBackdropFeature` extends `ScreenPart` for exactly this reason: it renders many translucent animated circles and diamonds as a fullscreen backdrop every frame, and any per-frame widget pipeline overhead would compound noticeably at 60 fps.

```python
from shared.part_lifecycle import ScreenPart

class BouncingShapesBackdropFeature(ScreenPart):
    HOST_REQUIREMENTS = {
        "bind_runtime": ("app", "screen_rect"),
    }

    def __init__(self, *, circle_count=28, diamond_count=0, seed=None,
                 scene_name=None, part_name="bouncing_shapes_backdrop"):
        super().__init__(part_name, scene_name=scene_name)
        # Sprites are fully pre-rendered at init time — draw_screen does
        # zero allocation; it only calls surface.blit() per shape.
        self._shapes = self._create_shapes(circle_count, diamond_count)

    def bind_runtime(self, demo) -> None:
        # Randomise starting positions once the screen rect is known.
        width, height = demo.screen_rect.size
        self._randomize_positions(width, height)

    def on_screen_update(self, host, dt_seconds: float) -> None:
        # Advance every shape position and bounce off screen edges.
        # Called by the screen lifecycle layer, not the widget tree.
        for shape in self._shapes:
            shape.x += shape.dx
            shape.y += shape.dy
            # ... edge bounce logic ...

    def draw_screen(self, _host, surface, _theme) -> None:
        # Blit pre-cached sprites directly onto the full-screen surface.
        # No widget pipeline overhead — this is the performance-critical path.
        for shape in self._shapes:
            left = int(round(shape.x - shape.radius))
            top = int(round(shape.y - shape.radius))
            surface.blit(shape.sprite, (left, top))
```

#### Choosing between `Part` and `ScreenPart`

| Scenario | Use |
|---|---|
| Owns windows, buttons, or other controls on the scene | `Part` |
| Encapsulates reusable domain logic behind command messages | `LogicPart` |
| Wires preamble / event routing / postamble for controls | `Part` |
| Uses scheduler, event bus, or part messaging | `Part` |
| Needs to be shared as a logic service by multiple parts | `LogicPart` |
| Draws a fullscreen or large background animation every frame | `ScreenPart` |
| Needs raw per-frame `dt_seconds` for physics/animation | `ScreenPart` |
| Requires bypassing the widget pipeline for performance | `ScreenPart` |

A `ScreenPart` can still declare `HOST_REQUIREMENTS` and participate in the normal `build`/`bind_runtime`/`configure_accessibility`/`shutdown_runtime` lifecycle — it just adds the three screen-layer hooks on top.

### Screen Lifecycle Composition

Use screen lifecycle callbacks for scene-level behavior composition.

```python
# Set base callbacks
app.set_screen_lifecycle(
    preamble=base_preamble,
    event_handler=base_event_handler,
    postamble=base_postamble,
    scene_name="main",
)

# Add a layer and keep a disposer
dispose_layer = app.chain_screen_lifecycle(
    preamble=feature_preamble,
    event_handler=feature_event_handler,
    postamble=feature_postamble,
    scene_name="main",
)

# Remove just this layer later
dispose_layer()
```

### Scheduler Pattern

`TaskScheduler` runs background work and routes task messages onto the main thread in `update()`.

```python
def launch(scheduler):
    def logic(task_id, params):
        for i in range(params["count"]):
            scheduler.send_message(task_id, {"step": i})
        return {"ok": True}

    def on_message(payload):
        print("progress", payload["step"])

    scheduler.add_task("demo", logic, parameters={"count": 8}, message_method=on_message)


# In your frame/update loop:
scheduler.update()
for event in scheduler.get_finished_events():
    print("finished", event.task_id)
for event in scheduler.get_failed_events():
    print("failed", event.task_id, event.error)

# Clear both finished and failed notifications for the next frame
scheduler.clear_events()

# Task lifecycle management
scheduler.remove_tasks("demo")          # cancel one or more tasks by id
scheduler.remove_all()                  # cancel all pending/running tasks

# Suspend/resume individual tasks (moves them out of the pending queue)
scheduler.suspend_tasks("task_a", "task_b")
scheduler.resume_tasks("task_a")
scheduler.suspend_all()                 # suspend every pending task at once
suspended_ids = scheduler.read_suspended()   # list of currently suspended task ids
count = scheduler.read_suspended_len()

# Pause/resume the entire executor (blocks tasks from starting new work)
scheduler.set_execution_paused(True)
is_paused = scheduler.is_execution_paused()
scheduler.set_execution_paused(False)

# Throttle main-thread message delivery per update() call
scheduler.set_message_dispatch_limit(50)          # max messages per update()
scheduler.set_message_dispatch_time_budget_ms(4)  # stop dispatching after 4 ms
scheduler.set_message_dispatch_limit(None)        # remove limit (deliver all)

# Pick a sensible worker count for the current machine
workers = TaskScheduler.recommended_worker_count()  # static method
scheduler = TaskScheduler(max_workers=workers)
```

### Value Change Callbacks

`SliderControl` and `ScrollbarControl` support value callbacks in two modes:

- `compat`: callback can be `(value)` or `(value, reason)`
- `reason-required`: callback must accept `(value, reason)`

```python
from gui import SliderControl, LayoutAxis, ValueChangeReason

def on_zoom_changed(value, reason):
    if reason is ValueChangeReason.MOUSE_DRAG:
        print("drag", value)
    elif reason is ValueChangeReason.KEYBOARD:
        print("keyboard", value)

slider = SliderControl(
    "zoom",
    Rect(20, 120, 240, 30),
    LayoutAxis.HORIZONTAL,
    1,
    30,
    12,
    on_change=on_zoom_changed,
    on_change_mode="reason-required",
)
```

`VALUE_CHANGE_CALLBACK_MODES` is a tuple of all valid mode strings: `("compat", "reason-required")`. Use it for validation or to enumerate accepted values.

`ensure_reason_callback(callback)` adapts a legacy value-only callback to one that also accepts a `reason` argument, letting you unify old and new callbacks without branching:

```python
from gui import ensure_reason_callback, ValueChangeReason

def legacy_on_change(value):          # old one-arg callback
    print(f"Value: {value}")

adapted = ensure_reason_callback(legacy_on_change)
# adapted is now callable as adapted(value, reason) with reason silently ignored.
# Pass None to get None back (no-op adapter).
adapted = ensure_reason_callback(None)  # returns None
```

## Feature Example: Part Registration and Runtime Binding

```python
from shared.part_lifecycle import Part

class StatusFeature(Part):
    HOST_REQUIREMENTS = {
        "build": ("app", "root"),
        "bind_runtime": ("app",),
    }

    def __init__(self):
        super().__init__("status_feature", scene_name="main")
        self.scheduler = None

    def build(self, host):
        # create controls under host.root
        return None

    def bind_runtime(self, host):
        self.scheduler = host.app.get_scene_scheduler("main")


# In app bootstrap:
# app.register_part(StatusFeature(), host=demo)
# app.build_parts(demo)
# app.bind_parts_runtime(demo)
```

## Control Widgets Guide

### Common Pattern: Creating and Adding Controls

All controls follow a consistent pattern: create with a unique ID, bounding rect, and options, then add to a parent.

```python
from gui import ButtonControl, ToggleControl, LabelControl

# Add a button
button = parent.add(
    ButtonControl("btn_id", rect, "Button Text", on_click=callback, style="angle", font_role="body")
)
# style controls visual shape; built-in values: "box" (default), "radio", "round", "angle", "check"
# font_role must be a registered font role name (default: "body")

# Add a toggle (state-tracking button)
toggle = parent.add(
    ToggleControl(
        "toggle_id",
        rect,
        "On",   # text_on: label shown when pushed=True
        "Off",  # text_off: label shown when pushed=False
        pushed=False,
        on_toggle=lambda pushed: print(f"Toggled: {pushed}"),
        # style controls visual shape; built-in values: "box" (default), "radio", "round", "angle", "check"
    )
)

# Activate/query toggle state
toggle.pushed = True  # Set state
is_on = toggle.pushed  # Read state

# Replace callbacks at runtime
button.set_on_click(lambda: print("new callback"))
button.set_on_click(None)     # remove callback
toggle.set_on_toggle(lambda pushed: print(pushed))
toggle.set_on_toggle(None)    # remove callback
```

### UiNode Common API

All controls inherit from `UiNode`. These properties and methods are available on every control.

```python
# Visibility and enabled state
node.visible = False        # hide (triggers on_visibility_changed hook)
node.enabled = False        # disable (triggers on_enabled_changed hook)
node.show()                 # equivalent to node.visible = True
node.hide()                 # equivalent to node.visible = False
node.enable()               # equivalent to node.enabled = True
node.disable()              # equivalent to node.enabled = False

# Geometry helpers (all call invalidate() after mutation)
node.set_pos(x, y)          # move top-left corner
node.resize(width, height)  # resize without moving
node.set_rect(rect)         # replace rect entirely

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

# Identifiers and layout
node.control_id             # str; unique identifier within the scene
node.rect                   # pygame.Rect; mutable geometry

# Focus and accessibility
node.tab_index              # int; -1 = not focusable, >= 0 = participates in Tab order
node.focused                # bool property; True when this node holds keyboard focus
node.accepts_focus()        # True when tab_index >= 0 (controls keyboard Tab traversal)
node.accepts_mouse_focus()  # True when a mouse click should transfer focus; defaults to accepts_focus()
                            # LabelControl returns False — clicks never steal focus from other controls
node.set_tab_index(n)       # set the tab order index
node.set_accessibility(role="button", label="Save File")

# Invalidation
node.invalidate()           # mark as dirty for next draw pass
```

### Toggle Control

`ToggleControl` is a two-state button that tracks a `pushed` boolean. It fires `on_toggle(pushed: bool)` each time it changes state.

```python
from gui import ToggleControl

toggle = parent.add(
    ToggleControl(
        "toggle_id",
        rect,
        text_on="ON",        # label shown when pushed=True
        text_off="OFF",      # label shown when pushed=False (defaults to text_on)
        pushed=False,        # initial state
        on_toggle=lambda pushed: print(f"State: {pushed}"),
        style="box",         # built-in values: "box" (default), "radio", "round", "angle", "check"
        font_role="body",
    )
)

# Read / set state directly
is_on = toggle.pushed
toggle.pushed = True

# Replace callback at runtime
toggle.set_on_toggle(lambda pushed: print(pushed))
toggle.set_on_toggle(None)   # remove callback

# Font role for rendering
toggle.font_role = "body"    # must be a registered role name
```

Keyboard: when the toggle has focus, `Space` or `Return` activates it.

### Label Control

Display read-only text. Useful for status, titles, and information display.

```python
from gui import LabelControl

label = parent.add(
    LabelControl("label_id", rect, "Initial Text", align="left")
)

# Update text via property (triggers invalidation)
label.text = "Updated text"

# Control font role, size, and alignment
label.font_role = "body"    # matches a registered font role
label.font_size = 14        # integer point size
label.align = "center"      # "left", "center", or "right"

# Convenience helper from GuiApplication
app.style_label(label, size=14, role="body")
```

Clicking a `LabelControl` never steals or clears keyboard focus — labels are informational and opt out of mouse-click focus acquisition.

### Slider Control

Capture numeric input with mouse drag or keyboard. `SliderControl` and `ScrollbarControl` use the dual-mode value-change callback system.

```python
from gui import SliderControl, LayoutAxis, ValueChangeReason

def on_value_changed(value, reason):
    print(f"Value: {value}, Reason: {reason}")
    if reason == ValueChangeReason.MOUSE_DRAG:
        print("User is dragging")
    elif reason == ValueChangeReason.KEYBOARD:
        print("User pressed arrow keys")

slider = parent.add(
    SliderControl(
        "slider_id",
        rect,
        axis=LayoutAxis.HORIZONTAL,
        minimum=0,
        maximum=100,
        value=50,
        on_change=on_value_changed,
        on_change_mode="reason-required",
    )
)

# Programmatic updates
slider.set_value(75)           # set absolute value, clamped; returns True if changed
slider.adjust_value(5)         # move by delta, clamped; returns True if changed
slider.set_normalized(0.5)     # set from a 0.0–1.0 ratio; returns True if changed
slider.value                   # read current value (plain attribute)
slider.normalized              # read current value as 0.0–1.0 ratio within range

# Replace callback or mode at runtime
slider.set_on_change_callback(new_callback)   # validated against current mode
slider.set_on_change_mode("compat")           # returns normalized mode string
```

### Scrollbar Control

Scrollbar for viewport scrolling. Unlike `SliderControl`, it describes a viewport position within content: `content_size` is the total scrollable length, `viewport_size` is the visible window, and `offset` is the current scroll position.

```python
from gui import ScrollbarControl, LayoutAxis, ValueChangeReason

def on_scroll(offset, reason):
    if reason == ValueChangeReason.MOUSE_DRAG:
        # Thumb drag
        pass
    elif reason == ValueChangeReason.WHEEL:
        # Mouse wheel
        pass
    elif reason == ValueChangeReason.KEYBOARD:
        # Arrow keys / PageUp / PageDown / Home / End
        pass
    elif reason == ValueChangeReason.PROGRAMMATIC:
        # set_offset() / adjust_offset() call
        pass

scrollbar = parent.add(
    ScrollbarControl(
        "scrollbar_id",
        rect,
        axis=LayoutAxis.VERTICAL,
        content_size=1000,   # total scrollable length in pixels
        viewport_size=200,   # visible area height in pixels
        offset=0,            # initial scroll position
        step=20,             # arrow-key and wheel step size
        on_change=on_scroll,
    )
)

# Programmatic updates
scrollbar.set_offset(100)      # absolute position, clamped; returns True if changed
scrollbar.adjust_offset(20)    # relative move, clamped; returns True if changed
fraction = scrollbar.scroll_fraction  # 0.0–1.0 normalized position

# Replace callback or mode at runtime
scrollbar.set_on_change_callback(new_callback)   # validated against current mode
scrollbar.set_on_change_mode("reason-required")  # returns normalized mode string
```

### Button Group Control

Mutually exclusive selection (radio button behavior). Each `ButtonGroupControl` is a single button belonging to a named group. Clicking any button in the group deselects the previously selected one.

```python
from gui import ButtonGroupControl

# Create one ButtonGroupControl per option, sharing the same group name.
btn_a = parent.add(
    ButtonGroupControl("option_a", rect_a, group="view_mode", text="List", selected=True,
                       on_activate=lambda: print("List selected"))
)
btn_b = parent.add(
    ButtonGroupControl("option_b", rect_b, group="view_mode", text="Grid")
)
btn_c = parent.add(
    ButtonGroupControl("option_c", rect_c, group="view_mode", text="Detail")
)

# Query which button is currently pushed
if btn_a.pushed:
    print("List view active")

# Query the selected control_id for the whole group
selected_id = btn_a.button_id  # returns the control_id of whichever is selected

# Replace or remove the activation callback at runtime
btn_a.set_on_activate(lambda: print("New callback"))
btn_a.set_on_activate(None)   # remove callback

# Clear stale group entries between independent app instances (e.g., in tests)
ButtonGroupControl.clear_group_registry("view_mode")
```

`on_activate` fires each time a button in the group is selected — whether by mouse click or keyboard. Keyboard: when a `ButtonGroupControl` has focus, `Space` or `Return` activates it (selects it and fires `on_activate`).

### Image Control

Display PNG/JPG images scaled to fit a rectangle.

```python
from gui import ImageControl

image = parent.add(
    ImageControl("image_id", rect, image_path="data/images/backdrop.jpg")
)

# Update image
image.set_image("data/images/new_image.png")
```

### Frame Control

A decorative border frame that groups content visually.

```python
from gui import FrameControl

frame = parent.add(
    FrameControl("frame_id", rect, border_width=2)
)

# Add controls inside the frame
label = frame.add(
    LabelControl("label", inner_rect, "Framed Content")
)

# Update border width at runtime (triggers invalidation)
frame.border_width = 3
```

### Arrow Box Control

Clickable arrow button with optional hold-repeat activation. Direction is specified in degrees: 0 = right, 90 = down, 180 = left, 270 = up. Used internally by scrollbars but usable standalone.

```python
from gui import ArrowBoxControl

up_arrow = parent.add(
    ArrowBoxControl(
        "up_arrow",
        rect,
        direction=270,                    # degrees (0=right, 90=down, 180=left, 270=up)
        on_activate=lambda: print("Up"),  # called on click and on hold-repeat
        repeat_interval_seconds=0.08,     # repeat rate while held
    )
)

# Replace activation callback at runtime
up_arrow.set_on_activate(lambda: print("New callback"))

# Remove callback
up_arrow.set_on_activate(None)
```

### Window Control

Floating, draggable window with title bar and frame.

```python
from gui import WindowControl

window = parent.add(
    WindowControl(
        "window_id",
        rect,
        "Window Title",
        preamble=None,  # Optional: lifecycle callback before event handling
        event_handler=None,  # Optional: custom event handler
        postamble=None,  # Optional: lifecycle callback after event handling
        use_frame_backdrop=True,
    )
)

# Add controls inside the window
button = window.add(
    ButtonControl("btn", inner_rect, "Click me")
)

# Query window state
is_active = window.active          # bool property
window_rect = window.rect          # full rect including title bar
content_rect = window.content_rect()     # excludes title bar

# Close (hide) the window
window.close()
```

### Panel Control

`PanelControl` is the base container for child controls. Use it to group related widgets, manage windows, and build layout regions. It optionally draws a theme background fill.

```python
from gui import PanelControl

# A region panel that draws a background
panel = root.add(
    PanelControl("sidebar", Rect(0, 0, 240, screen_height), draw_background=True)
)

# A transparent/non-painting container (useful with set_pristine/restore_pristine)
root_container = root.add(
    PanelControl("root_container", screen_rect, draw_background=False)
)

# Add children to a panel
label = panel.add(LabelControl("info", Rect(8, 8, 224, 24), "Panel content"))
button = panel.add(ButtonControl("ok", Rect(8, 40, 100, 32), "OK"))

# Remove a child
panel.remove(label)
```

`PanelControl` also manages floating `WindowControl` children: it tracks the active window, handles z-order with `_raise_window` / `_lower_window`, and clears stale drag state when windows are hidden or disabled.

### Task Panel Control

`TaskPanelControl` is a panel that slides in/out from a screen edge. Create it directly and add it to a root container. See the [Task Panel Configuration](#task-panel-configuration) section for a complete example.

```python
from gui import TaskPanelControl, ButtonControl
from pygame import Rect

task_panel = root.add(
    TaskPanelControl(
        "task_panel",
        Rect(0, 0, screen_width, 48),
        auto_hide=True,
        hidden_peek_pixels=4,
        animation_step_px=4,
        dock_bottom=False,
    )
)

button = task_panel.add(
    ButtonControl("task_btn", Rect(8, 8, 100, 32), "Task Button")
)
```

### Canvas Control

High-performance drawable surface with an internal event queue. Incoming mouse events are stored as `CanvasEventPacket` objects and drained by the caller each frame.

```python
from gui import CanvasControl, CanvasEventPacket

canvas = parent.add(
    CanvasControl(
        "canvas_id",
        rect,
        max_events=256,  # event queue capacity
    )
)

# Configure overflow behavior (default: drop_oldest)
canvas.set_overflow_mode("drop_newest")
canvas.set_overflow_handler(
    lambda dropped, size: print(f"Dropped {dropped} events, queue={size}")
)
canvas.set_motion_coalescing(True)  # merge consecutive motion events (default True)

# In your update loop, drain the event queue:
packet = canvas.read_event()
while packet is not None:
    if packet.is_left_down():
        x, y = packet.local_pos   # canvas-relative coordinates
        print(f"Left click at ({x}, {y})")
    elif packet.is_mouse_motion():
        print(f"Motion at {packet.local_pos}")
    elif packet.is_mouse_wheel():
        print(f"Wheel delta {packet.wheel_delta}")
    packet = canvas.read_event()

# Draw custom content onto the backing surface each frame:
canvas_surface = canvas.get_canvas_surface()
pygame.draw.circle(canvas_surface, (255, 0, 0), (100, 100), 50)
```

## Event Handling and Propagation

The framework uses canonical `GuiEvent` objects with three-phase dispatch: capture, target, and bubble.

### GuiEvent Fields

| Field | Type | Description |
|---|---|---|
| `kind` | `EventType` | Semantic event type enum |
| `type` | `int` | Raw pygame event type integer |
| `key` | `Optional[int]` | Keyboard key code (key events only) |
| `mod` | `int` | Keyboard modifier bitmask; non-zero on key events with active modifiers (e.g. `pygame.KMOD_SHIFT`) |
| `pos` | `Optional[tuple]` | Logical pointer position (screen coordinates, lock-adjusted) |
| `rel` | `Optional[tuple]` | Logical motion delta |
| `raw_pos` | `Optional[tuple]` | Raw pygame position before lock adjustment |
| `raw_rel` | `Optional[tuple]` | Raw pygame motion delta |
| `button` | `Optional[int]` | Mouse button index (1=left, 2=middle, 3=right) |
| `wheel_x` | `int` | Horizontal wheel delta |
| `wheel_y` | `int` | Vertical wheel delta |
| `text` | `Optional[str]` | Text input character (TEXT_INPUT events) |
| `widget_id` | `Optional[str]` | Widget control_id for widget events |
| `task_panel` | `bool` | True when event originates in the task panel |
| `task_id` | `Optional[Hashable]` | Scheduler task id for task events |
| `error` | `Optional[str]` | Error message for failed task events |
| `phase` | `EventPhase` | Current dispatch phase (CAPTURE/TARGET/BUBBLE) |
| `propagation_stopped` | `bool` | True if `stop_propagation()` was called |
| `default_prevented` | `bool` | True if `prevent_default()` was called |

### GuiEvent Helper Methods

```python
from gui import GuiEvent, EventPhase, EventType
import pygame

def handle_event(event: GuiEvent) -> bool:
    # --- Type checks ---
    event.is_quit()                          # True for QUIT events
    event.is_kind(EventType.KEY_DOWN, EventType.KEY_UP)  # True if kind is any of the args

    # --- Key events ---
    event.is_key_down()                      # True for any KEY_DOWN
    event.is_key_down(pygame.K_ESCAPE)       # True for Escape key down
    event.is_key_up(pygame.K_RETURN)         # True for Enter key up
    event.is_text_event()                    # True for TEXT_INPUT or TEXT_EDITING

    # Modifier bitmask — use pygame constants
    if event.mod & pygame.KMOD_SHIFT:
        print("Shift held")
    if event.mod & pygame.KMOD_CTRL:
        print("Ctrl held")

    # --- Mouse button events ---
    event.is_mouse_down()                    # any button down
    event.is_mouse_down(1)                   # left button down
    event.is_mouse_up(3)                     # right button up
    event.is_left_down()                     # left button down (equivalent to is_mouse_down(1))
    event.is_left_up()                       # left button up
    event.is_right_down()                    # right button down
    event.is_right_up()                      # right button up
    event.is_middle_down()                   # middle button down
    event.is_middle_up()                     # middle button up

    # --- Mouse motion / wheel ---
    event.is_mouse_motion()                  # True for MOUSE_MOTION
    event.is_mouse_wheel()                   # True for MOUSE_WHEEL
    event.wheel_delta                        # int; wheel_y (vertical scroll delta)

    # --- Geometry ---
    event.collides(rect)                     # True if pos is inside rect

    # --- Propagation ---
    event.stop_propagation()                 # halt dispatch to parent containers
    event.prevent_default()                  # suppress default framework behavior

    # --- Cloning ---
    copy = event.clone()                     # shallow copy with independent propagation state

    return True  # consumed
```

### Routed Event Flow

Events traverse the scene graph in three phases:

1. **CAPTURE**: Root → Target (top-down)
2. **TARGET**: Direct target handling
3. **BUBBLE**: Target → Root (bottom-up)

Containers automatically propagate events to children. Call `stop_propagation()` to halt traversal.

### Keyboard and Action Handling

```python
from gui import ActionManager

# Register actions
app.actions.register_action("zoom_in", lambda event: (print("Zooming in"), True))
app.actions.register_action("zoom_out", lambda event: (print("Zooming out"), True))

# Unregister an action
app.actions.unregister_action("zoom_out")

# Check registration and enumerate
if app.actions.has_action("zoom_in"):
    print("zoom_in is registered")
all_names = app.actions.registered_actions()   # sorted list of all registered names

# Bind keys to actions (scene-scoped or global)
app.actions.bind_key(pygame.K_PLUS, "zoom_in", scene="main")
app.actions.bind_key(pygame.K_MINUS, "zoom_out", scene="main")

# window_only=True restricts the binding to when a window has keyboard focus
app.actions.bind_key(pygame.K_DELETE, "delete_item", scene="main", window_only=True)

# Remove a specific binding
app.actions.unbind_key(pygame.K_MINUS, "zoom_out", scene="main")  # returns True if removed

# Inspect all bindings for an action
bindings = app.actions.bindings_for_action("zoom_in")
for binding in bindings:
    print(f"  key={binding.key} scene={binding.scene} window_only={binding.window_only}")
```

## Focus and Keyboard Input

Focus determines which widget receives keyboard input. The framework automatically manages focus traversal and visualization.

### Tab Traversal

Set tab indices to control keyboard navigation order.

```python
# During widget creation or after:
button1.set_tab_index(0)
button2.set_tab_index(1)
input_field.set_tab_index(2)

# Tab key navigates in order; Shift+Tab goes backward
# Focus ring wraps at boundaries
```

**Hint-aware cycling:** The first `Tab` press establishes focus context and shows the visual focus indicator on the current (or first) focusable node without moving focus. Subsequent `Tab` presses cycle through nodes in tab-index order. This means users always see the current focused control before cycling away from it.

**Active-window scope rule:** Tab traversal and focused-key routing are scoped to active windows. Controls inside inactive windows are excluded from focus candidates. If the currently focused control belongs to a window that becomes inactive, focus is cleared automatically until a valid active-scope target is focused again.

### Focus Management

The `FocusManager` is available directly on the `GuiApplication` instance as `app.focus`.

```python
from gui import FocusManager

# Access the application-wide focus manager
focus_manager = app.focus

# Query focus
current_node = focus_manager.focused_node          # currently focused UiNode, or None
current_id = focus_manager.focused_control_id      # control_id string, or None
has_any    = focus_manager.has_focus               # bool; True when any node holds focus

# Set focus programmatically
focus_manager.set_focus(node, show_hint=True)                  # focus a specific node
focus_manager.set_focus_by_id(app.scene, "my_button")          # focus by control_id; returns bool

# Clear focus
focus_manager.clear_focus()

# Cycle focus (Tab-style traversal); returns True when focus moved
focus_manager.cycle_focus(app.scene, forward=True)             # forward = Tab
focus_manager.cycle_focus(app.scene, forward=False)            # backward = Shift+Tab
# Optionally scope traversal to nodes inside a specific window
focus_manager.cycle_focus(app.scene, forward=True, window=my_window)

# Count focusable nodes (respects visibility, enabled state, and tab_index)
count = focus_manager.focusable_count(app.scene)               # int
count = focus_manager.focusable_count(app.scene, window=my_window)  # scoped to window
```

### Focus Visualization

`FocusVisualizer` renders a dashed rectangle around the currently focused control and fades it out after `FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS` (1.5 s). It is accessible directly as `app.focus_visualizer`.

```python
from gui.core.focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS
# 1.5 — shared timeout for both traversal hints and activation hints.

visualizer = app.focus_visualizer

# Show a hint for a specific node (called automatically by FocusManager on focus change)
visualizer.set_focus_hint(node)                # show hint
visualizer.set_focus_hint(node, show_hint=False)  # suppress hint (e.g., mouse-click focus)

# Clear the hint immediately (called automatically when focus is cleared)
visualizer.clear_focus_hint()

# Restart the hint timer for the given node without changing focus.
# Useful after a keyboard activation to extend hint visibility.
visualizer.refresh_focus_hint(node)    # True if hint was refreshed, False if no hint active
visualizer.refresh_focus_hint()        # refresh current hint node (no arg = use current)

# Query
visualizer.has_active_hint()   # True when a hint is currently visible or fading
```

**Keyboard activation and focus hints:** Activating a `ButtonControl`, `ToggleControl`, or `ButtonGroupControl` via `Space` or `Return` while focused automatically calls `refresh_focus_hint` so the focus indicator stays visible during the activation — using the same `FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS` timeout as Tab-traversal hints.

**Mouse-click focus:** `set_focus_hint(node, show_hint=False)` is used for mouse-click focus transfers so clicking a button does not re-trigger the visual indicator unnecessarily.

### Accessibility Configuration

```python
# Set accessibility metadata for screen readers
widget.set_accessibility(
    role="button",  # button, toggle, slider, textinput, etc.
    label="Save File",  # Accessible name
)

# Helper to set tab indices across controls
next_idx = 0
for control in [btn1, btn2, inp]:
    control.set_tab_index(next_idx)
    next_idx += 1
```

## Window and Layout Management

### Window Management

`WindowControl` is a floating, draggable window with a title bar. It is added to a `PanelControl` which manages window ordering and activation.

```python
from gui import WindowControl

window = panel.add(
    WindowControl(
        "window_id",
        rect,
        "Window Title",
        titlebar_height=24,
        preamble=None,          # optional: called before each event dispatch cycle
        event_handler=None,     # optional: custom event handler callback
        postamble=None,         # optional: called after each event dispatch cycle
        title_font_role="title",
        use_frame_backdrop=True,  # True = legacy frame visuals; False = black backing
    )
)

# Add controls inside the window
button = window.add(ButtonControl("btn", inner_rect, "Click me"))

# Query window state
is_active = window.active                    # bool property; read/write
window_rect = window.rect                    # full rect including title bar
content_rect = window.content_rect()         # excludes title bar
title_bar_rect = window.title_bar_rect()     # just the title bar area

# Programmatic close (hides the window, releasing active state)
window.close()

# Move window by a pixel delta
window.move_by(dx=10, dy=0)

# Pristine backdrop (restore background image before drawing)
window.set_pristine(my_surface)
window.restore_pristine(surface)
```

### Automatic Window Tiling

The framework includes automatic layout for multiple windows. Both `configure_window_tiling` and `set_window_tiling_enabled` accept an optional `scene_name` parameter so non-active scenes can be configured without switching scenes first.

`build_parts(host)` automatically primes the per-scene tiling registration order for all scenes after building parts, so no manual pre-registration ceremony (calling `tile_windows()` before first visibility toggles) is needed.

```python
# Configure tiling for the active scene or a named non-active scene
app.configure_window_tiling(
    gap=16,                  # pixels between windows
    padding=16,              # pixels from screen edge
    avoid_task_panel=True,   # exclude the task panel area from the work region
    center_on_failure=True,  # center window when tiling cannot fit all windows
    relayout=False,          # trigger immediate relayout when True
    scene_name="main",       # optional: target a non-active scene
)

app.set_window_tiling_enabled(True, relayout=False, scene_name="main")

# Trigger tiling immediately after visibility changes
app.tile_windows()                           # relayout all visible windows
app.tile_windows(newly_visible=[window])     # hint: only place the newly shown window

# Read current tiling configuration
settings = app.read_window_tiling_settings()  # dict of current settings

# Disable tiling
app.set_window_tiling_enabled(False)
```

`WindowTilingManager` is also accessible directly; `prime_registration()` locks the registration order for all windows currently in the scene without triggering a relayout:

```python
tiler = app.window_tiling   # active scene's WindowTilingManager
tiler.prime_registration()  # stamp registration order now; idempotent for existing windows
```

### Layout System

Position widgets using absolute coordinates or anchor-based relative positioning.

```python
from gui import LayoutAxis

# Set anchor bounds (usually screen rect)
app.layout.set_anchor_bounds(screen.get_rect())

# Anchor-based positioning
rect = app.layout.anchored(
    size=(200, 100),
    anchor="top_right",  # top_left, top_center, top_right,
                         # center_left, center, center_right,
                         # bottom_left, bottom_center, bottom_right
    margin=(20, 20),  # (right/left margin, top/bottom margin)
    use_rect=True,  # Return Rect instead of (x, y)
)

# Linear layout (horizontal or vertical strips)
app.layout.set_linear_properties(
    anchor=(100, 100),
    item_width=120,
    item_height=32,
    spacing=10,
    horizontal=True,
    wrap_count=0,     # optional: wrap after N items (0 = no wrap)
    use_rect=True,    # True = return Rect; False = return (x, y)
)

# Get next position in linear layout (auto-advances cursor)
rect1 = app.layout.next_linear()
rect2 = app.layout.next_linear()

# Or access by explicit index (does not advance cursor)
rect_at_0 = app.layout.linear(0)
rect_at_3 = app.layout.linear(3)

# Grid layout (rows and columns)
app.layout.set_grid_properties(
    anchor=(40, 40),
    item_width=160,
    item_height=120,
    column_spacing=12,
    row_spacing=12,
    use_rect=True,
)

# Access by explicit column/row (supports column_span and row_span)
rect_0_0 = app.layout.gridded(column=0, row=0)
rect_wide = app.layout.gridded(column=1, row=0, column_span=2)  # spans 2 columns

# Or advance through cells automatically (left→right, top→bottom)
rect_a = app.layout.next_gridded(columns=3)  # pass the column count for wrapping
rect_b = app.layout.next_gridded(columns=3)
```

## Observable Values and Data Binding

Use `ObservableValue` to create reactive data that automatically notifies subscribers when it changes.

```python
from gui import ObservableValue, PresentationModel

# Create an observable value
count = ObservableValue(0)

# Subscribe to changes; subscribe() returns an unsubscribe callable
def on_count_changed(new_value):
    print(f"Count changed to {new_value}")

unsubscribe = count.subscribe(on_count_changed)

# Update value via the property setter (triggers all subscribers)
count.value = 5

# Update without notifying subscribers
count.set_silently(10)

# Notify all subscribers with the current value even if it has not changed
count.force_notify()

# Introspect the number of active subscriptions
n = count.observer_count

# Unsubscribe later
unsubscribe()

# Create a presentation model (groups related values and manages subscriptions)
class SceneViewModel(PresentationModel):
    def __init__(self):
        super().__init__()
        self.zoom = ObservableValue(1.0)
        self.is_playing = ObservableValue(False)

view_model = SceneViewModel()

# bind() registers the subscription and tracks it for disposal
view_model.bind(view_model.zoom, lambda z: print(f"Zoom: {z}"))
view_model.bind(view_model.is_playing, lambda playing: print(f"Playing: {playing}"))

# Update values via property setter
view_model.zoom.value = 2.0
view_model.is_playing.value = True

# Dispose all managed subscriptions at once (e.g., on scene cleanup)
view_model.dispose()
```

## Canvas and Custom Drawing

The `CanvasControl` provides a drawable surface for custom graphics and interactive content. Mouse events that land on the canvas are queued as `CanvasEventPacket` objects. Drain the queue in your update hook each frame using `read_event()`.

```python
from gui import CanvasControl, CanvasEventPacket

canvas = parent.add(
    CanvasControl("canvas_id", rect, max_events=256)
)

# Drain the event queue each frame (e.g., in Part.on_update or a screen lifecycle postamble)
packet = canvas.read_event()
while packet is not None:
    if packet.is_left_down():
        lx, ly = packet.local_pos   # canvas-local coordinates
        print(f"Left click at ({lx}, {ly})")
    elif packet.is_mouse_motion():
        print(f"Motion: pos={packet.pos}, local={packet.local_pos}, rel={packet.rel}")
    elif packet.is_mouse_wheel():
        print(f"Wheel delta: {packet.wheel_delta}")
    packet = canvas.read_event()

# Draw custom content to the canvas backing surface each frame:
canvas_surface = canvas.get_canvas_surface()
pygame.draw.circle(canvas_surface, (255, 0, 0), (100, 100), 50)
pygame.draw.line(canvas_surface, (0, 255, 0), (0, 0), (200, 200), 2)
```

`CanvasEventPacket` helper methods: `is_mouse_motion()`, `is_mouse_wheel()`, `is_mouse_down(button)`, `is_mouse_up(button)`, `is_left_down()`, `is_left_up()`, `is_right_down()`, `is_right_up()`, `is_middle_down()`, `is_middle_up()`.

Fields: `kind`, `pos` (screen coordinates), `local_pos` (canvas-relative coordinates), `rel`, `button`, `wheel_delta`.

## Task Panel Configuration

`TaskPanelControl` is a panel that slides in/out from an edge of the screen, typically holding application-level action buttons. Construct it like any other control and add it to a root container.

```python
from gui import TaskPanelControl, ButtonControl
from pygame import Rect

# Create task panel docked at the top of the screen
task_panel = root.add(
    TaskPanelControl(
        "task_panel",
        Rect(0, 0, screen_width, 48),
        auto_hide=True,          # slide out of view when not hovered
        hidden_peek_pixels=4,    # pixels visible when hidden (gives hover target)
        animation_step_px=4,     # pixels per frame while animating
        dock_bottom=False,       # True = dock to bottom edge instead
    )
)

# Add buttons to the task panel
exit_btn = task_panel.add(
    ButtonControl("exit_btn", Rect(8, 8, 100, 32), "Exit", on_click=app.quit)
)
exit_btn.set_accessibility(role="button", label="Exit application")

# Mutate settings at runtime
task_panel.set_auto_hide(False)
task_panel.set_hidden_peek_pixels(8)
task_panel.set_animation_step_px(6)
```

## Themes and Styling

`ColorTheme` is constructed without arguments; its palette uses built-in colors. Each scene runtime gets its own theme. Register font roles per-scene via `app.register_font_role(...)`.

```python
from gui import ColorTheme, BuiltInGraphicsFactory

# Each scene has a theme accessible as app.theme (for the active scene).
# Full built-in palette:
bg_color    = app.theme.background  # scene fill color
text_color  = app.theme.text        # primary text color
light_color = app.theme.light       # lightest widget surface
med_color   = app.theme.medium      # mid-tone (used for disabled-state text/borders)
dark_color  = app.theme.dark        # darkest border/shadow accent
high_color  = app.theme.highlight   # selection / focus accent
shadow_col  = app.theme.shadow      # text drop-shadow color

# Register font roles for a scene (overrides built-in body/title/display defaults)
app.register_font_role(
    role_name="body",
    size=14,
    file_path="data/fonts/Ubuntu-B.ttf",   # relative to repo root, or absolute
    system_name="arial",                    # pygame system font fallback
    bold=False,
    italic=False,
    scene_name="main",                      # omit to use the currently active scene
)

app.register_font_role(
    role_name="heading",
    size=24,
    file_path="data/fonts/Gimbot.ttf",
    system_name="arial",
    bold=True,
    scene_name="main",
)

# Apply font role to a label via the convenience helper
app.style_label(label, size=14, role="body")

# For other controls, set font_role and related properties directly:
button.font_role = "body"
toggle.font_role = "body"
```

## Advanced Patterns

### FontManager

`FontManager` manages named font roles (e.g. `"body"`, `"title"`, `"display"`) and caches loaded `pygame.font.Font` objects. Each scene has its own `FontManager`; access the active scene's instance via `app.theme.fonts`.

Three roles are pre-registered by default for every scene:

| Role | Typeface | Default size |
|---|---|---|
| `"body"` | Ubuntu-B.ttf / arial | 16 |
| `"title"` | Gimbot.ttf / arial bold | 14 |
| `"display"` | Gimbot.ttf / arial bold | 72 |

```python
from gui import FontManager

fonts = app.theme.fonts   # active scene's FontManager

# Register or update a role
fonts.register_role(
    "heading",
    size=24,
    file_path="data/fonts/Ubuntu-B.ttf",   # relative to resource root, or absolute
    system_name="arial",                   # pygame system-font fallback
    bold=True,
    italic=False,
)

# Load a font object from a registered role
font = fonts.get_font("heading")        # returns pygame.font.Font at the role's size
font = fonts.get_font("heading", size=32)  # override size for this call only

# Introspect registered roles
names = fonts.role_names()              # tuple of all registered role names in order
exists = fonts.has_role("heading")      # True/False
rev = fonts.revision                    # int; increments whenever a role changes
```

The `revision` property is used internally so controls can detect font changes and rebuild their cached bitmaps.

#### FontInstance — measurement and metrics

`font_instance()` returns a bound view over a resolved role+size pair. Use it to measure text geometry without rendering.

```python
fonts = app.theme.fonts

# Get a bound instance for a registered role (optionally at an overridden size)
fi = fonts.font_instance("heading")          # at the role's registered size
fi = fonts.font_instance("heading", size=48) # at an explicit size

# Size and metrics
fi.point_size    # int; effective point size
fi.line_height   # int; font line height in pixels (pygame.font.Font.get_height())

# Measure text width/height in pixels
width, height = fi.text_size("Hello")    # no shadow padding

# Measure including shadow padding (matches what LabelControl renders)
width, height = fi.text_surface_size("Hello", shadow=True)
width, height = fi.text_surface_size("Hello", shadow=True, shadow_offset=(2, 2))
```

Example: size a label's rect to exactly fit its text surface:

```python
label = root.add(LabelControl("title", Rect(24, 24, 1, 1), "gui_do"))
app.style_label(label, size=64, role="display")
fi = app.theme.fonts.font_instance(label.font_role, size=label.font_size)
label.rect.size = fi.text_surface_size(label.text, shadow=True)
```

### EventManager

`EventManager` converts raw pygame events to canonical `GuiEvent` objects. It is accessible as `app.event_manager`, but in most cases `GuiApplication.process_event(event)` calls it automatically. Use it directly when you need a standalone conversion outside the main loop.

```python
from gui import EventManager, GuiEvent

manager = EventManager()
gui_event: GuiEvent = manager.to_gui_event(raw_pygame_event)
# pointer_pos can be supplied explicitly if not embedded in the event
gui_event = manager.to_gui_event(raw_event, pointer_pos=(x, y))
```

### Event Bus (Pub-Sub)

`EventBus` is a scoped publish-subscribe bus for non-input UI events. Access it as `app.events`.

```python
from gui import EventBus

bus = app.events

# Subscribe; returns a Subscription object for later removal
sub = bus.subscribe("status_changed", lambda payload: print(f"Status: {payload}"))

# Subscribe with an optional scope tag for bulk removal
sub2 = bus.subscribe("data_ready", handler, scope="life_scene")

# Publish to all matching subscribers
bus.publish("status_changed", {"message": "Ready"})

# Publish with a scope: delivers to unscoped subscribers AND scope-matched subscribers
bus.publish("data_ready", result, scope="life_scene")
# Publish with no scope (default): delivers ONLY to unscoped subscribers
bus.publish("status_changed", {"message": "Ready"})

# Unsubscribe one subscription
bus.unsubscribe(sub)

# Remove all subscriptions tagged with a scope; returns the count removed
removed = bus.unsubscribe_scope("life_scene")

# Subscribe for exactly one delivery, then automatically unsubscribe
bus.once("startup_done", lambda _: print("Startup complete!"))

# Introspect — total subscription count or per-topic
total = bus.subscriber_count()
for_topic = bus.subscriber_count("status_changed")
```

### Cross-Part Communication via Messaging

Parts communicate by sending dictionary messages to named target parts. The receiver drains its queue each frame.

```python
from shared.part_lifecycle import Part

class ProducerPart(Part):
    def on_update(self, host):
        # Send a message to a named target part
        self.send_message("consumer_part", {
            "topic": "data_update",
            "data": {"value": 42}
        })

class ConsumerPart(Part):
    def on_update(self, host):
        # Drain the incoming message queue
        while self.has_messages():
            payload = self.pop_message()
            if payload.get("topic") == "data_update":
                print(f"Received data: {payload['data']}")

        # Other queue introspection helpers:
        # self.peek_message()        -> copy of next without removing
        # self.message_count()       -> int queue length
        # self.message_queue_empty() -> bool
        # self.clear_messages()      -> discard all queued messages
```

### Part Font Role Management

Parts can register their own namespaced font roles without colliding with other parts or application-level roles. Roles are stored under a qualified name `part.<part_name>.<role_name>` and resolved via `self.font_role(...)`.

```python
from shared.part_lifecycle import Part

class MyFeature(Part):
    def __init__(self):
        super().__init__("my_feature", scene_name="main")

    def build(self, host) -> None:
        # Register a single namespaced font role owned by this part
        self.register_font_role(
            host,
            "heading",
            size=20,
            file_path="data/fonts/Ubuntu-B.ttf",
            system_name="arial",
            bold=True,
            scene_name="main",
        )

        # Register several roles at once
        self.register_font_roles(
            host,
            {
                "body":    {"size": 14, "system_name": "arial"},
                "caption": {"size": 11, "system_name": "arial", "italic": True},
            },
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        # Resolve the local role name to the qualified global name
        heading_role = self.font_role("heading")   # "part.my_feature.heading"
        host.app.style_label(self.title_label, size=20, role=heading_role)
```

### LogicPart Runnables for Scheduler Workers

For compute-heavy features, keep scheduler control flow in a render part and move pixel/algorithm work into one or more `LogicPart` providers. Register worker entrypoints as named runnables in the logic part, then invoke them from scheduler tasks via `app.run_part_runnable(...)`.

```python
from shared.part_lifecycle import LogicPart, RoutedMessagePart

class MandelbrotLogicPart(LogicPart):
    def bind_runtime(self, host) -> None:
        # Expose worker entrypoints via the public GuiApplication API.
        host.app.register_part_runnable(self.name, "iterative_task", self.run_iterative_task)
        host.app.register_part_runnable(self.name, "recursive_task", self.run_recursive_task)

    def run_iterative_task(self, scheduler, task_id, params):
        ...  # emits scheduler.send_message(task_id, payload)

class MandelbrotRenderFeature(RoutedMessagePart):
    def bind_runtime(self, demo) -> None:
        # Bind aliases so one render part can target multiple logic providers.
        self.bind_logic_part("mandelbrot_logic_primary", alias="primary")
        self.bind_logic_part("mandelbrot_logic_can1", alias="can1")

    def _run_logic(self, demo, alias: str, runnable: str, task_id: str, params):
        provider_name = self.logic_part_name(alias=alias)
        scheduler = demo.app.get_scene_scheduler("main")
        demo.app.run_part_runnable(provider_name, runnable, scheduler, task_id, params)

    def launch_recursive(self, demo):
        scheduler = demo.app.get_scene_scheduler("main")
        scheduler.add_task(
            "recu",
            lambda task_id, params: self._run_logic(demo, "primary", "recursive_task", task_id, params),
            parameters={...},
            message_method=self.make_progress_handler(demo, "recu"),
        )
```

This pattern keeps concerns clean:

- render part: window/canvas state, launch modes, status flow, payload painting
- logic part(s): viewport math, pixel function, recursive/iterative algorithms
- scheduler: task lifecycle, progress/failure events, main-thread message delivery

### Pointer and Input Lock

`GuiApplication` supports two lock modes for pointer-intensive interactions (canvas dragging, first-person input):

**Area lock** — clamp the pointer inside a rectangular region.

```python
# Confine pointer to a rect (clamped in process_event before dispatch)
app.set_lock_area(some_rect)

# Release area lock
app.set_lock_area(None)
```

**Point lock** — stationary logical cursor with relative motion deltas (first-person / drag-canvas pattern).

```python
# Engage point lock; pointer renders at lock_point_pos; motion recalculated as deltas
app.set_lock_point(locking_object, point=(cx, cy))  # point defaults to screen center

# Read motion delta from a motion event while locked
delta = app.get_lock_point_motion_delta(event)  # (dx, dy) or None if not locked/not motion

# Release point lock; hardware cursor warps back to lock_point_pos
app.set_lock_point(None)

# Query lock state
if app.mouse_point_locked:
    cx, cy = app.lock_point_pos   # position where virtual cursor is drawn

# Read current logical pointer position (lock-adjusted, always up to date)
x, y = app.logical_pointer_pos
```

### InvalidationTracker The active tracker is available as `app.invalidation`. The renderer calls it internally each frame, but you can force a full redraw from application code:

```python
from gui import InvalidationTracker

# Force a full redraw on the next frame (e.g., after a theme change)
app.invalidation.invalidate_all()

# The renderer calls begin_frame() at the start of each draw pass.
# Returns (full_redraw: bool, regions: list) — regions is always empty in the current implementation.
full, regions = app.invalidation.begin_frame()

# end_frame() clears the full-redraw flag after the frame is done.
app.invalidation.end_frame()
```

### Scene Transitions

Switch between scenes smoothly.

```python
# Create scenes — note: create_scene() does NOT make the scene active.
# call switch_scene() to activate the intended startup scene.
app.create_scene("main")
app.create_scene("settings")
app.create_scene("about")

# Configure non-active scenes directly using scene_name= (no switch needed)
app.configure_window_tiling(gap=16, padding=16, avoid_task_panel=True,
                             center_on_failure=True, relayout=False,
                             scene_name="settings")
app.set_window_tiling_enabled(True, relayout=False, scene_name="settings")

# Activate the startup scene
app.switch_scene("main")

# Register parts for each scene
main_parts = [Feature1(), Feature2()]
for part in main_parts:
    app.register_part(part, host=demo)

# Build and bind parts — build_parts() also auto-primes tiling registration
app.build_parts(demo)
app.bind_parts_runtime(demo)

# Later, switch to a different scene
app.switch_scene("settings")
# Previous scene's scheduler and timers are suspended
```

### Lifecycle Callbacks

Perform setup/cleanup at key points in the application lifecycle.

```python
def on_scene_start():
    print("Scene is now active")

def on_scene_end():
    print("Scene is no longer active")

app.set_screen_lifecycle(
    preamble=on_scene_start,
    postamble=on_scene_end,
    scene_name="main",
)
```

### Using Timers for Timed Events

The `Timers` service schedules one-shot and repeating callbacks per scene. Access the active scene's timer service via `app.timers`.

```python
# Access the active scene's timer service
timers = app.timers

# Schedule a one-shot timer (fires once after delay_seconds, then removes itself)
timers.add_once("my_timer", delay_seconds=1.0, callback=lambda: print("1 second elapsed"))

# Schedule a repeating timer (fires every interval_seconds)
timers.add_timer(
    "repeating",
    interval_seconds=0.5,
    callback=lambda: print("Fires every 500 ms"),
)

# Reschedule an existing timer (preserves elapsed accumulator)
timers.reschedule("repeating", new_interval_seconds=0.25)

# Check and cancel a specific timer
if timers.has_timer("my_timer"):
    timers.remove_timer("my_timer")

# List all active timer ids
ids = timers.timer_ids()

# Cancel all timers at once; returns the count that were removed
cancelled = timers.cancel_all()
```

## GuiApplication Helpers

`GuiApplication` exposes a number of shorthand helpers beyond the basic scene-cycle API.

### Scene and Part Management

```python
# Scene queries
scene_names = app.scene_names()       # list of all registered scene names
is_known   = app.has_scene("about")   # True if the scene exists
removed    = app.remove_scene("about") # True when removed (cannot remove active scene)
active     = app.active_scene_name    # name of the currently active scene

# Part management
app.register_part(my_part, host=demo)   # register a Part with optional host
app.unregister_part("my_feature")       # unregister and shutdown; returns bool
part = app.get_part("my_feature")       # Part instance or None
names = app.part_names()                # tuple of registered part names in order
```

### Logic Part Bindings

```python
app.bind_part_logic("consumer", "logic_part")          # bind consumer to LogicPart
app.unbind_part_logic("consumer", alias="default")     # remove one binding; returns bool
name = app.get_part_logic("consumer", alias="default") # provider name or None

# Send a command message from a consumer to its bound LogicPart
app.send_part_logic_message("consumer", {"command": "reset"})
```

### Node Search

```python
# Find the first node with a given control_id in the active (or named) scene
node = app.find("my_button")
node = app.find("my_button", scene_name="settings")

# Find all nodes satisfying a predicate
visible_buttons = app.find_all(lambda n: n.visible and hasattr(n, "on_click"))
```

### Focus Helpers

```python
# Focus a control by its control_id; returns True when focused successfully
focused = app.focus_on("my_button")
focused = app.focus_on("my_button", scene_name="settings")
```

### Part Accessibility and Messaging Helpers

```python
# Call configure_accessibility on all parts in order (returns next available tab index)
next_idx = app.configure_parts_accessibility(demo, tab_index_start=0)

# Send a message between two registered parts by name
app.send_part_message("producer_part", "consumer_part", {"topic": "data_update", "value": 42})
```

### Scene-Specific Services

```python
# Access a scene's scheduler or graphics factory by name
scheduler  = app.get_scene_scheduler("main")
factory    = app.get_scene_graphics_factory("main")

# Scene-level prewarm (runs Part.prewarm for active scene parts + shared parts)
warmed = app.prewarm_scene("control_showcase")
warmed = app.prewarm_scene("control_showcase", force=True)

# First-open profiling controls
app.configure_first_frame_profiling(enabled=True, min_ms=0.25)
# Optional custom logger
app.configure_first_frame_profiling(enabled=True, logger=lambda msg: print(msg))

# Font role queries for the active (or named) scene
roles = app.font_roles()               # tuple of registered role names
roles = app.font_roles(scene_name="main")

# Window tiling helpers
app.tile_windows()                     # immediately relayout all visible windows
app.tile_windows(newly_visible=[win])  # hint which window was just made visible
settings = app.read_window_tiling_settings()  # current tiling configuration dict

# Scene backdrop (pristine background image blit before every frame)
# source can be a path string (relative to data/images/), a pygame.Surface, or None
app.set_pristine("backdrop.jpg", scene_name="main")        # load from data/images/
app.set_pristine(my_surface, scene_name="main")            # use an existing Surface
app.set_pristine(None, scene_name="main")                  # clear backdrop
app.restore_pristine()                                     # blit active scene backdrop to display
app.restore_pristine(scene_name="main", surface=my_surf)   # blit to a specific surface

# Coordinate conversion
local_pos = app.convert_to_window(screen_pos, window)  # convert (x,y) to window-local coords
```

Environment shortcut: set `GUI_DO_PROFILE_FIRST_OPEN=1` (or `true`/`yes`/`on`) before app startup to enable first-open hotspot profiling without calling `configure_first_frame_profiling(...)` manually.

## UiEngine Standalone Usage

`app.run()` is the preferred entry point and manages `UiEngine` internally. `app.run()` accepts `target_fps` and an optional `max_frames` limit (useful in tests), and returns the number of frames processed.

```python
# Standard usage
frames = app.run(target_fps=60)

# Bounded run — exits after at most N frames
frames = app.run(target_fps=60, max_frames=300)
```

Use `UiEngine` directly only when you need frame-level control from an outer runner.

```python
from gui import UiEngine

engine = UiEngine(app, target_fps=60)

# Bounded run — returns the number of frames processed
frames = engine.run(max_frames=300)

# Read measured FPS after the loop
print(f"Average FPS: {engine.current_fps:.1f}")
```

The engine calls `app.process_event(event)`, `app.update(dt_seconds)`, `app.draw()`, and `pygame.display.flip()` each frame, then calls `app.shutdown()` when the loop exits.

## Cursor Management

`GuiApplication` hides the system cursor at startup and renders a software cursor each frame. Two built-in cursors are registered by default: `normal` and `hand`.

```python
# Register a custom cursor (image looked up under data/cursors/ or absolute path)
app.register_cursor("crosshair", "crosshair.png", hotspot=(8, 8))

# Switch the active cursor
app.set_cursor("hand")
app.set_cursor("normal")
app.set_cursor("crosshair")
```

The renderer blits the active cursor surface each frame at the logical pointer position (or the lock-point position when point-lock is active).

## Contributing

### Development Setup

```bash
python -m venv venv
source venv/Scripts/activate  # Windows PowerShell / Git Bash path may differ
pip install pygame numpy
```

For CI parity:

```bash
pip install -r requirements-ci.txt
```

### Run Tests

```bash
python -m pytest -q
```

## Public API

```python
from gui import (
    GuiApplication,
    UiEngine,
    PanelControl,
    LabelControl,
    ButtonControl,
    ArrowBoxControl,
    ButtonGroupControl,
    CanvasControl,
    CanvasEventPacket,
    FrameControl,
    ImageControl,
    SliderControl,
    ScrollbarControl,
    TaskPanelControl,
    ToggleControl,
    WindowControl,
    LayoutAxis,
    LayoutManager,
    WindowTilingManager,
    ActionManager,
    EventManager,
    EventBus,
    FocusManager,
    FontManager,
    EventPhase,
    EventType,
    GuiEvent,
    VALUE_CHANGE_CALLBACK_MODES,
    ValueChangeCallbackMode,
    ValueChangeCallback,
    ensure_reason_callback,
    normalize_value_change_callback_mode,
    ValueChangeReason,
    InvalidationTracker,
    ObservableValue,
    PresentationModel,
    TaskEvent,
    TaskScheduler,
    Timers,
    BuiltInGraphicsFactory,
    ColorTheme,
)

# Demo-only contracts are intentionally outside gui package:
from demo_parts.mandelbrot_demo_part import MandelStatusEvent
```

## Demo/Package Boundary

- `gui/` contains reusable framework/runtime functionality.
- `demo_parts/` contains demo-specific contracts and helpers.
- Boundary scope for demo entrypoints is `*_demo.py`.
- Active demo entrypoints should consume the framework through `from gui import ...`, without aliases, and with a single `from gui import (...)` block.

## Architecture Docs

- `docs/public_api_spec.md`: supported exports and strict API contracts.
- `docs/event_system_spec.md`: normalized event model and routing semantics.
- `docs/architecture_boundary_spec.md`: package boundary rules and enforcement tests.

## Run Boundary Contract Tests

```bash
python -m unittest tests.test_boundary_contracts tests.test_public_api_exports tests.test_mandel_event_schema_exports tests.test_public_api_docs_contracts tests.test_architecture_boundary_docs_contracts tests.test_contract_command_parity tests.test_readme_public_api_contracts tests.test_readme_docs_contracts tests.test_contract_docs_helpers tests.test_contract_catalog_consistency -v
python -m pytest -q tests/test_boundary_contracts.py
python -m pytest -q tests/test_boundary_contracts.py tests/test_public_api_exports.py tests/test_mandel_event_schema_exports.py tests/test_public_api_docs_contracts.py tests/test_architecture_boundary_docs_contracts.py tests/test_contract_command_parity.py tests/test_readme_public_api_contracts.py tests/test_readme_docs_contracts.py tests/test_contract_docs_helpers.py tests/test_contract_catalog_consistency.py
```
