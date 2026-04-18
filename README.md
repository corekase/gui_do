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
- Common controls: buttons, toggles, button groups, scrollbars, labels, images, frames, arrow boxes, canvases, and bottom task panels.
- A task scheduler for background computation with UI-thread progress callbacks.

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

The same command is run in CI by the GitHub Actions workflow:

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

## 3. Minimal runnable setup

```python
import pygame
from pygame import Rect
from gui import GuiManager, Engine, StateManager, Event, ButtonStyle

pygame.init()
screen = pygame.display.set_mode((1280, 720))

fonts = [
    ("normal", "Gimbot.ttf", 16),
    ("titlebar", "Ubuntu-B.ttf", 14),
]

gui = GuiManager(screen, fonts)
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

`Engine.run()` performs the frame cycle:

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

This is a key behavior used by the demo when building each window section.

## Public API Entry Points

From `gui` package import:

- `GuiManager`
- `Engine`
- `StateManager`
- `colours`
- `Event`
- `CanvasEvent`
- `Orientation`
- `ArrowPosition`
- `ButtonStyle`

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

- `gui.ArrowBox(id, rect, direction_degrees, on_activate=None)`
- `gui.Button(id, rect, style, text, on_activate=None)`
- `gui.ButtonGroup(group, id, rect, style, text)`
- `gui.Canvas(id, rect, backdrop=None, on_activate=None, automatic_pristine=False)`
- `gui.Frame(id, rect)`
- `gui.Image(id, rect, image, automatic_pristine=False, scale=True)`
- `gui.Label(position, text, shadow=False, id=None)`
- `gui.Scrollbar(id, overall_rect, orientation, arrow_position, (total, start, bar_size, inc))`
- `gui.Toggle(id, rect, style, pushed, pressed_text, raised_text=None)`
- `gui.Window(title, pos, size, backdrop=None, preamble=None, event_handler=None, postamble=None)`

Task panel behavior is manager-owned (not a separate widget factory).

Constructor takes one task panel switch:

- `task_panel_enabled=True`

When enabled, optional customization is done through:

- `gui.configure_task_panel(height=38, x=0, reveal_pixels=4, auto_hide=True, timer_interval=16.0, movement_step=4, backdrop=None, preamble=None, event_handler=None, postamble=None)`

You can call `configure_task_panel(...)` with any subset of keyword arguments to override defaults.

To parent newly created widgets into the task panel container, bracket creation with:

- `gui.begin_task_panel()`
- `gui.end_task_panel()`

Runtime task panel helpers on `GuiManager`:

- `gui.set_task_panel_enabled(enabled)`
- `gui.set_task_panel_auto_hide(auto_hide)`
- `gui.set_task_panel_reveal_pixels(reveal_pixels)`
- `gui.set_task_panel_movement_step(movement_step)`
- `gui.set_task_panel_timer_interval(timer_interval)`
- `gui.read_task_panel_settings()`

## Events and Callbacks

## GUI events

Your screen/window event handler receives framework events (`Event` enum), not raw pygame events.

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
- For canvases, `on_activate` should drain queued canvas events via `canvas.read_event()`.

## Canvas usage (from Life window in demo)

`Canvas` is an off-screen drawing surface plus an input event queue.

Key methods:

- `canvas.get_canvas_surface()`
- `canvas.read_event()` returns `CanvasEventPacket | None`
- `canvas.set_event_queue_limit(max_events)`
- `canvas.set_overflow_handler(callback)`
- `canvas.set_motion_coalescing(enabled)`

The demo uses canvas events for:

- Right-mouse drag panning (`MouseButtonDown`/`MouseMotion`/`MouseButtonUp`)
- Mouse wheel zoom (`MouseWheel`)

Important: if you do not consume events fast enough, older events are dropped when queue is full.

## Background Tasks and Timers

## Scheduler

Use `gui.scheduler` for background work.

- `add_task(task_id, logic, parameters=None, message_method=None)`
- `send_message(task_id, payload)` from inside the task function
- `pop_result(task_id)` after completion
- `remove_tasks(*ids)`, `tasks_busy_match_any(*ids)`

The Mandelbrot demo uses this heavily:

- Worker task computes regions.
- Task sends incremental draw payloads to main thread.
- UI applies payloads in a message callback.
- `Event.Task` is used for completion/failure handling.

## Threading and affinity rules

Current Python builds still have the GIL, but scheduler worker tasks should be treated as true concurrent producers and the GUI loop as the single consumer/owner of UI state.

- Only mutate widget/window/screen state from main-thread callbacks (screen/window lifecycle, widget handlers, scheduler message callbacks, and `Event.Task` handling).
- Worker task logic should not directly touch `GuiManager`, widgets, windows, renderer objects, or pygame surfaces.
- Worker tasks should communicate with the UI only through `scheduler.send_message(...)` and by returning a result consumed through task completion.
- Task messages, completion notifications, and task failures are queued and then applied on the frame thread during `scheduler.update()`.
- Removing/re-adding the same task id is generation-protected: stale worker messages/completions/failures from earlier generations are discarded.

## Timers

`gui.timers.add_timer(id, duration_ms, callback)` lets you run periodic callbacks from the frame loop.

The arrow box implementation uses timers internally for repeat activation behavior while held.

## Rendering and Drawing Model

## Pristine background restoration

`set_pristine(image)` captures a clean background snapshot.

You can then call `restore_pristine()` each frame (as the demo does) before drawing dynamic content. This is the primary erase/redraw pattern used in `gui_do`.

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

`gui.set_lock_area(locking_object, area)` clamps the pointer position to a `Rect` until released.

- `locking_object` must be a registered widget.
- `area` must be a valid `Rect` with positive width/height.
- Call `gui.set_lock_area(None)` to release.

## Lock to a point (relative input mode)

`gui.set_lock_point(locking_object, point=None)` enables point-lock mode.

- Input remains active through the locked widget while the hardware pointer is recentred only when it exits a broad center region.
- If `point` is omitted, the current mouse position is used.
- Call `gui.set_lock_point(None)` to release.

The demo uses this mode on the Life canvas while right-dragging.

## Load and select custom cursors

Cursor images are loaded through `BitmapFactory` and selected by name in `GuiManager`.

- `gui.bitmap_factory.load_cursor(hotspot, cursor_name, filename)`
- `gui.set_cursor(cursor_name)`

Notes:

- `hotspot` is a tuple `(x, y)` inside the cursor image.
- `cursor_name` is the logical ID you use later with `set_cursor`.
- `filename` is the file inside `data/cursors/`.
- Cursors are shared between bitmap factories and therefore also gui managers.  Any cursor loaded in any gui manager can be set in any other gui manager as long as it has been loaded somewhere at least once.

Example:

```python
gui.bitmap_factory.load_cursor((1, 1), "normal", "cursor.png")
gui.bitmap_factory.load_cursor((12, 12), "hand", "hand.png")

gui.set_cursor("normal")
# ... later during drag state
gui.set_cursor("hand")
```

## Layout helper

`set_grid_properties(anchor, width, height, spacing, use_rect=True)` plus `gridded(x, y)` gives a simple uniform grid positioning workflow.

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

If assets are missing or not found, verify the `data/` directory contains the files referenced by the demo and you are starting python in the same directory as the demo.  If the application is running on a system that has case-sensitive filenames, like Linux, then the case of the data directory and the filename string need to match.

# Optional Deep Dive: Life and Mandelbrot Internals

The earlier sections are enough to build and ship applications. This part exists for developing programmers who want a complete mental model of how to use the GUI APIs in more advanced patterns.

## Life example: how `generate()` uses the delta table

In the demo, live cells are stored as a `set` of grid coordinates, for example `(x, y)`.

The class-level `neighbours` tuple is a delta table:

- `(-1, -1)`, `( 0, -1)`, `( 1, -1)`
- `(-1,  0)`, `(.., ..)`, `( 1,  0)`
- `(-1,  1)`, `( 0,  1)`, `( 1,  1)`

`generate()` works in two stages:

1. It computes local population with a helper (`population(cell)`):
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
- Sends payloads with `scheduler.send_message(task_id, payload)`.
- Payloads are numeric data like `(x, y, w, h, value)` or `(x, y, w, h, values)` where `values` is a list of iteration counts.

Important rule demonstrated by the demo:

- Worker tasks do not draw and do not access pygame surfaces.
- They only publish numeric messages.

UI side (main thread callback):

- The scheduler message handler receives those numeric payloads.
- `apply_mandel_result(...)` chooses the target canvas by `task_id`.
- Iteration counts are converted to RGB via `col(...)`.
- The callback performs actual drawing (`fill` for region blocks or per-pixel writes).

Why this matters for API usage:

- It preserves thread affinity for UI resources.
- It avoids cross-thread surface access bugs.
- It gives progressive rendering: users see the fractal appear while computation continues.

If you use the scheduler for any heavy computation, follow the same pattern:

1. Compute in worker.
2. Send compact numeric progress messages.
3. Convert numbers to visuals only in the UI-thread callback.
