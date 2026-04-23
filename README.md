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
- `control_showcase`: dedicated showcase scene with its own backdrop and a `Back` task-panel button

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

### Part Lifecycle

A feature is a `Part` with optional hooks:

- `build(host)`
- `bind_runtime(host)`
- `configure_accessibility(host, tab_index_start) -> int`
- `handle_event(host, event) -> bool`
- `on_update(host)`
- `draw(host, surface, theme)`
- `shutdown_runtime(host)`

Host field requirements can be declared per hook using `HOST_REQUIREMENTS` and are validated before invocation.

### Part Types: `Part`, `LogicPart`, and `ScreenPart`

There are three part base classes in `shared.part_lifecycle`. Choosing between them depends on what the feature owns and how it runs.

#### `Part` — General-purpose feature unit

`Part` is the standard base for features that build and manage controls (windows, buttons, canvases, sliders, etc.) on a scene. Its lifecycle hooks integrate directly with `GuiApplication` scene management: `build` creates controls, `bind_runtime` wires services, `on_update` runs frame logic, and `draw` renders into its own controls rather than directly onto the screen surface.

Use `Part` for features that:
- own a window or other UI structure on the scene
- coordinate preamble, event routing, and postamble for those controls
- communicate through the scheduler, event bus, or part messaging

The demo's `LifeSimulationFeature` and `MandelbrotRenderFeature` both extend `Part`. Each owns a `WindowControl` containing a `CanvasControl` and control widgets. Their screen-drawing responsibilities are delegated to those controls — the Part itself is responsible for wiring and orchestration, not raw pixel output.

```python
from shared.part_lifecycle import Part

class LifeSimulationFeature(Part):
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
class MandelbrotRenderFeature(Part):
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
                 scene_name="main", part_name="bouncing_shapes_backdrop"):
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
    ButtonControl("btn_id", rect, "Button Text", on_click=callback, style="angle")
)

# Add a toggle (state-tracking button)
toggle = parent.add(
    ToggleControl(
        "toggle_id",
        rect,
        "On",   # text_on: label shown when pushed=True
        "Off",  # text_off: label shown when pushed=False
        pushed=False,
        on_toggle=lambda pushed: print(f"Toggled: {pushed}"),
    )
)

# Activate/query toggle state
toggle.pushed = True  # Set state
is_on = toggle.pushed  # Read state
```

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
slider.set_value(75)
slider.adjust_value(5)   # move by delta, clamped
slider.value             # read current value
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
scrollbar.set_offset(100)      # absolute position, clamped
scrollbar.adjust_offset(20)    # relative move, clamped
fraction = scrollbar.scroll_fraction  # 0.0–1.0 normalized position
```

### Button Group Control

Mutually exclusive selection (radio button behavior). Each `ButtonGroupControl` is a single button belonging to a named group. Clicking any button in the group deselects the previously selected one.

```python
from gui import ButtonGroupControl

# Create one ButtonGroupControl per option, sharing the same group name.
btn_a = parent.add(
    ButtonGroupControl("option_a", rect_a, group="view_mode", text="List", selected=True)
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

# Clear stale group entries between independent app instances (e.g., in tests)
ButtonGroupControl.clear_group_registry("view_mode")
```

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
is_active = window.is_active()
window_rect = window.get_window_rect()
content_rect = window.content_rect()
```

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

### Event Phases and Propagation

```python
from gui import GuiEvent, EventPhase, EventType

def handle_event(event):
    # Check event type
    if event.kind == EventType.MOUSE_BUTTON_DOWN:
        print(f"Mouse button {event.button} pressed at {event.pos}")
    elif event.kind == EventType.KEY_DOWN:
        print(f"Key {event.key} pressed")

    # Stop propagation to parent containers
    event.stop_propagation()

    # Prevent default browser/system behavior
    event.prevent_default()

    # Return True to consume event
    return True
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

# Bind keys to actions (scene-scoped or global)
app.actions.bind_key(pygame.K_PLUS, "zoom_in", scene="main")
app.actions.bind_key(pygame.K_MINUS, "zoom_out", scene="main")
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

### Focus Management

The `FocusManager` is available directly on the `GuiApplication` instance as `app.focus`.

```python
from gui import FocusManager

# Access the application-wide focus manager
focus_manager = app.focus

# Query focus
current_node = focus_manager.focused_node          # currently focused UiNode, or None
current_id = focus_manager.focused_control_id      # control_id string, or None

# Set focus programmatically
focus_manager.set_focus(node, show_hint=True)                  # focus a specific node
focus_manager.set_focus_by_id(app.scene, "my_button")          # focus by control_id; returns bool

# Clear focus
focus_manager.clear_focus()
```

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
is_active = window.is_active()
window_rect = window.get_window_rect()   # includes title bar
content_rect = window.content_rect()     # excludes title bar

# Pristine backdrop (restore background image before drawing)
window.set_pristine(my_surface)
window.restore_pristine(surface)
```

### Automatic Window Tiling

The framework includes automatic layout for multiple windows.

```python
# Enable automatic tiling
app.configure_window_tiling(
    gap=16,  # Pixels between windows
    padding=16,  # Pixels from screen edge
    avoid_task_panel=True,  # Don't overlap task panel
    center_on_failure=True,  # Center window if tiling fails
    relayout=False,  # Immediately relayout existing windows
)

app.set_window_tiling_enabled(True)

# Disable tiling
app.set_window_tiling_enabled(False)
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
    anchor="top_right",  # top_left, top_center, top_right, center, etc.
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
)

# Get next position in linear layout
rect1 = app.layout.next_linear()
rect2 = app.layout.next_linear()
```

## Observable Values and Data Binding

Use `ObservableValue` to create reactive data that automatically notifies subscribers when it changes.

```python
from gui import ObservableValue, PresentationModel

# Create an observable value
count = ObservableValue(initial_value=0)

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
# Access palette colors directly:
bg_color = app.theme.background
text_color = app.theme.text

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

# Publish to subscribers in a specific scope only
bus.publish("data_ready", result, scope="life_scene")

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

### Scene Transitions

Switch between scenes smoothly.

```python
# Create multiple scenes
app.create_scene("main")
app.create_scene("settings")
app.create_scene("about")

# Register parts for each scene
main_parts = [Feature1(), Feature2()]
for part in main_parts:
    app.register_part(part, host=demo, scene_name="main")

# Build and bind parts for a scene
app.switch_scene("main")
app.build_parts(demo)
app.bind_parts_runtime(demo)

# Later, switch to a different scene
app.switch_scene("settings")
# Previous scene's scheduler and timers are suspended
```

### Lifecycle Callbacks

Perform setup/cleanup at key points in the application lifecycle.

```python
def on_scene_start(host):
    print("Scene is now active")

def on_scene_update(host, dt):
    print(f"Frame time: {dt}")

def on_scene_end(host):
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

### Scene-Specific Services

```python
# Access a scene's scheduler or graphics factory by name
scheduler  = app.get_scene_scheduler("main")
factory    = app.get_scene_graphics_factory("main")

# Font role queries for the active (or named) scene
roles = app.font_roles()               # tuple of registered role names
roles = app.font_roles(scene_name="main")

# Window tiling helpers
app.tile_windows()                     # immediately relayout all visible windows
settings = app.read_window_tiling_settings()  # current tiling configuration dict
```

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
python -m unittest discover -s tests -p "test_*.py" -v
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
