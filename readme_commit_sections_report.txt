===== COMMIT 2b83537 =====
2b83537 implement layout management
--- ## 2. Project layout expected by gui_do ---

The toolkit expects assets under `data/`:

- `data/fonts/`
- `data/images/`
- `data/cursors/`

The demo uses this directly (fonts, `*.ttf` files, and images, example `backdrop.jpg`, and cursors, example `cursor.png`).

Resource loading resolves from the repository `data/` folder, so it is independent of your current working directory.


--- ## 1. Engine: frame orchestration ---

`Engine.run() -> None` performs the frame cycle:

1. Screen/window preamble callbacks.
2. Input polling and dispatch.
3. Scheduler update (task completion + progress message dispatch).
4. Screen/window postamble callbacks.
5. Render + display flip.

This means your callbacks and UI updates happen on the main thread in a predictable order each frame.


--- ## 2. StateManager: multi-GUI app states ---

You can register multiple `GuiManager` instances as named contexts (for example, `gui1` and `gui2` in the demo) and switch at runtime.

Important behavior: when context switches, mouse position is carried over.


--- ## 3. GuiManager: your main API surface ---

You mostly program through `GuiManager`.

It owns:

- Widget/window registration.
- Event routing.
- Renderer.
- Scheduler (`gui.scheduler`) and timers (`gui.timers`).
- Layout system (`grid`, `linear`, and `anchor` helpers).


--- ## 4. Window vs screen widgets ---

- If there is no active window, created widgets become screen-level widgets.
- After creating a window, subsequent widgets are parented to that active window.
- Toggling `window.visible` also updates active-window state: setting `True` makes that window active, setting `False` removes it from active selection.
- Keyboard input follows active-window focus: key events go to the active window handler, and if no window is active they go to the screen lifecycle event handler.

This is a key behavior used by the demo when building each window section.


--- ## Public API Entry Points ---

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


--- ## Core Runtime API Reference ---

The sections above focus on practical usage. This section provides complete callable coverage for the core runtime classes.


--- ## Engine API ---

- `Engine(state_manager: StateManager)`
- `engine.run() -> None`


--- ## StateManager API ---

- `state.register_context(name: str, gui: GuiManager, replace: bool = False) -> GuiManager`
- `state.switch_context(name: str) -> GuiManager`
- `state.get_active_gui() -> Optional[GuiManager]`
- `state.set_running(running: bool) -> None`


--- ## GuiManager Properties ---

- `gui.graphics_factory` (property)
- `gui.scheduler` (property)
- `gui.buffered` (read/write bool property)


--- ## GuiManager Advanced Methods ---

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


--- ## Background Tasks and Timers ---


--- ## Scheduler ---

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


--- ## Timers ---

`gui.timers.add_timer(id: Hashable, duration: float, callback: Callable[[], None]) -> None` lets you run periodic callbacks from the frame loop.

The arrow box implementation uses timers internally for repeat activation behavior while held.


--- # ... later during drag state ---
gui.set_cursor("hand")
```

## Layout helper

`gui.set_grid_properties(anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None` plus `gui.gridded(x: int, y: int) -> Union[Rect, Tuple[int, int]]` gives a simple uniform grid positioning workflow.

The demo uses this repeatedly for dense control layouts.

## Layout managers and geometry patterns

The package now includes a small layout system with three practical managers based on common GUI patterns:

- Grid layout for dense control matrices with stable row/column semantics.
- Linear layout for toolbar/button rows or columns, with optional wrapping.
- Anchor layout for edge/center alignment inside a bounded area.

Runtime API:

- `gui.set_grid_properties(anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None`
- `gui.gridded(x: int, y: int) -> Union[Rect, Tuple[int, int]]`
- `gui.set_linear_properties(anchor: Tuple[int, int], item_width: int, item_height: int, spacing: int, horizontal: bool = True, wrap_count: int = 0, use_rect: bool = True) -> None`
- `gui.linear(index: int) -> Union[Rect, Tuple[int, int]]`
- `gui.next_linear() -> Union[Rect, Tuple[int, int]]`
- `gui.reset_linear_cursor() -> None`
- `gui.set_anchor_bounds(bounds: Rect) -> None`
- `gui.anchored(size: Tuple[int, int], anchor: str = "center", margin: Tuple[int, int] = (0, 0), use_rect: bool = True) -> Union[Rect, Tuple[int, int]]`
- `gui.place_gui_object(gui_object: Union[Window, Widget], geometry: Union[Rect, Tuple[int, int]]) -> Union[Window, Widget]`

Best-practice mapping to this package's geometry model:

- Use grid layout when widgets share one canonical size and `Rect` geometry is directly passed into widget constructors.
- Use linear layout when ordering matters more than row/column coordinates, for example task-panel button strips and bottom action rows.
- Use anchor layout when a geometry target must be aligned to container bounds (for example centering a window footprint in screen coordinates).
- Use `place_gui_object` for post-construction layout passes: it maps `Rect` to `position` by `.topleft` and preserves widget/window sizes.
- Keep a single layout strategy per region (for example one linear strip per task panel row) to reduce hidden geometry coupling.

## Demo Walkthrough: What To Learn From It

`gui_do_demo.py` demonstrates several production-use patterns:
[...truncated section after 40 lines...]

--- ## Layout helper ---

`gui.set_grid_properties(anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None` plus `gui.gridded(x: int, y: int) -> Union[Rect, Tuple[int, int]]` gives a simple uniform grid positioning workflow.

The demo uses this repeatedly for dense control layouts.


--- ## Layout managers and geometry patterns ---

The package now includes a small layout system with three practical managers based on common GUI patterns:

- Grid layout for dense control matrices with stable row/column semantics.
- Linear layout for toolbar/button rows or columns, with optional wrapping.
- Anchor layout for edge/center alignment inside a bounded area.

Runtime API:

- `gui.set_grid_properties(anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None`
- `gui.gridded(x: int, y: int) -> Union[Rect, Tuple[int, int]]`
- `gui.set_linear_properties(anchor: Tuple[int, int], item_width: int, item_height: int, spacing: int, horizontal: bool = True, wrap_count: int = 0, use_rect: bool = True) -> None`
- `gui.linear(index: int) -> Union[Rect, Tuple[int, int]]`
- `gui.next_linear() -> Union[Rect, Tuple[int, int]]`
- `gui.reset_linear_cursor() -> None`
- `gui.set_anchor_bounds(bounds: Rect) -> None`
- `gui.anchored(size: Tuple[int, int], anchor: str = "center", margin: Tuple[int, int] = (0, 0), use_rect: bool = True) -> Union[Rect, Tuple[int, int]]`
- `gui.place_gui_object(gui_object: Union[Window, Widget], geometry: Union[Rect, Tuple[int, int]]) -> Union[Window, Widget]`

Best-practice mapping to this package's geometry model:

- Use grid layout when widgets share one canonical size and `Rect` geometry is directly passed into widget constructors.
- Use linear layout when ordering matters more than row/column coordinates, for example task-panel button strips and bottom action rows.
- Use anchor layout when a geometry target must be aligned to container bounds (for example centering a window footprint in screen coordinates).
- Use `place_gui_object` for post-construction layout passes: it maps `Rect` to `position` by `.topleft` and preserves widget/window sizes.
- Keep a single layout strategy per region (for example one linear strip per task panel row) to reduce hidden geometry coupling.



===== COMMIT b5ef975 =====
b5ef975 implement window tiling
--- ## 2. Project layout expected by gui_do ---

The toolkit expects assets under `data/`:

- `data/fonts/`
- `data/images/`
- `data/cursors/`

The demo uses this directly (fonts, `*.ttf` files, and images, example `backdrop.jpg`, and cursors, example `cursor.png`).

Resource loading resolves from the repository `data/` folder, so it is independent of your current working directory.


--- ## 1. Engine: frame orchestration ---

`Engine.run() -> None` performs the frame cycle:

1. Screen/window preamble callbacks.
2. Input polling and dispatch.
3. Scheduler update (task completion + progress message dispatch).
4. Screen/window postamble callbacks.
5. Render + display flip.

This means your callbacks and UI updates happen on the main thread in a predictable order each frame.


--- ## 2. StateManager: multi-GUI app states ---

You can register multiple `GuiManager` instances as named contexts (for example, `gui1` and `gui2` in the demo) and switch at runtime.

Important behavior: when context switches, mouse position is carried over.


--- ## 3. GuiManager: your main API surface ---

You mostly program through `GuiManager`.

It owns:

- Widget/window registration.
- Event routing.
- Renderer.
- Scheduler (`gui.scheduler`) and timers (`gui.timers`).
- Layout helper (`set_grid_properties` and `gridded`).


--- ## 4. Window vs screen widgets ---

- If there is no active window, created widgets become screen-level widgets.
- After creating a window, subsequent widgets are parented to that active window.
- Toggling `window.visible` also updates active-window state: setting `True` makes that window active, setting `False` removes it from active selection.
- Keyboard input follows active-window focus: key events go to the active window handler, and if no window is active they go to the screen lifecycle event handler.

This is a key behavior used by the demo when building each window section.


--- ## Public API Entry Points ---

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


--- ## Core Runtime API Reference ---

The sections above focus on practical usage. This section provides complete callable coverage for the core runtime classes.


--- ## Engine API ---

- `Engine(state_manager: StateManager)`
- `engine.run() -> None`


--- ## StateManager API ---

- `state.register_context(name: str, gui: GuiManager, replace: bool = False) -> GuiManager`
- `state.switch_context(name: str) -> GuiManager`
- `state.get_active_gui() -> Optional[GuiManager]`
- `state.set_running(running: bool) -> None`


--- ## GuiManager Properties ---

- `gui.graphics_factory` (property)
- `gui.scheduler` (property)
- `gui.buffered` (read/write bool property)


--- ## GuiManager Advanced Methods ---

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


--- ## Background Tasks and Timers ---


--- ## Scheduler ---

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


--- ## Timers ---

`gui.timers.add_timer(id: Hashable, duration: float, callback: Callable[[], None]) -> None` lets you run periodic callbacks from the frame loop.

The arrow box implementation uses timers internally for repeat activation behavior while held.


--- # ... later during drag state ---
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
[...truncated section after 40 lines...]

--- ## Layout helper ---

`gui.set_grid_properties(anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None` plus `gui.gridded(x: int, y: int) -> Union[Rect, Tuple[int, int]]` gives a simple uniform grid positioning workflow.

The demo uses this repeatedly for dense control layouts.



===== COMMIT 45b44af =====
45b44af improve scrollbar
--- ## 2. Project layout expected by gui_do ---

The toolkit expects assets under `data/`:

- `data/fonts/`
- `data/images/`
- `data/cursors/`

The demo uses this directly (fonts, `*.ttf` files, and images, example `backdrop.jpg`, and cursors, example `cursor.png`).

Resource loading resolves from the repository `data/` folder, so it is independent of your current working directory.


--- ## 1. Engine: frame orchestration ---

`Engine.run() -> None` performs the frame cycle:

1. Screen/window preamble callbacks.
2. Input polling and dispatch.
3. Scheduler update (task completion + progress message dispatch).
4. Screen/window postamble callbacks.
5. Render + display flip.

This means your callbacks and UI updates happen on the main thread in a predictable order each frame.


--- ## 2. StateManager: multi-GUI app states ---

You can register multiple `GuiManager` instances as named contexts (for example, `gui1` and `gui2` in the demo) and switch at runtime.

Important behavior: when context switches, mouse position is carried over.


--- ## 3. GuiManager: your main API surface ---

You mostly program through `GuiManager`.

It owns:

- Widget/window registration.
- Event routing.
- Renderer.
- Scheduler (`gui.scheduler`) and timers (`gui.timers`).
- Layout helper (`set_grid_properties` and `gridded`).


--- ## 4. Window vs screen widgets ---

- If there is no active window, created widgets become screen-level widgets.
- After creating a window, subsequent widgets are parented to that active window.
- Toggling `window.visible` also updates active-window state: setting `True` makes that window active, setting `False` removes it from active selection.
- Keyboard input follows active-window focus: key events go to the active window handler, and if no window is active they go to the screen lifecycle event handler.

This is a key behavior used by the demo when building each window section.


--- ## Public API Entry Points ---

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


--- ## Core Runtime API Reference ---

The sections above focus on practical usage. This section provides complete callable coverage for the core runtime classes.


--- ## Engine API ---

- `Engine(state_manager: StateManager)`
- `engine.run() -> None`


--- ## StateManager API ---

- `state.register_context(name: str, gui: GuiManager, replace: bool = False) -> GuiManager`
- `state.switch_context(name: str) -> GuiManager`
- `state.get_active_gui() -> Optional[GuiManager]`
- `state.set_running(running: bool) -> None`


--- ## GuiManager Properties ---

- `gui.graphics_factory` (property)
- `gui.scheduler` (property)
- `gui.buffered` (read/write bool property)


--- ## GuiManager Advanced Methods ---

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


--- ## Background Tasks and Timers ---


--- ## Scheduler ---

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


--- ## Timers ---

`gui.timers.add_timer(id: Hashable, duration: float, callback: Callable[[], None]) -> None` lets you run periodic callbacks from the frame loop.

The arrow box implementation uses timers internally for repeat activation behavior while held.


--- # ... later during drag state ---
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
[...truncated section after 40 lines...]

--- ## Layout helper ---

`gui.set_grid_properties(anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None` plus `gui.gridded(x: int, y: int) -> Union[Rect, Tuple[int, int]]` gives a simple uniform grid positioning workflow.

The demo uses this repeatedly for dense control layouts.



===== COMMIT 0917397 =====
0917397 improve guimanager
--- ## 2. Project layout expected by gui_do ---

The toolkit expects assets under `data/`:

- `data/fonts/`
- `data/images/`
- `data/cursors/`

The demo uses this directly (fonts, `*.ttf` files, and images, example `backdrop.jpg`, and cursors, example `cursor.png`).

Resource loading resolves from the repository `data/` folder, so it is independent of your current working directory.


--- ## 1. Engine: frame orchestration ---

`Engine.run() -> None` performs the frame cycle:

1. Screen/window preamble callbacks.
2. Input polling and dispatch.
3. Scheduler update (task completion + progress message dispatch).
4. Screen/window postamble callbacks.
5. Render + display flip.

This means your callbacks and UI updates happen on the main thread in a predictable order each frame.


--- ## 2. StateManager: multi-GUI app states ---

You can register multiple `GuiManager` instances as named contexts (for example, `gui1` and `gui2` in the demo) and switch at runtime.

Important behavior: when context switches, mouse position is carried over.


--- ## 3. GuiManager: your main API surface ---

You mostly program through `GuiManager`.

It owns:

- Widget/window registration.
- Event routing.
- Renderer.
- Scheduler (`gui.scheduler`) and timers (`gui.timers`).
- Layout helper (`set_grid_properties` and `gridded`).


--- ## 4. Window vs screen widgets ---

- If there is no active window, created widgets become screen-level widgets.
- After creating a window, subsequent widgets are parented to that active window.
- Toggling `window.visible` also updates active-window state: setting `True` makes that window active, setting `False` removes it from active selection.
- Keyboard input follows active-window focus: key events go to the active window handler, and if no window is active they go to the screen lifecycle event handler.

This is a key behavior used by the demo when building each window section.


--- ## Public API Entry Points ---

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


--- ## Core Runtime API Reference ---

The sections above focus on practical usage. This section provides complete callable coverage for the core runtime classes.


--- ## Engine API ---

- `Engine(state_manager: StateManager)`
- `engine.run() -> None`


--- ## StateManager API ---

- `state.register_context(name: str, gui: GuiManager, replace: bool = False) -> GuiManager`
- `state.switch_context(name: str) -> GuiManager`
- `state.get_active_gui() -> Optional[GuiManager]`
- `state.set_running(running: bool) -> None`


--- ## GuiManager Properties ---

- `gui.graphics_factory` (property)
- `gui.scheduler` (property)
- `gui.buffered` (read/write bool property)


--- ## GuiManager Advanced Methods ---

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


--- ## Background Tasks and Timers ---


--- ## Scheduler ---

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


--- ## Timers ---

`gui.timers.add_timer(id: Hashable, duration: float, callback: Callable[[], None]) -> None` lets you run periodic callbacks from the frame loop.

The arrow box implementation uses timers internally for repeat activation behavior while held.


--- # ... later during drag state ---
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
[...truncated section after 40 lines...]

--- ## Layout helper ---

`gui.set_grid_properties(anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None` plus `gui.gridded(x: int, y: int) -> Union[Rect, Tuple[int, int]]` gives a simple uniform grid positioning workflow.

The demo uses this repeatedly for dense control layouts.



===== COMMIT b21d719 =====
b21d719 improve api
--- ## 2. Project layout expected by gui_do ---

The toolkit expects assets under `data/`:

- `data/fonts/`
- `data/images/`
- `data/cursors/`

The demo uses this directly (fonts, `*.ttf` files, and images, example `backdrop.jpg`, and cursors, example `cursor.png`).

Resource loading resolves from the repository `data/` folder, so it is independent of your current working directory.


--- ## 1. Engine: frame orchestration ---

`Engine.run() -> None` performs the frame cycle:

1. Screen/window preamble callbacks.
2. Input polling and dispatch.
3. Scheduler update (task completion + progress message dispatch).
4. Screen/window postamble callbacks.
5. Render + display flip.

This means your callbacks and UI updates happen on the main thread in a predictable order each frame.


--- ## 2. StateManager: multi-GUI app states ---

You can register multiple `GuiManager` instances as named contexts (for example, `gui1` and `gui2` in the demo) and switch at runtime.

Important behavior: when context switches, mouse position is carried over.


--- ## 3. GuiManager: your main API surface ---

You mostly program through `GuiManager`.

It owns:

- Widget/window registration.
- Event routing.
- Renderer.
- Scheduler (`gui.scheduler`) and timers (`gui.timers`).
- Layout helper (`set_grid_properties` and `gridded`).


--- ## 4. Window vs screen widgets ---

- If there is no active window, created widgets become screen-level widgets.
- After creating a window, subsequent widgets are parented to that active window.
- Toggling `window.visible` also updates active-window state: setting `True` makes that window active, setting `False` removes it from active selection.
- Keyboard input follows active-window focus: key events go to the active window handler, and if no window is active they go to the screen lifecycle event handler.

This is a key behavior used by the demo when building each window section.


--- ## Public API Entry Points ---

From `gui` package import:

- `GuiManager`
- `Engine`
- `StateManager`
- `TaskPanelSettings`
- `MouseInputState`
- `colours`
- `Event`
- `CanvasEvent`
- `Orientation`
- `ArrowPosition`
- `ButtonStyle`


--- ## Core Runtime API Reference ---

The sections above focus on practical usage. This section provides complete callable coverage for the core runtime classes.


--- ## Engine API ---

- `Engine(state_manager: StateManager)`
- `engine.run() -> None`


--- ## StateManager API ---

- `state.register_context(name: str, gui: GuiManager, replace: bool = False) -> GuiManager`
- `state.switch_context(name: str) -> GuiManager`
- `state.get_active_gui() -> Optional[GuiManager]`
- `state.set_running(running: bool) -> None`


--- ## GuiManager Properties ---

- `gui.graphics_factory` (property)
- `gui.scheduler` (property)
- `gui.buffered` (read/write bool property)


--- ## GuiManager Advanced Methods ---

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


--- ## Background Tasks and Timers ---


--- ## Scheduler ---

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


--- ## Timers ---

`gui.timers.add_timer(id: Hashable, duration: float, callback: Callable[[], None]) -> None` lets you run periodic callbacks from the frame loop.

The arrow box implementation uses timers internally for repeat activation behavior while held.


--- # ... later during drag state ---
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
[...truncated section after 40 lines...]

--- ## Layout helper ---

`gui.set_grid_properties(anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None` plus `gui.gridded(x: int, y: int) -> Union[Rect, Tuple[int, int]]` gives a simple uniform grid positioning workflow.

The demo uses this repeatedly for dense control layouts.



===== COMMIT 7285ff0 =====
7285ff0 readme
--- ## 2. Project layout expected by gui_do ---

The toolkit expects assets under `data/`:

- `data/fonts/`
- `data/images/`
- `data/cursors/`

The demo uses this directly (fonts, `*.ttf` files, and images, example `backdrop.jpg`, and cursors, example `cursor.png`).

Resource loading resolves from the repository `data/` folder, so it is independent of your current working directory.


--- ## 1. Engine: frame orchestration ---

`Engine.run() -> None` performs the frame cycle:

1. Screen/window preamble callbacks.
2. Input polling and dispatch.
3. Scheduler update (task completion + progress message dispatch).
4. Screen/window postamble callbacks.
5. Render + display flip.

This means your callbacks and UI updates happen on the main thread in a predictable order each frame.


--- ## 2. StateManager: multi-GUI app states ---

You can register multiple `GuiManager` instances as named contexts (for example, `gui1` and `gui2` in the demo) and switch at runtime.

Important behavior: when context switches, mouse position is carried over.


--- ## 3. GuiManager: your main API surface ---

You mostly program through `GuiManager`.

It owns:

- Widget/window registration.
- Event routing.
- Renderer.
- Scheduler (`gui.scheduler`) and timers (`gui.timers`).
- Layout helper (`set_grid_properties` and `gridded`).


--- ## 4. Window vs screen widgets ---

- If there is no active window, created widgets become screen-level widgets.
- After creating a window, subsequent widgets are parented to that active window.
- Toggling `window.visible` also updates active-window state: setting `True` makes that window active, setting `False` removes it from active selection.
- Keyboard input follows active-window focus: key events go to the active window handler, and if no window is active they go to the screen lifecycle event handler.

This is a key behavior used by the demo when building each window section.


--- ## Public API Entry Points ---

From `gui` package import:

- `GuiManager`
- `Engine`
- `StateManager`
- `TaskPanelSettings`
- `colours`
- `Event`
- `CanvasEvent`
- `Orientation`
- `ArrowPosition`
- `ButtonStyle`


--- ## Core Runtime API Reference ---

The sections above focus on practical usage. This section provides complete callable coverage for the core runtime classes.


--- ## Engine API ---

- `Engine(state_manager: StateManager)`
- `engine.run() -> None`


--- ## StateManager API ---

- `state.register_context(name: str, gui: GuiManager, replace: bool = False) -> GuiManager`
- `state.switch_context(name: str) -> GuiManager`
- `state.get_active_gui() -> Optional[GuiManager]`
- `state.set_running(running: bool) -> None`


--- ## GuiManager Properties ---

- `gui.graphics_factory` (property)
- `gui.scheduler` (property)
- `gui.buffered` (read/write bool property)


--- ## GuiManager Advanced Methods ---

- `gui.build_font_registry(**fonts: Tuple[str, int]) -> List[Tuple[str, str, int]]`
- `gui.load_fonts(fonts: Iterable[Tuple[str, str, int]]) -> None`
- `gui.hide_widgets(*widgets: Widget) -> None`
- `gui.show_widgets(*widgets: Widget) -> None`
- `gui.lower_window(window: Window) -> None`
- `gui.raise_window(window: Window) -> None`
- `gui.set_task_owner(task_id: Hashable, window: Optional[Window]) -> None`
- `gui.set_task_owners(window: Optional[Window], *task_ids: Hashable) -> None`
- `gui.draw_gui() -> None`
- `gui.undraw_gui() -> None`
- `gui.get_mouse_pos() -> Tuple[int, int]`
- `gui.set_mouse_pos(pos: Tuple[int, int], update_physical_coords: bool = True) -> None`
- `gui.convert_to_screen(point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int>`
- `gui.convert_to_window(point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int>`
- `gui.copy_graphic_area(surface: Surface, rect: Rect, flags: int = 0) -> Surface`


--- ## Background Tasks and Timers ---


--- ## Scheduler ---

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


--- ## Timers ---

`gui.timers.add_timer(id: Hashable, duration: float, callback: Callable[[], None]) -> None` lets you run periodic callbacks from the frame loop.

The arrow box implementation uses timers internally for repeat activation behavior while held.


--- # ... later during drag state ---
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
[...truncated section after 40 lines...]

--- ## Layout helper ---

`gui.set_grid_properties(anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None` plus `gui.gridded(x: int, y: int) -> Union[Rect, Tuple[int, int]]` gives a simple uniform grid positioning workflow.

The demo uses this repeatedly for dense control layouts.



