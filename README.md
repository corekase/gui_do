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
        "Off",  # label when not pushed
        "On",   # label when pushed
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
    LabelControl("label_id", rect, "Initial Text")
)

# Update text
label.set_label("Updated text")

# Apply styling
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
        min_value=0,
        max_value=100,
        current_value=50,
        on_change=on_value_changed,
        on_change_mode="reason-required",
    )
)

# Programmatic updates
slider.set_value(75)
slider.value  # Read current value
```

### Scrollbar Control

Similar to slider but includes increment/decrement arrow buttons at the ends.

```python
from gui import ScrollbarControl, LayoutAxis, ValueChangeReason

def on_scroll(value, reason):
    if reason == ValueChangeReason.MOUSE_DRAG:
        # Thumb drag
        pass
    elif reason == ValueChangeReason.ARROW_CLICK:
        # Arrow button click
        pass

scrollbar = parent.add(
    ScrollbarControl(
        "scrollbar_id",
        rect,
        axis=LayoutAxis.VERTICAL,
        min_value=0,
        max_value=1000,
        current_value=0,
        on_change=on_scroll,
    )
)
```

### Button Group Control

Mutually exclusive selection (radio button behavior).

```python
from gui import ButtonGroupControl

group = parent.add(
    ButtonGroupControl(
        "group_id",
        rect,
        options=["Option A", "Option B", "Option C"],
        on_selection_change=lambda idx: print(f"Selected: {idx}"),
    )
)

group.selected_index = 1  # Set selection
idx = group.selected_index  # Read selection
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

A decorative border/frame that groups content visually.

```python
from gui import FrameControl

frame = parent.add(
    FrameControl("frame_id", rect, frame_type="box")
)

# Add controls inside the frame
label = frame.add(
    LabelControl("label", inner_rect, "Framed Content")
)
```

### Arrow Box Control

Clickable arrow buttons (used internally for scrollbars but can be used directly).

```python
from gui import ArrowBoxControl

up_arrow = parent.add(
    ArrowBoxControl(
        "up_arrow",
        rect,
        direction="up",
        on_click=lambda: print("Clicked up"),
    )
)
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

Application-level control panel (typically at top/bottom of screen). Configured separately via `GuiApplication`.

```python
# Task panel is created automatically by GuiApplication
# Configure it in your app setup:
app.configure_task_panel(
    height=64,
    x_position="bottom",  # "top" or "bottom"
    reveal_on_focus=True,
    auto_hide=True,
    auto_hide_timer_ms=3000,
    step_size=8,
)

# Add buttons to task panel
task_panel = app.get_task_panel("main")
button = task_panel.add(
    ButtonControl("task_btn", rect, "Task Button")
)
```

### Canvas Control

High-performance drawable surface for custom graphics and event handling.

```python
from gui import CanvasControl, GuiEvent

def on_canvas_event(event):
    if event.is_mouse_motion():
        print(f"Mouse at {event.pos}")
        return True  # Consume event
    return False

canvas = parent.add(
    CanvasControl(
        "canvas_id",
        rect,
        max_events=256,  # Event buffer size
    )
)

canvas.on_handle_event = on_canvas_event

# In your draw loop:
def draw_scene(surface, theme):
    canvas.draw(surface, theme)
    # Canvas surfaces are cleared each frame
    canvas_surface = canvas.get_graphics_surface()
    # Draw custom content to canvas_surface
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

# Bind keys to actions
app.actions.bind_key(pygame.K_PLUS, "zoom_in", scene="main")
app.actions.bind_key(pygame.K_MINUS, "zoom_out", scene="main")

# Bind to specific windows
window = app.get_active_window(scene="main")
app.actions.bind_key_to_widget(pygame.K_RETURN, "activate", widget=window)
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

```python
from gui import FocusManager

# Get the active focus manager for a scene
focus_manager = app.get_focus_manager("main")

# Query focus
current = focus_manager.current()  # Currently focused widget
# Returns None if no widget is focused

# Set focus programmatically
focus_manager.set_focus_to(widget)

# Clear focus
focus_manager.clear_focus()

# Query widget properties
is_visible = focus_manager.is_widget_visible(widget)
is_focusable = focus_manager.is_widget_focusable(widget)
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

Windows are floating containers managed by the application.

```python
# Get active window in scene
window = app.get_active_window(scene="main")

# Get all windows
windows = app.get_all_windows(scene="main")

# Query window state
is_active = window.is_active()
rect = window.get_window_rect()
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

# Subscribe to changes
def on_count_changed(new_value):
    print(f"Count changed to {new_value}")

count.subscribe(on_count_changed)

# Update value
count.set(5)  # Triggers subscriber

# Create a presentation model (groups related values)
class SceneViewModel(PresentationModel):
    def __init__(self):
        super().__init__()
        self.zoom = ObservableValue(1.0)
        self.rotation = ObservableValue(0.0)
        self.is_playing = ObservableValue(False)

view_model = SceneViewModel()
view_model.zoom.subscribe(lambda z: print(f"Zoom: {z}"))
view_model.is_playing.subscribe(lambda playing: print(f"Playing: {playing}"))

# Update values
view_model.zoom.set(2.0)
view_model.is_playing.set(True)
```

## Canvas and Custom Drawing

The `CanvasControl` provides a drawable surface for custom graphics and interactive content.

```python
from gui import CanvasControl

def on_canvas_draw(canvas, surface, theme):
    # Draw custom content
    pygame.draw.circle(surface, (255, 0, 0), (100, 100), 50)

def on_canvas_event(event):
    if event.is_mouse_down():
        print(f"Clicked at {event.pos}")
        return True  # Consume event
    return False

canvas = parent.add(
    CanvasControl("canvas_id", rect, max_events=256)
)

# Bind event handler
canvas.on_handle_event = on_canvas_event

# Bind draw handler
canvas.on_draw = on_canvas_draw

# In main loop, events posted to canvas are accessible via:
for event in canvas.get_events():
    handle_canvas_event(event)

# Clear canvas (done automatically each frame)
canvas.clear_events()
```

## Task Panel Configuration

The task panel is a special control area (usually at top or bottom) for application-level actions.

```python
from gui import TaskPanelControl

# Configure task panel in app initialization
app.configure_task_panel(
    height=64,  # Height in pixels
    x_position="bottom",  # "top" or "bottom"
    reveal_on_focus=True,  # Show when mouse approaches edge
    auto_hide=True,  # Hide after inactivity
    auto_hide_timer_ms=3000,  # Milliseconds before hiding
    step_size=8,  # Animation step size in pixels
)

# Get task panel to add controls
task_panel = app.get_task_panel("main")

button = task_panel.add(
    ButtonControl("exit_btn", rect, "Exit", on_click=app.quit)
)

button.set_accessibility(role="button", label="Exit application")
```

## Themes and Styling

Customize appearance using `ColorTheme` and font roles.

```python
from gui import ColorTheme, BuiltInGraphicsFactory

# Create a custom theme
theme = ColorTheme(
    factory=BuiltInGraphicsFactory(),
    background=(30, 30, 30),  # Dark background
    foreground=(200, 200, 200),  # Light text
    accent=(100, 150, 255),  # Blue accent
    border=(80, 80, 80),  # Gray borders
)

# Register font roles
app.register_font_role(
    role_name="body",
    size=12,
    file_path="data/fonts/Ubuntu-Regular.ttf",
    system_name="arial",
    scene_name="main",
)

app.register_font_role(
    role_name="heading",
    size=24,
    file_path="data/fonts/Ubuntu-Bold.ttf",
    system_name="arial",
    scene_name="main",
)

# Apply styling to controls
app.style_label(label, size=12, role="body")
app.style_button(button, role="primary")
```

## Advanced Patterns

### Cross-Part Communication via Messaging

Parts can publish and subscribe to messages.

```python
from shared.part_lifecycle import Part

class ProducerPart(Part):
    def on_update(self, host):
        # Publish a message
        self.send_message({
            "topic": "data_update",
            "data": {"value": 42}
        })

class ConsumerPart(Part):
    def on_update(self, host):
        # Consume messages
        while self.has_messages():
            payload = self.pop_message()
            if payload.get("topic") == "data_update":
                print(f"Received data: {payload['data']}")
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

The `Timers` service allows scheduling one-shot and repeating timers per scene.

```python
# Get timers for a scene
timers = app.get_scene_timers("main")

# Schedule a one-shot timer
def on_timer_1000ms():
    print("1 second elapsed")

timers.set_timer(
    key="my_timer",
    duration_ms=1000,
    callback=on_timer_1000ms,
    repeat=False,  # One-shot
)

# Schedule a repeating timer
timers.set_timer(
    key="repeating",
    duration_ms=500,
    callback=lambda: print("Repeating every 500ms"),
    repeat=True,
)

# Cancel a timer
timers.clear_timer("my_timer")
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
