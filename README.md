[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

# gui_do

Architecture-first pygame GUI framework focused on clean interaction patterns, and composable feature architecture.

## Quick Start

### Installation

```bash
# Install runtime dependencies
pip install pygame numpy
```

### Run the Demo

```bash
python gui_do_demo.py
```

You'll see an interactive demo with two feature windows and a screen backdrop feature:
- **Bouncing Circles Backdrop**: Cached random circles are composed in screen preamble and animated in screen postamble with edge-bounce motion
- **Life**: Conway's Game of Life simulation with drag-pan, click-to-toggle cells, and zoom controls
- **Mandelbrot**: Real-time Mandelbrot renderer with iterative/recursive modes and split-canvas visualization

Backdrop/pristine defaults:
- Scene pristine state defaults to a solid black surface per scene, so `set_pristine(...)` is optional.
- Calling `GuiApplication.set_pristine(...)` still overwrites that same scene backing surface.
- `WindowControl` defaults to black pristine backing (`use_frame_backdrop=False`), and can opt into legacy frame visuals with `use_frame_backdrop=True`.

Font roles currently defined by the framework and demo:
- `body`: framework default body/control text, `Ubuntu-B.ttf`, 16 px
- `title`: framework default window-title text, `Gimbot.ttf`, 14 px, bold
- `display`: framework default large display text, `Gimbot.ttf`, 72 px, bold
- `part.life_simulation.window_title`: Life part window title bar, `Gimbot.ttf`, 14 px, bold
- `part.life_simulation.control`: Life part button/toggle text, `Ubuntu-B.ttf`, 16 px
- `part.life_simulation.annotation`: Life part label text such as the zoom label, `Ubuntu-B.ttf`, 16 px
- `part.mandelbrot.window_title`: Mandelbrot part window title bar, `Gimbot.ttf`, 14 px, bold
- `part.mandelbrot.control`: Mandelbrot part button text, `Ubuntu-B.ttf`, 16 px
- `part.mandelbrot.caption`: Mandelbrot part help/caption text, `Ubuntu-B.ttf`, 14 px
- `part.mandelbrot.status`: Mandelbrot part status line text, `Ubuntu-B.ttf`, 16 px
- `screen.main.task_panel.control`: scene-owned task panel control text for `Quit`, `Life`, and `Mandelbrot`, `Ubuntu-B.ttf`, 16 px

Typography ownership model:
- Parts register and own their own namespaced font roles during build.
- Scene-level UI that is not part-owned registers screen-owned roles, such as the task panel controls.
- Controls render from explicit font-role properties instead of relying on runtime font-switch commands.

### Minimal Runnable Example

```python
import pygame
from pygame import Rect
from gui import GuiApplication, PanelControl, ButtonControl, LabelControl

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My App")

# Initialize the app
app = GuiApplication(screen)
screen_rect = screen.get_rect()
app.layout.set_anchor_bounds(screen_rect)
app.create_scene("main")
app.switch_scene("main")

# Build a simple scene
root = app.add(
    PanelControl("root", Rect(0, 0, screen_rect.width, screen_rect.height)),
    scene_name="main",
)

label = root.add(
    LabelControl("label", Rect(10, 10, 300, 30), text="Hello, gui_do!"),
)
app.style_label(label, size=18, role="body")

def on_quit():
    app.quit()

button = root.add(
    ButtonControl("quit", Rect(10, 50, 100, 30), text="Quit"),
)
button.set_on_click(on_quit)

app.actions.register_action("exit", lambda _event: (app.quit() or True))
app.actions.bind_key(pygame.K_ESCAPE, "exit", scene="main")

# Run the app through gui_do-managed lifecycle
app.run(target_fps=60)

pygame.quit()
```

## Contributing

### Development Setup

1. Clone the repository and navigate to the project directory
2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # or
   source venv/bin/activate      # On macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install pygame numpy
   ```

For CI parity (includes coverage tooling used by GitHub Actions):
```bash
pip install -r requirements-ci.txt
```

### Running Tests

Run all tests:
```bash
python -m unittest discover tests -v
```

Run specific test suites:
```bash
# Pointer capture contracts
python -m unittest tests.test_pointer_capture_contracts -v

# Architecture boundaries
python -m unittest tests.test_boundary_contracts tests.test_public_api_exports tests.test_architecture_boundary_docs_contracts -v

# Demo functionality
python -m unittest tests.test_gui_do_demo_life_runtime tests.test_gui_do_demo_presentation_model tests.test_demo_parts_gui_portability tests.test_bouncing_circles_demo_part -v
```

### Code Style

- **One primary class per module**: Each module contains exactly one main public class.
- **Folder hierarchy reflects responsibility**: The `gui/` folder structure mirrors GUI component categories (controls, layout, core, app, theme).
- **Explicit imports**: Demo entrypoints import from `gui` root exports only, not from internal submodules.
- **Part-based composition**: Features are implemented as `Part` subclasses with standardized lifecycle hooks.
- **Strict API boundaries**: The `gui/` package does not depend on `demo_parts/`; the demo uses `gui` exclusively.

### Architecture & Design Rules

These constraints ensure maintainability and prevent common GUI bugs:

- **Pointer capture owns drag behavior**: When a control starts a drag, it acquires a lock area via `PointerCapture`. All subsequent motion uses locked coordinates only.
- **Slider/scrollbar never reposition pointer on release**: This prevents cursor drift at the end of drags.
- **Release ends capture only**: No cursor reconciliation or mutation logic runs during release.
- **Normalized event dispatch**: All raw pygame events are normalized to canonical `GuiEvent` objects at framework ingress.
- **Pristine fallback defaults**: Scene/window pristine restore paths are valid without image loading; explicit pristine assignment remains an overwrite operation.

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
- Boundary scope for demo entrypoints is `*_demo.py` (excluding `_pre_rebase*_demo.py` archives).
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

## Tutorial: Building a Feature with the Life Simulation

This tutorial walks through the Life feature implementation to show how to build, compose, and integrate a feature into the gui_do framework.

### Overview: The Part Lifecycle

Every feature in gui_do is a `Part` subclass. Parts follow a standardized lifecycle:

1. **`build(demo)`**: Create all UI controls and wire event handlers
2. **`bind_runtime(demo)`**: Connect runtime services (scheduler, timers, event bus)
3. **`configure_accessibility(demo, tab_index_start)`**: Set up keyboard navigation and accessibility metadata
4. **`on_update(demo)`**: Process cross-part messages and state updates (called every frame by `app.update()`)
5. **`shutdown_runtime(demo)`** (optional): Cleanup when the app shuts down

### Step 1: Define Your Feature Class

```python
from shared.part_lifecycle import Part

class LifeSimulationFeature(Part):
    """Conway's Game of Life with interactive pan, zoom, and cell toggling."""

    def __init__(self) -> None:
        super().__init__("life_simulation")  # Unique name for messaging
        self.life_cells = set()
        self.life_origin = [0.0, 0.0]
        self.life_cell_size = 12
        self.demo = None
        self.window = None
        self.canvas = None
        # ... other state
```

### Step 2: Build UI Controls

The `build()` method creates and configures all UI elements:

```python
def build(self, demo) -> None:
    """Build the Life feature UI using the application's configured UI types."""
    ui = demo.app.read_part_ui_types()

    # Create the window that will contain Life controls
    self.window = demo.root.add(
        ui.window_control_cls(
            "life_window",
            Rect(100, 100, 600, 400),
            title="Life Simulation",
            use_frame_backdrop=True,
        )
    )

    # Create the canvas for rendering the game grid
    self.canvas = self.window.add(
        ui.canvas_control_cls(
            "life_canvas",
            Rect(0, 0, 500, 350),
        )
    )

    # Add control buttons
    self.reset_button = self.window.add(
        ui.button_control_cls(
            "life_reset",
            Rect(10, 360, 100, 30),
            text="Reset",
            on_click=self._on_reset_clicked,
        )
    )

    # Add a slider for zoom control
    self.zoom_slider = self.window.add(
        ui.slider_control_cls(
            "life_zoom",
            Rect(120, 360, 200, 30),
            LayoutAxis.HORIZONTAL,
            1,
            20,
            value=5,
            on_change=self._on_zoom_slider_changed,
        )
    )
```

### Step 3: Bind Runtime Services

The `bind_runtime()` method connects to application services like the scheduler:

```python
def bind_runtime(self, demo) -> None:
    """Bind scheduler/runtime services required after scene construction."""
    if self.scheduler is None:
        self.scheduler = demo.app.get_scene_scheduler("main")
    self.scheduler.set_message_dispatch_limit(256)
```

### Step 4: Set Up Accessibility

The `configure_accessibility()` method assigns tab order and ARIA labels:

```python
def configure_accessibility(self, demo, tab_index_start: int) -> int:
    """Assign accessibility metadata and tab order for Life controls."""
    controls = [
        self.reset_button,
        self.zoom_slider,
    ]
    roles = [
        ("button", "Reset life board"),
        ("slider", "Life zoom"),
    ]
    next_index = int(tab_index_start)
    for control, (role, label) in zip(controls, roles):
        if control is None:
            continue
        control.set_tab_index(next_index)
        control.set_accessibility(role=role, label=label)
        next_index += 1
    return next_index
```

### Step 5: Handle Events and State

The `on_update()` hook runs every frame and processes events:

```python
def on_update(self, host) -> None:
    """Run Life simulation update and consume canvas events."""
    # Drain canvas events (mouse clicks, drags, wheel)
    while True:
        event = self.canvas.read_event()
        if event is None:
            break
        self._handle_canvas_event(event)

    # Apply Conway's Game of Life rules
    self._update_life()

    # Re-render the visible cells onto the canvas
    self._render_life(self.canvas)

def _handle_canvas_event(self, event) -> None:
    """Process canvas mouse events: drag to pan, click to toggle cells."""
    if event.is_mouse_motion():
        # Right-click drag pans the view
        if event.buttons[2]:  # Right mouse button
            self.life_origin[0] -= event.rel[0]
            self.life_origin[1] -= event.rel[1]

    elif event.is_mouse_down():
        # Left-click toggles a cell
        if event.button == 1:
            cell = self._screen_pos_to_cell(event.pos)
            if cell in self.life_cells:
                self.life_cells.remove(cell)
            else:
                self.life_cells.add(cell)

    elif event.is_mouse_wheel():
        # Scroll wheel zooms
        if event.wheel_delta > 0:
            self.life_cell_size = min(20, self.life_cell_size + 1)
        else:
            self.life_cell_size = max(1, self.life_cell_size - 1)

def _update_life(self) -> None:
    """Apply one generation of Conway's Game of Life."""
    neighbors_counts = {}
    for x, y in self.life_cells:
        for dx, dy in self.neighbours:
            nx, ny = x + dx, y + dy
            neighbors_counts[(nx, ny)] = neighbors_counts.get((nx, ny), 0) + 1

    new_cells = set()
    for cell, count in neighbors_counts.items():
        x, y = cell
        is_alive = cell in self.life_cells
        if (is_alive and count in (2, 3)) or (not is_alive and count == 3):
            new_cells.add(cell)

    self.life_cells = new_cells
```

### Step 6: Register and Connect the Feature

In your demo entrypoint, register the feature with the app:

```python
class GuiDoDemo:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((1920, 1080))
        self.app = GuiApplication(self.screen)

        # Create the feature
        self._life_feature = LifeSimulationFeature()

        # Register it with the app
        self.app.register_part(self._life_feature, host=self)

        # Build the scene
        self._build_main_scene()

        # Configure the feature's accessibility and bind runtime services
        self.app.configure_parts_accessibility(self, tab_index_start=3)
        self.app.bind_parts_runtime(self)

    def _build_main_scene(self) -> None:
        """Build the root scene container and call build() on all parts."""
        self.root = self.app.add(
            PanelControl("main_root", Rect(0, 0, 1920, 1080), draw_background=False),
            scene_name="main",
        )
        # This calls build() on all registered parts
        self.app.build_parts(self)
```

## API Lifecycle Usage

The gui_do framework uses a strict part-based lifecycle to manage feature composition and state. Understanding these hooks is essential for both building GUI apps and creating reusable features.

### GUI Application Lifecycle

The managed `app.run()` loop performs this flow internally:

```python
# After scene construction and runtime binding:
app.run(target_fps=60)
```

Internally, the managed loop processes pygame events, updates controls and parts,
draws the active scene, and presents the frame.

### Screen Lifecycle Composition

Use screen lifecycle callbacks when a feature needs per-frame behavior at the screen level
(for example backdrop composition before draw, or motion updates after update).

`GuiApplication.set_screen_lifecycle(...)` sets the base callbacks.

`GuiApplication.chain_screen_lifecycle(...)` appends callbacks on top of the base and returns
a dispose function that removes just that chained layer.

```python
# Base lifecycle (optional)
app.set_screen_lifecycle(
    preamble=base_preamble,
    event_handler=base_screen_handler,
    postamble=base_postamble,
)

# Add a composed layer (for example, from a Part.bind_runtime)
dispose = app.chain_screen_lifecycle(
    preamble=feature_preamble,
    event_handler=feature_screen_handler,
    postamble=feature_postamble,
)

# Later, remove only this layer
dispose()
```

Chaining semantics:
- Preamble order: base first, then chained layers in registration order
- Event-handler order: base first, then chained layers until one returns `True`
- Postamble order: base first, then chained layers in registration order
- Calling `set_screen_lifecycle(...)` resets base callbacks and clears chained layers

### Part Lifecycle Hooks

Every `Part` subclass can implement these lifecycle methods (all optional):

#### `build(host)`

**Purpose**: Create all UI controls and wire event handlers. This is called once after the part is registered.

**When it runs**: Called from `GuiApplication.build_parts(host)` during scene construction.

**Signature**:
```python
def build(self, host) -> None:
    # Create controls under an existing container/window
    self.button = self.window.add(ButtonControl(..., on_click=self._on_button_clicked))
```

**Common patterns**:
- Create root scene nodes via `host.app.add(...)`, then attach child controls with `container.add(...)`
- Pass callbacks in constructors when available, or use current setters such as `set_on_click()`
- Store references to controls as instance attributes for later access

#### `bind_runtime(host)`

**Purpose**: Connect to runtime services that exist after scene construction (scheduler, event bus, timers).

**When it runs**: Called from `GuiApplication.bind_parts_runtime(host)` after `build()` completes.

**Signature**:
```python
def bind_runtime(self, host) -> None:
    self.scheduler = host.app.get_scene_scheduler("main")
    self.event_bus = host.app.get_event_bus()
    self.scheduler.subscribe(self._on_task_complete)
```

**Why separate from build?**: Some services are not available until the scene is fully constructed.

#### `configure_accessibility(host, tab_index_start: int) -> int`

**Purpose**: Set accessibility metadata (ARIA roles, labels) and keyboard navigation tab order.

**When it runs**: Called from `GuiApplication.configure_parts_accessibility(host, num_controls)`.

**Returns**: The next available tab index (for coordinating across multiple parts).

**Signature**:
```python
def configure_accessibility(self, host, tab_index_start: int) -> int:
    controls = [self.button, self.slider]
    roles = [("button", "Do action"), ("slider", "Adjust value")]
    next_index = tab_index_start
    for control, (role, label) in zip(controls, roles):
        control.set_tab_index(next_index)
        control.set_accessibility(role=role, label=label)
        next_index += 1
    return next_index
```

#### `on_update(host)`

**Purpose**: Update feature state, process events, and publish messages every frame.

**When it runs**: Called from `GuiApplication.update()` after the UI engine has processed input and updated all controls.

**Signature**:
```python
def on_update(self, host) -> None:
    """Drain events, update state, publish messages."""
    # Process control events
    while True:
        event = self.canvas.read_event()
        if event is None:
            break
        self._handle_event(event)

    # Update feature state
    self._update_simulation()

    # Publish cross-part messages
    self.send_message("other_part", {"status": "done"})

    # Or consume messages from other parts
    while self.has_messages():
        msg = self.pop_message()
        self._handle_cross_part_message(msg)
```

**Common patterns**:
- Drain canvas events with `canvas.read_event()` (returns `None` when the queue is empty)
- Update internal state (simulation, calculations)
- Render to canvas with `canvas.fill()`, `canvas.draw_line()`, etc.
- Publish status via `self.send_message(target_part_name, message_dict)`
- Consume cross-part messages with `self.pop_message()`

#### `shutdown_runtime(host)` (optional)

**Purpose**: Clean up resources when the app shuts down.

**When it runs**: Called from `GuiApplication.shutdown()`.

**Signature**:
```python
def shutdown_runtime(self, host) -> None:
    """Clean up resources."""
    if self.worker_thread:
        self.worker_thread.join(timeout=1)
    if self.file_handle:
        self.file_handle.close()
```

### Cross-Part Messaging

Parts can publish messages to other parts:

```python
# In one part, publish a status message
self.send_message("mandelbrot_part", {
    "topic": "life_status",
    "generation": 42,
    "population": 1234,
})

# In another part, consume it
def on_post_frame(self, host) -> None:
    while self.has_messages():
        msg = self.pop_message()
        if msg.get("topic") == "life_status":
            generation = msg.get("generation")
            population = msg.get("population")
            self._update_display(generation, population)
```

### Control Event Handling

Individual controls emit events that parts can consume:

```python
# Slider value changes (strict reason-aware mode)
def _on_slider_change(self, value, reason):
    print(f"Slider now {value} via {reason.value}")

slider = self.window.add(
    SliderControl(..., on_change=self._on_slider_change, on_change_mode="reason-required")
)

# Button clicks
def _on_button_click(self):
    print("Button clicked")

button = self.window.add(ButtonControl(..., on_click=self._on_button_click))

# Canvas events
while True:
    event = self.canvas.read_event()
    if event is None:
        break
    if event.is_mouse_down():
        print(f"Clicked at {event.pos}")
    elif event.is_mouse_motion():
        print(f"Mouse moved by {event.rel}")
```

### Scene Management

Each app can have multiple scenes, and the framework routes events and updates to the active scene:

```python
# Create a scene
app.create_scene("main")
app.create_scene("settings")

# Switch scenes
app.switch_scene("settings")

# Access the active scene
active_scene = app.get_active_scene()

# Get a scheduler for a specific scene
scheduler = app.get_scene_scheduler("main")
```

## Addendum: Typing Legend

This section documents the type annotations and patterns used throughout gui_do.

### Core Types

- **`UiNode`**: Base class for all GUI controls. All controls inherit from `UiNode`.
- **`Control`**: A `UiNode` that can receive events and has interactive behavior (buttons, sliders, etc.).
- **`Container`**: A `UiNode` that can have children (panels, windows, frames).
- **`Part`**: A composable feature that implements lifecycle hooks (`build`, `bind_runtime`, `on_update`).
- **`GuiEvent`**: Normalized pygame event wrapper with semantic methods like `is_mouse_down()`, `is_key_down()`.
- **`Scene`**: A top-level container that manages a graph of UI nodes.

### Event Types

- **`EventType`**: Enum of event kinds (MOUSE_DOWN, MOUSE_UP, MOUSE_MOTION, KEY_DOWN, KEY_UP, WHEEL).
- **`EventPhase`**: Enum of event propagation phases (CAPTURE, TARGET, BUBBLE).
- **`GuiEvent`**: Canonical event object with properties:
  - `event.pos`: (int, int) - normalized mouse position
  - `event.rel`: (int, int) - relative motion since last frame
  - `event.key`: int - pygame key code
  - `event.unicode`: str - character representation
  - `event.wheel_delta`: int - scroll delta (+1 / -1)
  - Methods: `is_mouse_down()`, `is_key_down(key)`, `is_mouse_wheel()`, etc.

### Callback Signatures

- **`OnClickCallback`**: `Callable[[GuiEvent], bool]` - returns True to consume event
- **`OnValueChangeCallback`**: `Callable[[T], None] | Callable[[T, ValueChangeReason], None]` - value-only (compat mode) or value+reason callback
- **`OnVisibilityChangeCallback`**: `Callable[[bool], None]` - (is_visible)
- **`OnWindowFocusCallback`**: `Callable[[bool], None]` - (is_focused)

### Layout & Geometry

- **`Rect`**: pygame.Rect - position and size (x, y, width, height)
- **`LayoutAxis`**: Enum (HORIZONTAL, VERTICAL) - axis for layout calculations
- **`AnchorPoint`**: Enum (TOP_LEFT, CENTER, BOTTOM_RIGHT, etc.) - anchor reference for positioning

### Collections & Containers

- **`OrderedDict[str, Part]`**: Ordered registry of parts for deterministic iteration
- **`Dict[str, Control]`**: Named control lookup tables
- **`List[UiNode]`**: Child node lists (order matters for z-order/tab order)
- **`Set[Tuple[int, int]]`**: Cell coordinates (used in Life simulation)

### Observable Values

- **`ObservableValue[T]`**: Wrapper that publishes change events
  - `value.get() -> T`
  - `value.set(new_value: T) -> None`
  - `value.subscribe(callback: Callable[[T, T], None]) -> None`

### Task Scheduler

- **`TaskEvent`**: Event emitted by `TaskScheduler`
  - `event.task_id`: str - unique task identifier
  - `event.is_complete()`: bool - True if task finished
  - `event.is_failure()`: bool - True if task failed
  - `event.result`: Any - task result (if complete)
  - `event.failure_reason`: str - error message (if failed)

- **`TaskScheduler`**: Service for background task management
  - `schedule_task(task_id, task_fn, callback=None) -> None`
  - `await_task(task_id, timeout_ms=None) -> TaskEvent`
  - `has_task(task_id) -> bool`

### Color & Theme

- **`ColorTheme`**: Configuration object
  - `color_theme.get_color(key: str) -> Color` - lookup named color
  - `color_theme.graphics_factory` - factory for creating graphics objects

### Pointer Capture

- **`PointerCapture`**: Manages drag lock areas
  - `capture.acquire(node, lock_rect: Rect) -> bool`
  - `capture.release(node) -> bool`
  - `capture.is_captured(node) -> bool`

## Major Concepts Explained

### 1. The Part System

A **Part** is a composable unit of functionality. Parts enable feature encapsulation and standardized lifecycle management.

**Why Parts?**
- Decouples features from the main application code
- Allows multiple independent demos to coexist
- Standardizes how features integrate with the framework
- Enables cross-part messaging for loosely-coupled communication

**Part Anatomy**:
```python
from shared.part_lifecycle import Part

class MyFeature(Part):
    def __init__(self):
        super().__init__("my_feature")  # Unique name
        # Feature state

    def build(self, demo):
        # Create UI
        pass

    def bind_runtime(self, demo):
        # Connect services
        pass

    def configure_accessibility(self, demo, tab_index_start):
        # Set up keyboard navigation
        return next_tab_index

    def on_update(self, demo):
        # Update every frame
        pass
```

### 2. Event System & Normalization

Raw pygame events are error-prone and vary in structure. The gui_do framework normalizes all events to canonical `GuiEvent` objects.

**Normalization Process**:
1. Raw pygame event enters `GuiApplication.process_event(event)`
2. `EventManager` normalizes to `GuiEvent`
3. Framework routes through `ActionManager`, `FocusManager`, then to individual controls
4. Controls consume or propagate via `event.stop_propagation()` / `event.prevent_default()`

**Event Routing Phases**:
- **CAPTURE**: Event descends from root to target (rarely used)
- **TARGET**: Event reaches the target control
- **BUBBLE**: Event propagates back up to root (default)

### 3. Pointer Capture & Drag Lock

One of gui_do's key features is reliable drag handling without cursor drift.

**The Problem**: During a drag, the cursor can jump if logic reconciles pointer positions incorrectly, especially on release.

**The Solution: Pointer Capture**:
1. When a control starts a drag (e.g., slider handle), it acquires a **lock area** via `PointerCapture`
2. All subsequent motion uses coordinates from the locked area **only** (ignoring cursor position outside)
3. On release, capture simply ends; no cursor mutation occurs
4. This removes drift bugs entirely

**In Code**:
```python
# Slider acquires capture during left-press on handle
capture_rect = Rect(handle.x - 10, handle.y - 10, handle.width + 20, handle.height + 20)
app.pointer_capture.acquire(self, capture_rect)

# Motion handler uses captured coordinates
if app.pointer_capture.is_captured(self):
    pos = app.input_state.pos  # Locked position, safe to use
    self._update_slider_from_position(pos)

# Release just ends capture; no cursor repositioning
app.pointer_capture.release(self)
```

### 4. Scheduler & Asynchronous Tasks

The `TaskScheduler` enables background work without blocking the UI.

**Use Cases**:
- Render-intensive computations (Mandelbrot set)
- Long-running I/O (file loading, network requests)
- Deferred UI updates

**Pattern**:
```python
def launch_render(self):
    def render_task():
        # Long-running computation
        return mandelbrot_pixels

    callback = lambda event: self._on_render_complete(event)
    self.scheduler.schedule_task("render_1", render_task, callback)

def _on_render_complete(self, event):
    if event.is_failure():
        print(f"Render failed: {event.failure_reason}")
    else:
        pixels = event.result
        self._apply_pixels_to_canvas(pixels)
```

### 5. Scene & Window Management

Gui_do supports multiple scenes and window tiling.

**Scenes**: Each scene is an independent graph of UI nodes. The app can switch between scenes (e.g., "main" vs "settings").

**Windows**: Within a scene, `WindowControl` objects are top-level draggable containers. The framework can automatically tile windows in a grid.

**Tiling**: Call `app.configure_window_tiling(gap=16, padding=16, avoid_task_panel=True)` to enable automatic window arrangement.

**Window Focus**: Only one window is "active" at a time (receives keyboard input). Use `app.focus.request_focus(window)` to change which window is active.

### 6. Layout Management

The `LayoutManager` handles control positioning and sizing.

**Anchoring**: Controls can be anchored relative to their parent or the screen:
```python
app.layout.anchor(control, point=AnchorPoint.CENTER, offset=(0, 0))
```

**Grid Layout**: Arrange controls in a grid:
```python
children = [button1, button2, button3, button4]
app.layout.grid(children, cols=2, gap=10, padding=5)
```

**Linear Layout**: Arrange controls in a row or column:
```python
buttons = [save_btn, cancel_btn, delete_btn]
app.layout.linear(buttons, axis=LayoutAxis.HORIZONTAL, gap=5)
```

### 7. Control Lifecycle

Every control goes through these phases:

1. **Creation**: Create root scene nodes with `app.add(...)`, then attach child controls with `container.add(...)`
2. **Attachment**: Control is added to scene graph
3. **Event Input**: Control receives events during `app.process_event()`
4. **Update**: Control's internal state updates during `app.update()`
5. **Rendering**: Control draws itself during `app.draw()`
6. **Visibility/Focus**: Control responds to visibility and focus changes
7. **Removal**: Control is detached and cleaned up

**Visibility**: Hidden controls don't receive events and aren't rendered:
```python
control.visible = False  # Hide
control.visible = True   # Show
```

**Focus**: Only the focused control (or its active window) receives keyboard input:
```python
app.focus.request_focus(control)
is_focused = control.focused
```

### 8. Value Change Reasons

When a control's value changes, the callback can receive a `ValueChangeReason` to distinguish input sources:

```python
def on_slider_change(value, reason):
    if reason == ValueChangeReason.MOUSE_DRAG:
        print("User dragged slider")
    elif reason == ValueChangeReason.KEYBOARD:
        print("User changed value from keyboard")
    elif reason == ValueChangeReason.WHEEL:
        print("User changed value via wheel")
    elif reason == ValueChangeReason.PROGRAMMATIC:
        print("Code changed value via API")
```

This allows features to react differently based on the change source.

### 9. Color Theme & Graphics Factory

The framework uses pluggable rendering via `ColorTheme`:

```python
theme = ColorTheme()
theme.set_color("button_bg", pygame.Color(50, 50, 50))
theme.set_color("button_fg", pygame.Color(200, 200, 200))
theme.graphics_factory = BuiltInGraphicsFactory()

app = GuiApplication(screen, theme=theme)
```

Custom rendering is possible by providing a `graphics_factory` with custom draw functions.

---

## Architecture Documentation

For detailed specifications, see:

- **[docs/public_api_spec.md](docs/public_api_spec.md)**: Complete list of public exports and API contracts
- **[docs/event_system_spec.md](docs/event_system_spec.md)**: Event normalization and routing semantics
- **[docs/architecture_boundary_spec.md](docs/architecture_boundary_spec.md)**: Package boundaries between framework and demo code
