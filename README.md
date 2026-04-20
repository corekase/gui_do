# gui_do

[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

`gui_do` is a pygame-based GUI toolkit that is currently best used as a practical framework for building interactive desktop UIs inside a game loop.

This README is an implementation-focused tutorial for what exists now, not full API reference documentation.

Each release includes a link to a video demonstration as it was at the time.

## What You Get Right Now

- A managed GUI loop (`Engine`) that integrates events, timers, async tasks, and rendering.
- Multiple GUI contexts (`StateManager`) so you can switch between complete interfaces.
- A central manager (`GuiManager`) that creates widgets and routes events.
- Windowed and screen-level widgets.
- Common controls: buttons, toggles, button groups, sliders, scrollbars, labels, images, frames, arrow boxes, canvases, and bottom task panels.
- A task scheduler for background computation with UI-thread progress callbacks.

## Type Signature Legend

The method signatures in this README use standard Python typing forms:

- `Optional[T]`: value is either `T` or `None`.
- `Union[A, B]`: value may be either `A` or `B`.
- `Tuple[A, B, ...]`: fixed-size ordered tuple with typed positions.
- `List[T]`: mutable list of `T` values.
- `Callable[[A, B], R]`: callable taking `A` and `B`, returning `R`.
- `Hashable`: any value usable as a dictionary key (for example `str`, `int`, `tuple`).
- `Rect`: `pygame.Rect`.

## Quick Start

## 1. Install dependencies

```bash
pip install pygame numpy
```

## Testing

Run the full unit test suite locally from repo root:

```bash
python -m unittest discover -s tests -v
```

Run tests with coverage (line + branch) locally:

```bash
python -m pip install coverage
python -m coverage run --rcfile=.coveragerc -m unittest discover -s tests -v
python -m coverage report -m
python -m coverage xml -o coverage.xml
```

CI runs tests under coverage and uploads `coverage.xml` artifacts for each matrix job via:

- `.github/workflows/unittest.yml`

## Contributing

Before opening a PR, run the local test suite and confirm it passes:

```bash
python -m unittest discover -s tests -v
```

Please include any new tests needed for behavior changes or bug fixes.

## 2. Project layout expected by gui_do

The toolkit expects assets under `data/`:

- `data/fonts/`
- `data/images/`
- `data/cursors/`

The demo uses this directly (fonts, `*.ttf` files, and images, example `backdrop.jpg`, and cursors, example `cursor.png`).

Resource loading resolves from the repository `data/` folder, so it is independent of your current working directory.

## 3. Minimal runnable setup

When calling `gui.configure_fonts(**fonts: Tuple[str, int]) -> List[Tuple[str, str, int]]`, you must provide both `titlebar` and `normal` font entries because the GUI uses those names internally.

```python
import pygame
from pygame import Rect
from gui import GuiManager, Engine, StateManager, Event, ButtonStyle

pygame.init()
screen = pygame.display.set_mode((1280, 720))

gui = GuiManager(screen, task_panel_enabled=False)
gui.configure_fonts(
    normal=("Gimbot.ttf", 16),
    titlebar=("Ubuntu-B.ttf", 14),
)
gui.graphics_factory.set_font("normal")
gui.set_pristine("backdrop.jpg")

def on_button():
    print("Clicked")

gui.button("hello", Rect(20, 20, 120, 28), ButtonStyle.Round, "Hello", on_activate=on_button)

def on_screen_event(event):
    if event.type == Event.Quit:
        state.set_running(False)

gui.set_screen_lifecycle(event_handler=on_screen_event)

state = StateManager()
state.register_context("main", gui)
state.switch_context("main")
Engine(state).run()
```

## Mental Model

If you understand these 4 parts, the rest of the package makes sense.

## 1. Engine: frame orchestration

`Engine.run() -> None` performs the frame cycle:

1. Screen/window preamble callbacks.
2. Input polling and dispatch.
3. Scheduler update (task completion + progress message dispatch).
4. Screen/window postamble callbacks.
5. Render + display flip.

This means your callbacks and UI updates happen on the main thread in a predictable order each frame.

## 2. StateManager: multi-GUI app states

You can register multiple `GuiManager` instances as named contexts (for example, `gui1` and `gui2` in the demo) and switch at runtime.

Important behavior: when context switches, mouse position is carried over.

## 3. GuiManager: your main API surface

You mostly program through `GuiManager`.

It owns:

- Widget/window registration.
- Event routing.
- Renderer.
- Scheduler (`gui.scheduler`) and timers (`gui.timers`).
- Layout helper (`set_grid_properties` and `gridded`).

## 4. Window vs screen widgets

- If there is no active window, created widgets become screen-level widgets.
- After creating a window, subsequent widgets are parented to that active window.
- Toggling `window.visible` also updates active-window state: setting `True` makes that window active, setting `False` removes it from active selection.
- Keyboard input follows active-window focus: key events go to the active window handler, and if no window is active they go to the screen lifecycle event handler.

This is a key behavior used by the demo when building each window section.

## Public API Entry Points

From `gui` package import:

- `GuiManager`
- `Engine`
- `StateManager`
- `TaskPanelSettings`
- `MouseInputState`
- `colours`
- `Event`
- `CanvasEvent`
- `ButtonStyle`

## Colours

Importing `colours` is optional. You only need it if you want direct access to the GUI color dictionary values.

Dictionary keys and values:

- `colours['full']`: `(255, 255, 255)`
- `colours['light']`: `(0, 200, 200)`
- `colours['medium']`: `(0, 150, 150)`
- `colours['dark']`: `(0, 100, 100)`
- `colours['none']`: `(0, 0, 0)`
- `colours['text']`: `(255, 255, 255)`
- `colours['highlight']`: `(238, 230, 0)`
- `colours['background']`: `(0, 60, 60)`

## Creating UI: Practical Pattern

The demo follows this sequence, which is a solid default:

1. Initialize pygame and display surface.
2. Create one or more `GuiManager` instances with font tuples.
3. Set screen lifecycle (`set_screen_lifecycle`).
4. Set backdrop with `set_pristine`.
5. Create widgets/windows through `GuiManager` factory methods.
6. Register contexts with `StateManager`.
7. Run `Engine`.

## Widget Factories You Will Use

All of these both create and register the widget:

- `gui.arrow_box(id: str, rect: Rect, direction: float, on_activate: Optional[Callable[[], None]] = None) -> ArrowBox`
- `gui.button(id: str, rect: Rect, style: ButtonStyle, text: Optional[str], on_activate: Optional[Callable[[], None]] = None) -> Button`
- `gui.button_group(group: str, id: str, rect: Rect, style: ButtonStyle, text: str) -> ButtonGroup`
- `gui.canvas(id: str, rect: Rect, backdrop: Optional[str] = None, on_activate: Optional[Callable[[], None]] = None, automatic_pristine: bool = False) -> Canvas`
- `gui.frame(id: str, rect: Rect) -> Frame`
- `gui.image(id: str, rect: Rect, image: str, automatic_pristine: bool = False, scale: bool = True) -> Image`
- `gui.label(position: Union[Tuple[int, int], Tuple[int, int, int, int]], text: str, shadow: bool = False, id: Optional[str] = None) -> Label`
- `gui.slider(id: str, rect: Rect, horizontal: bool, total_range: int, position: float = 0.0, integer_type: bool = False, notch_interval_percent: float = 5.0, wheel_positive_to_max: bool = False, wheel_step: Optional[float] = None) -> Slider`
- `gui.scrollbar(id: str, overall_rect: Rect, horizontal: bool, style: Literal["skip", "split", "near", "far"], params: Tuple[int, int, int, int], wheel_positive_to_max: bool = False) -> Scrollbar`
- `gui.toggle(id: str, rect: Rect, style: ButtonStyle, pushed: bool, pressed_text: str, raised_text: Optional[str] = None) -> Toggle`
- `gui.window(title: str, pos: Tuple[int, int], size: Tuple[int, int], backdrop: Optional[str] = None, preamble: Optional[Callable[[], None]] = None, event_handler: Optional[Callable[[BaseEvent], None]] = None, postamble: Optional[Callable[[], None]] = None) -> Window`

Task panel behavior is manager-owned (not a separate widget factory).

Constructor takes one task panel switch:

- `task_panel_enabled=True`

Configure the task panel with an immutable settings object:

```python
from gui import TaskPanelSettings

gui.set_task_panel_settings(
    TaskPanelSettings(
        panel_height=42,
        left=0,
        width=None,
        hidden_peek_pixels=6,
        auto_hide=True,
        animation_interval_ms=12.0,
        animation_step_px=5,
        backdrop_image="taskpanel.png",
    )
)
```

Example:

```python
gui.set_task_panel_settings(
    TaskPanelSettings(
        auto_hide=False,
    )
)

gui.task_panel.button("exit", Rect(10, 5, 70, 28), ButtonStyle.Angle, "Exit")
apps_button = gui.task_panel.button("gui2", gui.gridded(0, 0), ButtonStyle.Round, "Apps")
drawing_toggle = gui.task_panel.toggle("circles", gui.gridded(1, 0), ButtonStyle.Round, False, "Drawing")
```

Runtime task panel helpers on `GuiManager`:

- `gui.set_task_panel_lifecycle(preamble: Optional[Callable[[], None]] = None, event_handler: Optional[Callable[[BaseEvent], None]] = None, postamble: Optional[Callable[[], None]] = None) -> None`
- `gui.set_task_panel_enabled(enabled: bool) -> None`
- `gui.set_task_panel_auto_hide(auto_hide: bool) -> None`
- `gui.set_task_panel_hidden_peek_pixels(hidden_peek_pixels: int) -> None`
- `gui.set_task_panel_animation_step_px(animation_step_px: int) -> None`
- `gui.set_task_panel_animation_interval_ms(animation_interval_ms: float) -> None`
- `gui.set_task_panel_settings(settings: TaskPanelSettings) -> None`
- `gui.read_task_panel_settings() -> Dict[str, object]`

Task panel widget API surface:

- `gui.task_panel.arrow_box(...)`
- `gui.task_panel.button(...)`
- `gui.task_panel.button_group(...)`
- `gui.task_panel.canvas(...)`
- `gui.task_panel.frame(...)`
- `gui.task_panel.image(...)`
- `gui.task_panel.label(...)`
- `gui.task_panel.scrollbar(...)`
- `gui.task_panel.slider(...)`
- `gui.task_panel.toggle(...)`

The task panel widget API intentionally mirrors `GuiManager` widget constructors and intentionally excludes `window(...)`.

## Core Runtime API Reference

The sections above focus on practical usage. This section provides complete callable coverage for the core runtime classes.

## Engine API

- `Engine(state_manager: StateManager)`
- `engine.run() -> None`

## StateManager API

- `state.register_context(name: str, gui: GuiManager, replace: bool = False) -> GuiManager`
- `state.switch_context(name: str) -> GuiManager`
- `state.get_active_gui() -> Optional[GuiManager]`
- `state.set_running(running: bool) -> None`

## GuiManager Properties

- `gui.graphics_factory` (property)
- `gui.scheduler` (property)
- `gui.buffered` (read/write bool property)

## GuiManager Advanced Methods

- `gui.build_font_registry(**fonts: Tuple[str, int]) -> List[Tuple[str, str, int]]`
- `gui.load_fonts(fonts: Iterable[Tuple[str, str, int]]) -> None`
- `gui.hide_widgets(*widgets: Widget) -> None`
- `gui.show_widgets(*widgets: Widget) -> None`
- `gui.lower_window(window: Window) -> None`
- `gui.raise_window(window: Window) -> None`
- `gui.set_task_owner(task_id: Hashable, window: Optional[Window]) -> None`
- `gui.set_task_owners(window: Optional[Window], *task_ids: Hashable) -> None`
- `gui.get_mouse_input_state() -> MouseInputState`
- `gui.copy_graphic_area(surface: Surface, rect: Rect, flags: int = 0) -> Surface`

Mouse input state format:

- `state.position: Tuple[int, int]`
- `state.buttons: Tuple[bool, bool, bool]` in `(left, middle, right)` order

Example:

```python
mouse = gui.get_mouse_input_state()
x, y = mouse.position
left, middle, right = mouse.buttons
```

## Events and Callbacks

## GUI events

Your screen/window event handler receives framework events (`Event` enum), not raw pygame events.
Keyboard events (`Event.KeyDown` / `Event.KeyUp`) are routed to the current active window handler when one is active; if no window is active, they are routed to the screen lifecycle event handler.

Common ones:

- `Event.Widget`: `event.widget_id` tells you which widget activated.
- `Event.Group`: for button groups; includes `event.group` and `event.widget_id`.
- `Event.Task`: async task completion/failure event.
- `Event.KeyDown`, `Event.KeyUp`, `Event.Quit`.

Pattern used by the demo:

```python
def gui1_screen_event_handler(self, event):
    if event.type == Event.Widget:
        if event.widget_id == "exit":
            self.state_manager.set_running(False)
        elif event.widget_id == "gui2":
            self.state_manager.switch_context("gui2")
    elif event.type == Event.KeyDown:
        if event.key == K_ESCAPE:
            self.state_manager.set_running(False)
```

## Widget callback signatures

- `on_activate` callbacks are zero-arg callables: `def callback() -> None`.
- For canvases, `on_activate` should drain queued canvas events via `canvas.read_event() -> Optional[CanvasEventPacket]`.

## Canvas usage (from Life window in demo)

`Canvas` is an off-screen drawing surface plus an input event queue.

Key methods:

- `canvas.get_canvas_surface() -> Surface`
- `canvas.read_event() -> Optional[CanvasEventPacket]`
- `canvas.set_event_queue_limit(max_events: int) -> None`
- `canvas.set_overflow_handler(callback: Optional[Callable[[int, int], None]], *, strict: bool = False) -> None`
- `canvas.set_overflow_mode(mode: str) -> None` where `mode` is `'drop_oldest'` or `'reject_new'`
- `canvas.set_motion_coalescing(enabled: bool) -> None`

Overflow callback signature:

- `callback(dropped_now: int, total_dropped: int) -> None`

The demo uses canvas events for:

- Right-mouse drag panning (`MouseButtonDown`/`MouseMotion`/`MouseButtonUp`)
- Mouse wheel zoom (`MouseWheel`)

Important: if you do not consume events fast enough, older events are dropped when queue is full.

## Background Tasks and Timers

## Scheduler

Use `gui.scheduler` for background work.

- `add_task(task_id: Hashable, logic: Callable[..., object], parameters: Optional[object] = None, message_method: Optional[Callable[[object], None]] = None) -> None`
- `send_message(task_id: Hashable, parameters: object) -> None` from inside the task function
- `pop_result(task_id: Hashable, default: Optional[object] = None) -> Optional[object]` after completion
- `remove_tasks(*ids: Hashable) -> None`, `tasks_busy_match_any(*ids: Hashable) -> bool`

The Mandelbrot demo uses this heavily:

- Worker task computes regions.
- Task sends incremental draw payloads to main thread.
- UI applies payloads in a message callback.
- `Event.Task` is used for completion/failure handling (`TaskEvent.operation`, `TaskEvent.id`, `TaskEvent.error`).

## Threading and affinity rules

Current Python builds still have the GIL, but scheduler worker tasks should be treated as true concurrent producers and the GUI loop as the single consumer/owner of UI state.

- Only mutate widget/window/screen state from main-thread callbacks (screen/window lifecycle, widget handlers, scheduler message callbacks, and `Event.Task` handling).
- Worker task logic should not directly touch `GuiManager`, widgets, windows, renderer objects, or pygame surfaces.
- Worker tasks should communicate with the UI only through `scheduler.send_message(task_id: Hashable, parameters: object) -> None` and by returning a result consumed through task completion.
- Task messages, completion notifications, and task failures are queued and then applied on the frame thread during `scheduler.update() -> List[Hashable]`.
- Removing/re-adding the same task id is generation-protected: stale worker messages/completions/failures from earlier generations are discarded.

## Timers

`gui.timers.add_timer(id: Hashable, duration: float, callback: Callable[[], None]) -> None` lets you run periodic callbacks from the frame loop.

The arrow box implementation uses timers internally for repeat activation behavior while held.

## Rendering and Drawing Model

## Pristine background restoration

`gui.set_pristine(image: str, obj: Optional[Any] = None) -> None` captures a clean background snapshot.

You can then call `gui.restore_pristine(area: Optional[Rect] = None, obj: Optional[Any] = None) -> None` each frame (as the demo does) before drawing dynamic content. This is the primary erase/redraw pattern used in `gui_do`.

## Buffered drawing

Set `gui.buffered = True` to have the renderer save pixels underneath gui objects before draws and restore them afterward.

- Use this when your graphical background doesn't change and instead of redrawing the entire background the graphical areas underneath gui objects are restored between gui loops.
- This setting is not useful if your background graphics are significantly changing, it is meant for mostly static backgrounds.
- You are responsible for undoing or otherwise managing your own changes to the background between gui loops.

## Coordinates

- Coordinates are pixel-based.
- Screen widgets use screen coordinates.
- Window child widgets use window-local coordinates.

## Mouse Locking and Cursors

These APIs are useful when building drag tools, RTS-style camera controls, or custom cursor workflows.

## Lock mouse to a rectangle

`gui.set_lock_area(locking_object: Optional[Widget], area: Optional[Rect] = None) -> None` clamps the pointer position to a `Rect` until released.

- `locking_object` must be a registered widget.
- `area` must be a valid `Rect` with positive width/height.
- Call `gui.set_lock_area(locking_object=None, area=None)` to release.

## Lock to a point (relative input mode)

`gui.set_lock_point(locking_object: Optional[Widget], point: Optional[Tuple[int, int]] = None) -> None` enables point-lock mode.

- Input remains active through the locked widget while the hardware pointer is recentred only when it exits a broad center region.
- If `point` is omitted, the current mouse position is used.
- Call `gui.set_lock_point(locking_object=None, point=None)` to release.

The demo uses this mode on the Life canvas while right-dragging.

## Load and select custom cursors

Cursor images are loaded through `WidgetGraphicsFactory` and selected by name in `GuiManager`.

- `gui.graphics_factory.register_cursor(*, name: str, filename: str, hotspot: Tuple[int, int]) -> CursorAsset`
- `gui.set_cursor(name: str) -> None`

Notes:

- `hotspot` is a tuple `(x, y)` inside the cursor image.
- `cursor_name` is the logical ID you use later with `set_cursor`.
- `filename` is the file inside `data/cursors/`.
- Cursors are shared between graphics factories and therefore also gui managers. Any cursor loaded in any gui manager can be set in any other gui manager as long as it has been loaded somewhere at least once.

Example:

```python
gui.graphics_factory.register_cursor(name="normal", filename="cursor.png", hotspot=(1, 1))
gui.graphics_factory.register_cursor(name="hand", filename="hand.png", hotspot=(12, 12))

gui.set_cursor("normal")
# ... later during drag state
gui.set_cursor("hand")
```

## Layout helper

`gui.set_grid_properties(anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None` plus `gui.gridded(x: int, y: int) -> Union[Rect, Tuple[int, int]]` gives a simple uniform grid positioning workflow.

The demo uses this repeatedly for dense control layouts.

## Demo Walkthrough: What To Learn From It

`gui_do_demo.py` demonstrates several production-use patterns:

- Two full GUI contexts (`gui1`, `gui2`) switched via `StateManager`.
- Screen-level controls that toggle window visibility.
- A button-group inspector window updating labels from `Event.Group` selections.
- Scrollbar variants (`Skip`, `Split`, `Near`, `Far`) in both orientations.
- A Game of Life canvas with pan/zoom and overflow-safe event handling.
- Mandelbrot rendering using background tasks and progressive updates.

If you are new to this package, reading and modifying the demo is the fastest way to become productive.

## Gotchas and Current Limits

These are the most useful caveats to know up front:

- No advanced layout engine yet (only simple grid helper).
- No built-in theming system; palette and style are mostly fixed.
- Window resizing is not implemented.
- Widget IDs must be unique across screen and all windows.
- Label auto IDs (`label_1`, `label_2`, ...) are generated if omitted.
- Canvas queues can overflow if not drained promptly.
- Task progress callbacks can backpressure if you send messages too quickly.

## Suggested Development Workflow

1. Start from `gui_do_demo.py` and strip features you do not need.
2. Keep your app logic in screen/window lifecycle handlers.
3. Use canvas for custom drawing regions.
4. Use scheduler tasks for expensive computation.
5. Treat `Event.Widget`, `Event.Group`, and `Event.Task` as your primary control flow events.

## Running the Demo

```bash
python gui_do_demo.py
```

If assets are missing or not found, verify the `data/` directory contains the files referenced by the demo. If the application is running on a system that has case-sensitive filenames, like Linux, the case of directory and file names must match the strings used in code.

# Optional Deep Dive: Life and Mandelbrot Internals

The earlier sections are enough to build and ship applications. This part exists for developing programmers who want a complete mental model of how to use the GUI APIs in more advanced patterns.

## Life example: how `generate(self) -> None` uses the delta table

In the demo, live cells are stored as a `set` of grid coordinates, for example `(x, y)`.

The class-level `neighbours` tuple is a delta table:

- `(-1, -1)`, `( 0, -1)`, `( 1, -1)`
- `(-1,  0)`, `(.., ..)`, `( 1,  0)`
- `(-1,  1)`, `( 0,  1)`, `( 1,  1)`

`generate(self) -> None` works in two stages:

1. It computes local population with a helper (`population(cell: Tuple[int, int]) -> int`):
    for each delta in `neighbours`, it adds the delta to the current cell to get a neighbor coordinate, then checks membership in `self.life`.
2. It builds a new set (`new_life`) by testing both:
    - each currently live cell (survival checks)
    - each neighbor around each live cell (birth checks)

Why this structure is useful:

- The delta table keeps neighbor logic centralized and easy to reason about.
- Using a set keeps membership checks fast and keeps the simulation sparse.
- Rebuilding into `new_life` avoids mutating the current generation while still reading from it.

In other words, the Life example shows a clean pattern for "read old state, compute next state, then swap" that maps well to GUI frame updates.

## Mandelbrot example: workers send numbers, UI thread draws pixels

The Mandelbrot tasks use `gui.scheduler` and intentionally avoid touching pygame surfaces in worker code.

Worker side (background task):

- Computes iteration counts (numbers) for pixels or rectangular regions.
- Sends payloads with `scheduler.send_message(task_id: Hashable, parameters: object) -> None`.
- Payloads are numeric data like `(x, y, w, h, value)` or `(x, y, w, h, values)` where `values` is a list of iteration counts.

Important rule demonstrated by the demo:

- Worker tasks do not draw and do not access pygame surfaces.
- They only publish numeric messages.

UI side (main thread callback):

- The scheduler message handler receives those numeric payloads.
- `apply_mandel_result(task_id: Hashable, result: Tuple[int, int, int, int, Union[int, List[int]]]) -> None` chooses the target canvas by `task_id`.
- Iteration counts are converted to RGB via `col(k: int) -> Tuple[int, int, int]`.
- The callback performs actual drawing (`fill` for region blocks or per-pixel writes).

Why this matters for API usage:

- It preserves thread affinity for UI resources.
- It avoids cross-thread surface access bugs.
- It gives progressive rendering: users see the fractal appear while computation continues.

If you use the scheduler for any heavy computation, follow the same pattern:

1. Compute in worker.
2. Send compact numeric progress messages.
3. Convert numbers to visuals only in the UI-thread callback.
