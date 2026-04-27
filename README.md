[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

# gui_do

gui_do is a pygame GUI framework built around strict scene isolation, a composable Feature lifecycle, and a normalized event pipeline. It provides controls, layout, focus management, background task scheduling, pub-sub messaging, observable data binding, overlay and notification systems, drag-and-drop, form validation, command history, animation tweens, and built-in telemetry — organized so that application logic and GUI structure stay separate by design.

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
  - [Cursor Management](#cursor-management)
- [Controls](#controls)
  - [Common Pattern and UiNode API](#common-pattern-and-uinode-api)
  - [PanelControl](#panelcontrol)
  - [LabelControl](#labelcontrol)
  - [ButtonControl](#buttoncontrol)
  - [ToggleControl](#togglecontrol)
  - [ArrowBoxControl](#arrowboxcontrol)
  - [ButtonGroupControl](#buttongroupcontrol)
  - [SliderControl](#slidercontrol)
  - [ScrollbarControl](#scrollbarcontrol)
  - [TextInputControl](#textinputcontrol)
  - [ListViewControl](#listviewcontrol)
  - [DropdownControl](#dropdowncontrol)
  - [ImageControl](#imagecontrol)
  - [CanvasControl](#canvascontrol)
  - [FrameControl](#framecontrol)
  - [WindowControl](#windowcontrol)
  - [SplitterControl](#splittercontrol)
  - [TaskPanelControl](#taskpanelcontrol)
  - [OverlayPanelControl](#overlaypanelcontrol)
  - [DataGridControl](#datagridcontrol)
- [Layout](#layout)
  - [LayoutAxis](#layoutaxis)
  - [LayoutManager](#layoutmanager)
  - [WindowTilingManager](#windowtilingmanager)
  - [ConstraintLayout](#constraintlayout)
- [Events and Input](#events-and-input)
  - [EventType, EventPhase, and GuiEvent](#eventtype-eventphase-and-guievent)
  - [EventManager](#eventmanager)
  - [EventBus](#eventbus)
  - [ActionManager](#actionmanager)
  - [FocusManager](#focusmanager)
  - [FontManager](#fontmanager)
- [Data and State](#data-and-state)
  - [ObservableValue and PresentationModel](#observablevalue-and-presentationmodel)
  - [ValueChangeCallback and ValueChangeReason](#valuechangecallback-and-valuechangereason)
  - [FormModel and FormField](#formmodel-and-formfield)
- [Scheduling and Animation](#scheduling-and-animation)
  - [TaskScheduler](#taskscheduler)
  - [Timers](#timers)
  - [TweenManager](#tweenmanager)
- [Overlay and Notifications](#overlay-and-notifications)
  - [OverlayManager](#overlaymanager)
  - [ToastManager](#toastmanager)
  - [DialogManager](#dialogmanager)
  - [ContextMenuManager](#contextmenumanager)
  - [DragDropManager](#dragdropmanager)
- [Command History](#command-history)
- [Feature System](#feature-system)
  - [Feature](#feature)
  - [DirectFeature](#directfeature)
  - [LogicFeature](#logicfeature)
  - [RoutedFeature](#routedfeature)
  - [FeatureMessage](#featuremessage)
  - [FeatureManager](#featuremanager)
- [Theme and Graphics](#theme-and-graphics)
  - [ColorTheme](#colortheme)
  - [BuiltInGraphicsFactory](#builtingraphicsfactory)
- [Telemetry](#telemetry)
- [Core Utilities](#core-utilities)
  - [InvalidationTracker](#invalidationtracker)

---

<a id="quick-start"></a>

## Quick Start — [Back to Top](#table-of-contents)

```bash
pip install gui_do
```

```python
import pygame
from gui_do import GuiApplication, UiEngine, LabelControl
from pygame import Rect

pygame.init()
surface = pygame.display.set_mode((800, 600))
app = GuiApplication(surface)

label = app.scene.add(LabelControl("lbl", Rect(50, 50, 300, 40), "Hello, gui_do!"))

engine = UiEngine(app, target_fps=60)
engine.run()
pygame.quit()
```

---

<a id="overview"></a>

## Overview — [Back to Top](#table-of-contents)

gui_do is structured around a small number of composable systems that work together:

**Scene graph.** Every application has at least one `Scene` accessed via `app.scene`. Scenes hold root `UiNode` controls in a tree. The active scene is drawn and dispatched each frame. Multiple named scenes can be registered and switched at runtime — only the active scene receives updates and input.

**Controls.** All visible widgets are `UiNode` subclasses. They hold a `rect`, `visible`, `enabled`, and `tab_index`. Controls are added to the scene graph via `scene.add(node)` or a parent control's `add(child)`. They implement `draw()`, `handle_event()`, and `update()`.

**Feature lifecycle.** Application logic is organized into `Feature` units. A Feature wraps a rect in the scene, manages its own controls, and responds to lifecycle events (`on_mount`, `on_unmount`, `on_update`, `on_message`). `DirectFeature`, `LogicFeature`, and `RoutedFeature` provide progressively more structured variants. Features are registered with `app.features`.

**Events.** pygame events are normalized by `EventManager` into `GuiEvent` objects with consistent fields (`kind`, `pos`, `button`, `key`, `wheel`). The normalized event is dispatched through the scene graph's capture/bubble pipeline. `EventBus` provides a separate scoped pub-sub channel for UI-to-UI communication. `ActionManager` maps key bindings to named actions.

**Focus.** `FocusManager` maintains keyboard focus as an independent concept from window activation. Tab-order traversal advances through nodes by `tab_index`. Focus can be set programmatically or through mouse clicks.

**Observable state.** `ObservableValue` wraps a value with a subscriber list. `PresentationModel` is a base for data models built from `ObservableValue` fields. Controls that expose a value callback use `ValueChangeCallback[T]` with a `ValueChangeReason` enum that identifies the input source.

**Scheduling.** `TaskScheduler` runs background tasks on a thread pool and safely dispatches results back to the UI loop via a message queue. `Timers` provides frame-driven repeating and one-shot callbacks. `TweenManager` interpolates object attributes over time with configurable easing.

**Overlay systems.** `OverlayManager` manages a stack of floating controls (overlays). `ToastManager` shows ephemeral notification banners. `DialogManager` provides modal alert, confirm, and prompt dialogs. `ContextMenuManager` builds click-positioned context menus. `DragDropManager` coordinates mouse drag-and-drop sessions between nodes.

**Forms and commands.** `FormModel` aggregates `FormField` instances with per-field and cross-field validation. `CommandHistory` provides a bounded undo/redo stack with transaction support.

gui_do suits interactive tool UIs, dashboard displays, game editors, and any application where the developer needs full control over layout and rendering while keeping logic and visuals separate.

---

<a id="minimal-runnable-example"></a>

## Minimal Runnable Example — [Back to Top](#table-of-contents)

```python
import pygame
from gui_do import GuiApplication, UiEngine, ButtonControl, LabelControl
from pygame import Rect

pygame.init()
surface = pygame.display.set_mode((640, 480))
pygame.display.set_caption("gui_do")

app = GuiApplication(surface)

label = app.scene.add(LabelControl("status", Rect(20, 20, 300, 32), "Ready"))
btn = app.scene.add(
    ButtonControl("btn", Rect(20, 70, 120, 36), "Click me", on_click=lambda: setattr(label, "text", "Clicked!"))
)

engine = UiEngine(app, target_fps=60)
engine.run()
pygame.quit()
```

---

<a id="package-management"></a>

## Package Management — [Back to Top](#table-of-contents)

<a id="start-a-new-project"></a>

### Start a New Project — [Back to Top](#table-of-contents)

```bash
# Create a virtual environment and install gui_do
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux

pip install gui_do
```

<a id="add-to-or-update-an-existing-project"></a>

### Add to or Update an Existing Project — [Back to Top](#table-of-contents)

```bash
# Add to an existing project
pip install gui_do

# Upgrade to the latest version
pip install --upgrade gui_do
```

---

<a id="application-bootstrap"></a>

## Application Bootstrap — [Back to Top](#table-of-contents)

<a id="guiapplication"></a>

### GuiApplication — [Back to Top](#table-of-contents)

`GuiApplication` is the central runtime coordinator. It owns the scene graph, input pipeline, focus, scheduler, overlay stack, theme, and all sub-managers.

```python
import pygame
from gui_do import GuiApplication

pygame.init()
surface = pygame.display.set_mode((800, 600))
app = GuiApplication(surface)
```

**Key attributes:**

| Attribute | Type | Description |
|---|---|---|
| `app.surface` | `pygame.Surface` | The display surface passed at construction |
| `app.scene` | `Scene` | Active scene graph root |
| `app.theme` | `ColorTheme` | Active colour palette and font manager |
| `app.layout` | `LayoutManager` | Grid and linear layout helpers |
| `app.window_tiling` | `WindowTilingManager` | Window snap and tile helpers |
| `app.scheduler` | `TaskScheduler` | Background thread-pool task runner |
| `app.timers` | `Timers` | Frame-driven repeating and one-shot timers |
| `app.tweens` | `TweenManager` | Property interpolation with easing |
| `app.overlay` | `OverlayManager` | Floating overlay controls |
| `app.toasts` | `ToastManager` | Ephemeral notification banners |
| `app.dialogs` | `DialogManager` | Modal alert / confirm / prompt dialogs (lazy) |
| `app.drag_drop` | `DragDropManager` | Mouse drag-and-drop session state |
| `app.focus` | `FocusManager` | Keyboard focus tracking |
| `app.actions` | `ActionManager` | Named actions with key bindings |
| `app.events` | `EventBus` | Scoped pub-sub for UI events |
| `app.invalidation` | `InvalidationTracker` | Frame-dirty tracking |
| `app.graphics_factory` | `BuiltInGraphicsFactory` | Visual surface builder |
| `app.features` | `FeatureManager` | Feature lifecycle host |
| `app.running` | `bool` | Set to `False` to stop the loop |

**Manual loop methods** (used when not using `UiEngine`):

```python
for event in pygame.event.get():
    app.process_event(event)

dt = clock.tick(60) / 1000.0
app.update(dt)

dirty = app.draw()
if dirty:
    pygame.display.update(dirty)
else:
    pygame.display.flip()

# On exit:
app.shutdown()
```

**Add a node to the active scene:**

```python
node = app.add(my_control)           # adds to default scene
node = app.add(my_control, scene_name="hud")   # adds to named scene
```

**Screen lifecycle callbacks** (draw-cycle hooks for non-Feature code):

```python
app.set_screen_lifecycle(
    preamble=lambda: surface.fill((30, 30, 40)),      # called before update
    event_handler=lambda event: False,                 # return True to consume
    postamble=lambda: None,                            # called after update
)
```

`chain_screen_lifecycle()` adds an additional layer without replacing the base; it returns a disposer callable.

<a id="uiengine"></a>

### UiEngine — [Back to Top](#table-of-contents)

`UiEngine` wraps the main loop: processes events, ticks the clock, calls `update()` and `draw()`, and calls `shutdown()` on exit.

```python
from gui_do import UiEngine

engine = UiEngine(app, target_fps=60)
frames = engine.run()           # blocks until app.running is False
print(engine.current_fps)       # measured FPS from last clock tick
```

`run(max_frames=None)` accepts an optional frame limit and returns the total frame count.

<a id="scene-management"></a>

### Scene Management — [Back to Top](#table-of-contents)

Applications can register multiple named scenes. Only the active scene is drawn and dispatched; inactive scene schedulers are automatically paused.

```python
# Access or lazily create a scene by name
hud_scene = app.create_scene("hud")

# Switch the active scene; inactive scenes are paused automatically
app.switch_scene("hud")

print(app.active_scene_name)     # "hud"
print(app.scene_names())         # ["default", "hud"]
print(app.has_scene("hud"))      # True

# Remove a non-active scene and shut down its scheduler
removed = app.remove_scene("hud")

# Access another scene's scheduler
sched = app.get_scene_scheduler("hud")
```

Each scene has its own independent `scheduler`, `timers`, `tweens`, `overlay`, `drag_drop`, `window_tiling`, `theme`, and `graphics_factory`. These are swapped onto `app.*` when `switch_scene()` is called.

**Pristine background:** A scene can store a background bitmap that is restored before each draw.

```python
app.set_pristine(source_surface)          # store background for active scene
app.restore_pristine()                    # blit background; returns True if set
```

<a id="cursor-management"></a>

### Cursor Management — [Back to Top](#table-of-contents)

gui_do hides the hardware cursor and manages cursor rendering internally.

```python
app.register_cursor("crosshair", "assets/crosshair.png", hotspot=(8, 8))
app.set_cursor("crosshair")    # switch to named cursor
app.set_cursor(None)           # clear (use default)
```

---

<a id="controls"></a>

## Controls — [Back to Top](#table-of-contents)

<a id="common-pattern-and-uinode-api"></a>

### Common Pattern and UiNode API — [Back to Top](#table-of-contents)

Every control inherits from `UiNode`. All controls share these attributes and methods:

```python
node.control_id    # str — unique identifier
node.rect          # pygame.Rect — bounding box
node.visible       # bool — included in draw pass
node.enabled       # bool — included in event dispatch
node.tab_index     # int — keyboard focus order; negative to exclude
node.parent        # UiNode or None — parent in scene tree
node.children      # list[UiNode]

node.add(child)         # attach a child node; returns child
node.remove(child)      # detach a child node
node.invalidate()       # mark dirty (propagates to ancestors)

node.set_accessibility(role="button", label="Submit")
```

Controls are added to the scene graph:

```python
btn = app.scene.add(ButtonControl("btn", rect, "OK"))
panel = app.scene.add(PanelControl("panel", rect))
label = panel.add(LabelControl("lbl", label_rect, "Hello"))
```

**Drag-and-drop hooks** (override on custom `UiNode` subclasses):

```python
def on_drag_start(self, event) -> "DragPayload | None":
    # Return a DragPayload to begin a drag, or None to decline
    return DragPayload(drag_id="item", data=self.data)

def on_drag_end(self, accepted: bool) -> None:
    pass

def accepts_drop(self, payload: "DragPayload") -> bool:
    return True

def on_drag_enter(self, payload: "DragPayload") -> None:
    pass

def on_drag_leave(self, payload: "DragPayload") -> None:
    pass

def on_drop(self, payload: "DragPayload", pos) -> bool:
    return True   # True = accepted
```

<a id="panelcontrol"></a>

### PanelControl — [Back to Top](#table-of-contents)

A plain rectangular container. Draws a themed panel background and clips child rendering to its bounds.

```python
from gui_do import PanelControl

panel = app.scene.add(PanelControl("panel", Rect(10, 10, 400, 300)))
label = panel.add(LabelControl("lbl", Rect(20, 20, 200, 30), "Inside panel"))
```

<a id="labelcontrol"></a>

### LabelControl — [Back to Top](#table-of-contents)

Static text display.

```python
from gui_do import LabelControl

label = app.scene.add(LabelControl("lbl", Rect(20, 20, 200, 32), "Hello"))

label.text = "Updated text"     # update at runtime
label.font_role = "title"       # "body" | "title" | "display" | any registered role
```

<a id="buttoncontrol"></a>

### ButtonControl — [Back to Top](#table-of-contents)

Clickable button with label.

```python
from gui_do import ButtonControl

def on_submit():
    print("submitted")

btn = app.scene.add(
    ButtonControl("submit_btn", Rect(20, 60, 120, 36), "Submit", on_click=on_submit)
)

btn.label = "Save"              # change label at runtime
btn.on_click = on_submit        # replace callback at runtime
btn.enabled = False             # disable without removing
```

<a id="togglecontrol"></a>

### ToggleControl — [Back to Top](#table-of-contents)

A checkbox-style toggle with a label.

```python
from gui_do import ToggleControl

toggle = app.scene.add(
    ToggleControl(
        "dark_mode",
        Rect(20, 100, 200, 32),
        "Dark mode",
        checked=False,
        on_change=lambda checked: print("dark:", checked),
    )
)

print(toggle.checked)       # bool
toggle.checked = True       # set programmatically
toggle.toggle()             # flip state
```

<a id="arrowboxcontrol"></a>

### ArrowBoxControl — [Back to Top](#table-of-contents)

A numeric stepper with increment/decrement arrow buttons and a center label that displays the current value.

```python
from gui_do import ArrowBoxControl

box = app.scene.add(
    ArrowBoxControl(
        "quantity",
        Rect(20, 140, 160, 36),
        label="Qty",
        value=1,
        minimum=1,
        maximum=10,
        step=1,
        on_change=lambda v, reason: print("qty:", v),
    )
)

print(box.value)            # current int or float value
box.value = 5               # set programmatically
box.minimum = 0
box.maximum = 20
box.step = 2
```

<a id="buttongroupcontrol"></a>

### ButtonGroupControl — [Back to Top](#table-of-contents)

A row of mutually exclusive radio-button-style buttons. Exactly one button is always selected.

```python
from gui_do import ButtonGroupControl

group = app.scene.add(
    ButtonGroupControl(
        "view_mode",
        Rect(20, 180, 300, 36),
        buttons=["List", "Grid", "Table"],
        selected_index=0,
        on_change=lambda idx: print("mode:", idx),
    )
)

print(group.selected_index)         # int
group.selected_index = 1            # select programmatically
print(group.labels)                 # list[str]
group.select(2)                     # select by index
```

<a id="slidercontrol"></a>

### SliderControl — [Back to Top](#table-of-contents)

A numeric range input with capture-locked drag. Callbacks receive `(value, ValueChangeReason)`.

```python
from gui_do import SliderControl, LayoutAxis, ValueChangeReason

def on_change(value: float, reason: ValueChangeReason) -> None:
    if reason is ValueChangeReason.MOUSE_DRAG:
        print("dragged to", value)

slider = app.scene.add(
    SliderControl(
        "volume",
        Rect(20, 220, 300, 24),
        axis=LayoutAxis.HORIZONTAL,
        minimum=0.0,
        maximum=1.0,
        value=0.5,
        on_change=on_change,
    )
)

slider.value                            # current float
slider.set_value(0.75)                  # set absolute, clamped; returns True if changed
slider.adjust_value(0.1)               # move by delta, clamped; returns True if changed
slider.set_normalized(0.5)             # set from 0.0–1.0 ratio; returns True if changed
slider.normalized                      # current value as 0.0–1.0 ratio
slider.handle_rect()                   # pygame.Rect of the drag handle
slider.set_on_change_callback(new_cb)  # replace callback at runtime
```

`ValueChangeReason` members:

| Member | Trigger |
|---|---|
| `KEYBOARD` | Arrow keys, Home, End, PageUp, PageDown |
| `MOUSE_DRAG` | Handle drag |
| `WHEEL` | Mouse scroll wheel |
| `PROGRAMMATIC` | `set_value()`, `adjust_value()`, `set_normalized()` |

<a id="scrollbarcontrol"></a>

### ScrollbarControl — [Back to Top](#table-of-contents)

A viewport scrollbar. `content_size` is the total scrollable length, `viewport_size` is the visible window, `offset` is the current position.

```python
from gui_do import ScrollbarControl, LayoutAxis, ValueChangeReason

scrollbar = app.scene.add(
    ScrollbarControl(
        "vscroll",
        Rect(388, 10, 12, 280),
        axis=LayoutAxis.VERTICAL,
        content_size=2000,
        viewport_size=280,
        offset=0,
        step=20,
        on_change=lambda offset, reason: print(offset, reason),
    )
)

scrollbar.offset                           # current int position
scrollbar.scroll_fraction                  # 0.0–1.0 normalized position
scrollbar.set_offset(400)                  # set absolute, clamped; returns True if changed
scrollbar.adjust_offset(20)               # relative move, clamped; returns True if changed
scrollbar.handle_rect()                   # pygame.Rect of the drag handle
scrollbar.set_on_change_callback(new_cb)  # replace callback at runtime

# Update geometry at runtime (e.g., when content length changes)
scrollbar.content_size = 3000
scrollbar.viewport_size = 280
```

`ValueChangeReason` applies the same way as `SliderControl`. `set_offset()` and `adjust_offset()` trigger `PROGRAMMATIC`.

<a id="textinputcontrol"></a>

### TextInputControl — [Back to Top](#table-of-contents)

A single-line text entry field with cursor, selection, placeholder, optional masking, and focus-aware keyboard handling.

```python
from gui_do import TextInputControl

field = app.scene.add(
    TextInputControl(
        "username",
        Rect(20, 260, 280, 36),
        value="",
        placeholder="Enter username",
        max_length=64,
        masked=False,
        on_change=lambda text: print("changed:", text),
        on_submit=lambda text: print("submitted:", text),
        font_role="body",
    )
)

field.value                     # current str
field.placeholder               # hint text shown when empty
field.max_length                # int or None
field.masked                    # bool — renders as *** when True
field.set_value("admin")        # set programmatically; does NOT fire on_change
field.cursor_pos                # int — caret position
field.selection_range           # (int, int) — start/end of selection
field.select_all()              # select all text
field.clear_selection()         # deselect without deleting
```

`on_change` fires on every keystroke. `on_submit` fires on Enter. `set_value()` is silent — it does not fire `on_change`.

<a id="listviewcontrol"></a>

### ListViewControl — [Back to Top](#table-of-contents)

A scrollable single- or multi-select list.

```python
from gui_do import ListViewControl, ListItem

lv = app.scene.add(
    ListViewControl(
        "files",
        Rect(20, 300, 280, 160),
        items=[
            ListItem("document.txt", value="doc.txt"),
            ListItem("image.png", value="img.png", enabled=True, data={"size": 1024}),
        ],
        on_select=lambda idx, item: print("selected:", item.label),
        multi_select=False,
        row_height=24,
        font_role="body",
    )
)

lv.selected_index               # int — first selected index (-1 when empty)
lv.selected_indices             # list[int]
lv.selected_item                # ListItem or None
lv.scroll_offset                # int — pixel scroll position
lv.item_count()                 # int

lv.set_items([ListItem("new.txt")])     # replace all items
lv.append_item(ListItem("extra.txt"))  # add to end
lv.insert_item(0, ListItem("first"))   # insert at index
lv.remove_item(2)                      # remove by index; returns True if removed

lv.select(1, scroll_to=True)   # programmatic selection
lv.deselect_all()
lv.scroll_to_item(3)
lv.scroll_to_top()
lv.scroll_to_bottom()
```

`ListItem(label, value=None, enabled=True, data=None)` — `data` is arbitrary and not rendered.

When items are non-empty, the control always has at least one selected item. Newly set items reset the selection to index 0.

<a id="dropdowncontrol"></a>

### DropdownControl — [Back to Top](#table-of-contents)

A collapsed selector that opens an overlay list of options. Always has one option selected when options are non-empty.

```python
from gui_do import DropdownControl, DropdownOption

dd = app.scene.add(
    DropdownControl(
        "theme_picker",
        Rect(20, 470, 200, 32),
        options=[
            DropdownOption("Dark", value="dark"),
            DropdownOption("Light", value="light"),
            DropdownOption("System", value="system", enabled=True, data=None),
        ],
        on_change=lambda idx, opt: print("selected:", opt.value),
        font_role="body",
    )
)

dd.selected_index               # int
dd.selected_index = 1           # set programmatically
dd.selected_option              # DropdownOption or None
dd.is_open                      # bool

dd.set_options([DropdownOption("Red"), DropdownOption("Blue")])
dd.open(app)                    # expand the dropdown
dd.close(app)                   # collapse the dropdown
```

`DropdownOption(label, value=None, enabled=True, data=None)`.

<a id="imagecontrol"></a>

### ImageControl — [Back to Top](#table-of-contents)

Renders a `pygame.Surface` scaled to fit its rect.

```python
from gui_do import ImageControl
import pygame

img_surface = pygame.image.load("logo.png").convert_alpha()
img = app.scene.add(ImageControl("logo", Rect(600, 10, 100, 100), surface=img_surface))

img.surface = new_surface       # replace at runtime
```

<a id="canvascontrol"></a>

### CanvasControl — [Back to Top](#table-of-contents)

A freeform drawing surface that forwards all events to a callback. Use for custom rendering and interaction.

```python
from gui_do import CanvasControl, CanvasEventPacket
from gui_do import EventType

def on_canvas_event(packet: CanvasEventPacket) -> bool:
    event = packet.event
    app = packet.app
    canvas = packet.canvas

    if event.kind == EventType.MOUSE_BUTTON_DOWN:
        pos = event.pos
        # draw to canvas.surface or manage your own state
        return True     # return True to consume, False to pass through

    return False

canvas = app.scene.add(
    CanvasControl("draw_area", Rect(20, 20, 760, 540), on_event=on_canvas_event)
)
```

`CanvasEventPacket` fields: `event` (`GuiEvent`), `app` (`GuiApplication`), `canvas` (`CanvasControl`).

<a id="framecontrol"></a>

### FrameControl — [Back to Top](#table-of-contents)

A bordered container that clips children to its content area.

```python
from gui_do import FrameControl

frame = app.scene.add(FrameControl("settings_frame", Rect(20, 80, 400, 300)))
frame.add(LabelControl("title", Rect(30, 90, 200, 28), "Settings"))
```

<a id="windowcontrol"></a>

### WindowControl — [Back to Top](#table-of-contents)

A draggable, titled sub-window with an optional close button. Windows are positioned absolutely within the scene.

```python
from gui_do import WindowControl

win = app.scene.add(
    WindowControl(
        "prefs_win",
        Rect(100, 80, 400, 300),
        title="Preferences",
        draggable=True,
        on_close=lambda: win.visible.__set__(win, False),
    )
)

win.title = "Options"
win.draggable = False
win.rect = Rect(200, 100, 400, 300)
```

<a id="splittercontrol"></a>

### SplitterControl — [Back to Top](#table-of-contents)

A two-pane container divided by a draggable splitter bar. Children are placed manually within `pane_a_rect` and `pane_b_rect`.

```python
from gui_do import SplitterControl, LayoutAxis

splitter = app.scene.add(
    SplitterControl(
        "main_split",
        Rect(0, 0, 800, 600),
        axis=LayoutAxis.HORIZONTAL,       # left/right panes
        ratio=0.3,                         # 30% for pane A
        min_pane_size=80,
        on_ratio_changed=lambda r: print("ratio:", r),
        divider_thickness=6,
    )
)

splitter.ratio                  # float 0.0–1.0
splitter.ratio = 0.5            # set programmatically
splitter.axis                   # LayoutAxis
splitter.is_horizontal          # bool
splitter.pane_a_rect            # pygame.Rect — left/top pane
splitter.pane_b_rect            # pygame.Rect — right/bottom pane
```

Typical use: add child controls whose rects match `pane_a_rect` and `pane_b_rect`, and update their positions in `on_ratio_changed`.

<a id="taskpanelcontrol"></a>

### TaskPanelControl — [Back to Top](#table-of-contents)

A panel that slides in when hovered and hides when not, suitable for toolbars or status panels. Extends `PanelControl`.

```python
from gui_do import TaskPanelControl

task_panel = app.scene.add(
    TaskPanelControl(
        "toolbar",
        Rect(0, 0, 800, 40),
        auto_hide=True,
        hidden_peek_pixels=4,
        animation_step_px=4,
        dock_bottom=False,          # True = hide downward
    )
)

task_panel.auto_hide = False                   # disable auto-hide
task_panel.set_hidden_peek_pixels(8)
task_panel.set_animation_step_px(6)

# Children track the panel's position automatically:
task_panel.add(ButtonControl("save_btn", Rect(10, 5, 80, 30), "Save"))
```

<a id="overlaypanelcontrol"></a>

### OverlayPanelControl — [Back to Top](#table-of-contents)

Base class for panels used as overlay content via `OverlayManager`. Create an `OverlayPanelControl` (or a subclass) and pass it to `app.overlay.show()`.

```python
from gui_do import OverlayPanelControl

panel = OverlayPanelControl("my_overlay", Rect(100, 100, 300, 200), draw_background=True)
panel.add(LabelControl("msg", Rect(110, 120, 280, 30), "Floating panel"))

handle = app.overlay.show(
    "my_overlay",
    panel,
    dismiss_on_outside_click=True,
    dismiss_on_escape=True,
    on_dismiss=lambda: print("dismissed"),
)
```

<a id="datagridcontrol"></a>

### DataGridControl — [Back to Top](#table-of-contents)

A virtualized multi-column table with sortable headers, column resize, keyboard navigation, and an optional scrollbar.

```python
from gui_do import DataGridControl, GridColumn, GridRow

grid = app.scene.add(
    DataGridControl(
        "results",
        Rect(20, 20, 760, 400),
        columns=[
            GridColumn(key="name",  title="Name",  width=200, sortable=True),
            GridColumn(key="size",  title="Size",  width=100, sortable=True),
            GridColumn(key="type",  title="Type",  width=80,  sortable=False),
        ],
        rows=[
            GridRow(data={"name": "file.txt", "size": "4 KB", "type": "Text"}, row_id=1),
            GridRow(data={"name": "image.png", "size": "128 KB", "type": "Image"}, row_id=2),
        ],
        row_height=26,
        show_scrollbar=True,
        font_role="medium",
        on_select=lambda idx, row: print("row selected:", row.data),
        on_sort=lambda col_key, ascending: print("sort:", col_key, ascending),
    )
)

grid.set_columns([GridColumn("id", "ID", width=60)])
grid.set_rows([GridRow({"id": "1"})])
grid.append_row(GridRow({"id": "2"}, row_id=2))
grid.remove_row(0)             # returns True if removed
grid.clear_rows()
grid.row_count                 # int
grid.selected_row_index        # int (-1 when none)
```

`GridColumn(key, title, width=120, sortable=True, min_width=20)`.
`GridRow(data, row_id=None)` — `data` is a `dict[str, Any]` keyed by column `key`.

---

<a id="layout"></a>

## Layout — [Back to Top](#table-of-contents)

<a id="layoutaxis"></a>

### LayoutAxis — [Back to Top](#table-of-contents)

An enum used by controls and layout helpers to specify orientation.

```python
from gui_do import LayoutAxis

LayoutAxis.HORIZONTAL
LayoutAxis.VERTICAL
```

<a id="layoutmanager"></a>

### LayoutManager — [Back to Top](#table-of-contents)

`app.layout` provides grid and linear layout helpers that compute control rects from configuration.

```python
from gui_do import LayoutManager

lm = app.layout

# Linear layout — evenly spaced items along a row or column
lm.set_linear_properties(
    anchor=(20, 20),     # top-left origin
    item_width=120,
    item_height=36,
    spacing=8,
    horizontal=True,     # False for vertical
    wrap_count=3,        # 0 = no wrapping
)
rect0 = lm.linear(0)        # pygame.Rect for item at index 0
rect1 = lm.next_linear()    # auto-increment cursor version

# Grid layout
lm.set_grid_properties(
    anchor=(20, 80),
    item_width=120,
    item_height=36,
    column_spacing=8,
    row_spacing=8,
)
rect_grid = lm.grid(col=0, row=1)
```

<a id="windowtilingmanager"></a>

### WindowTilingManager — [Back to Top](#table-of-contents)

`app.window_tiling` manages `WindowControl` instances: snapping to grid, tiling horizontally or vertically, and arranging windows into rows or columns within the application surface.

```python
app.window_tiling.tile_horizontal([win_a, win_b], rect=app.surface.get_rect(), gap=4)
app.window_tiling.tile_vertical([win_a, win_b, win_c], rect=app.surface.get_rect(), gap=4)
app.window_tiling.snap_to_grid(win, grid_size=16)
```

<a id="constraintlayout"></a>

### ConstraintLayout — [Back to Top](#table-of-contents)

Applies anchor-based rect derivation from a parent rect. Each registered node gets an `AnchorConstraint` that describes how its rect is computed from the parent's edges.

```python
from gui_do import ConstraintLayout, AnchorConstraint
from pygame import Rect

layout = ConstraintLayout()

layout.add(
    sidebar,
    AnchorConstraint(
        left=0,
        top=0,
        bottom=0,
        right=None,
        min_width=200,
        max_width=400,
    ),
)

layout.add(
    content,
    AnchorConstraint(
        left_frac=0.25,    # 25% from left edge
        right=0,
        top=0,
        bottom=0,
    ),
)

# Recompute and mutate all registered nodes' rects
layout.apply(parent_rect=app.surface.get_rect())

# Query without mutating
new_rect = layout.apply_to(sidebar, parent_rect)
print(layout.has(sidebar))     # True
print(layout.node_count())     # int
layout.remove(sidebar)
```

`AnchorConstraint` fields — all optional, `None` = unconstrained:

| Field | Description |
|---|---|
| `left`, `right`, `top`, `bottom` | Fixed pixel offset from the respective parent edge |
| `left_frac`, `right_frac`, `top_frac`, `bottom_frac` | Fractional offset (0.0–1.0 of parent dimension) |
| `min_width`, `max_width`, `min_height`, `max_height` | Size clamps applied after edge resolution |

When both edges along an axis are set, the size is derived from the gap between them. When only one edge is set, the node's current size is preserved.

---

<a id="events-and-input"></a>

## Events and Input — [Back to Top](#table-of-contents)

<a id="eventtype-eventphase-and-guievent"></a>

### EventType, EventPhase, and GuiEvent — [Back to Top](#table-of-contents)

`EventType` identifies the category of a normalized event:

```python
from gui_do import EventType

EventType.MOUSE_BUTTON_DOWN
EventType.MOUSE_BUTTON_UP
EventType.MOUSE_MOTION
EventType.MOUSE_WHEEL
EventType.KEY_DOWN
EventType.KEY_UP
EventType.TEXT_INPUT
EventType.FOCUS_GAINED
EventType.FOCUS_LOST
EventType.QUIT
```

`EventPhase` describes which direction the event is traveling through the node tree:

```python
from gui_do import EventPhase

EventPhase.CAPTURE     # root → target
EventPhase.BUBBLE      # target → root
```

`GuiEvent` is the normalized event object dispatched to `handle_event()`:

```python
from gui_do import GuiEvent, EventType

def handle_event(self, event: GuiEvent, app) -> bool:
    if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
        pos = event.pos          # (int, int) logical screen position
        return True

    if event.kind == EventType.KEY_DOWN:
        key = event.key          # pygame key constant
        if event.is_key_down(pygame.K_RETURN):
            return True

    if event.kind == EventType.MOUSE_WHEEL:
        dy = event.wheel[1]      # int — positive = scroll up
        return True

    return False
```

Key `GuiEvent` fields: `kind`, `pos`, `raw_pos`, `rel`, `button`, `key`, `mod`, `wheel`, `unicode`, `phase`. Helper: `is_key_down(key) -> bool`.

<a id="eventmanager"></a>

### EventManager — [Back to Top](#table-of-contents)

`app.event_manager` normalizes raw pygame events into `GuiEvent` objects. It is called internally by `app.process_event()`. In typical use you do not call it directly; events reach `handle_event()` on your controls automatically.

<a id="eventbus"></a>

### EventBus — [Back to Top](#table-of-contents)

`app.events` is a scoped pub-sub bus for non-input UI-to-UI messages.

```python
from gui_do import EventBus

# Subscribe to a topic; returns a Subscription object
sub = app.events.subscribe("selection_changed", lambda payload: print(payload))

# Subscribe with a scope tag for bulk unsubscription
sub2 = app.events.subscribe("state_updated", handler, scope="my_feature")

# Publish a payload to all subscribers of a topic
app.events.publish("selection_changed", {"id": 42})

# Unsubscribe one subscription
app.events.unsubscribe(sub)

# Unsubscribe all subscriptions for a scope; returns count removed
app.events.unsubscribe_scope("my_feature")

# Count active subscriptions
app.events.subscriber_count("selection_changed")
app.events.subscriber_count()                     # all topics
```

The `"toast"` topic is reserved: publishing `{"message": "...", "severity": "info"}` to it routes to `app.toasts`.

<a id="actionmanager"></a>

### ActionManager — [Back to Top](#table-of-contents)

`app.actions` maps named actions to handlers and key bindings.

```python
import pygame
from gui_do import ActionManager

# Register a named action handler
app.actions.register_action("save", lambda event: (save_document(), True)[1])

# Bind a key to an action (optional scene and window_only scope)
app.actions.bind_key(pygame.K_s, "save", scene=None, window_only=False)

# Remove a specific key binding
app.actions.unbind_key(pygame.K_s, "save")

# Unregister an action
app.actions.unregister_action("save")

# Query
app.actions.has_action("save")         # bool
app.actions.registered_actions()       # list[str]
app.actions.bindings_for_action("save")  # list[KeyBinding]
```

Action handlers receive the `GuiEvent` and should return `True` to consume it.

<a id="focusmanager"></a>

### FocusManager — [Back to Top](#table-of-contents)

`app.focus` tracks keyboard focus independently from window activation.

```python
# Set focus programmatically
app.focus.set_focus(my_node)
app.focus.set_focus(my_node, via_keyboard=True)  # show keyboard hint ring
app.focus.clear_focus()

# Query
app.focus.focused_node          # UiNode or None
app.focus.focused_control_id    # str or None

# Show keyboard hint for existing focus (e.g. after Tab press)
app.focus.show_keyboard_hint_for_current_focus()
```

Tab-order traversal is automatic — Tab/Shift-Tab cycles through nodes by ascending `tab_index`. Set `tab_index = -1` to exclude a node from traversal.

<a id="fontmanager"></a>

### FontManager — [Back to Top](#table-of-contents)

`FontManager` manages named font roles used by the theme and controls. It is accessed via `app.theme.fonts`.

```python
# Register a custom font role
app.theme.register_font_role(
    "mono",
    size=14,
    system_name="Courier New",   # or: file_path="path/to/font.ttf"
    bold=False,
    italic=False,
)

# Assign a role to a control
label.font_role = "mono"

# List registered roles
print(app.theme.font_roles())

# Render text directly (returns pygame.Surface)
surf = app.theme.render_text("Hello", role="title", shadow=True)
```

---

<a id="data-and-state"></a>

## Data and State — [Back to Top](#table-of-contents)

<a id="observablevalue-and-presentationmodel"></a>

### ObservableValue and PresentationModel — [Back to Top](#table-of-contents)

`ObservableValue[T]` wraps a value with a subscriber list that fires whenever the value changes.

```python
from gui_do import ObservableValue

count = ObservableValue(0)
print(count.value)           # 0

# Subscribe — returns an unsubscribe callable
unsub = count.subscribe(lambda new_val: print("count:", new_val))

count.value = 5              # fires subscribers
count.notify()               # fire subscribers without changing the value

unsub()                      # unsubscribe
```

`PresentationModel` is a base class for data models that expose `ObservableValue` fields:

```python
from gui_do import PresentationModel, ObservableValue

class AppState(PresentationModel):
    def __init__(self):
        self.selected_id = ObservableValue(None)
        self.zoom_level  = ObservableValue(1.0)

state = AppState()
state.selected_id.subscribe(lambda v: my_list.select_by_value(v))
state.selected_id.value = "item_42"
```

<a id="valuechangecallback-and-valuechangereason"></a>

### ValueChangeCallback and ValueChangeReason — [Back to Top](#table-of-contents)

Controls that expose a numeric or text value use a standardized callback signature:

```python
from gui_do import ValueChangeCallback, ValueChangeReason

# Callback signature: (value: T, reason: ValueChangeReason) -> None
def on_slider_change(value: float, reason: ValueChangeReason) -> None:
    if reason is ValueChangeReason.PROGRAMMATIC:
        return   # ignore programmatic updates if desired
    print(f"user changed value to {value} via {reason}")
```

`ValueChangeReason` members:

| Member | Value | Typical source |
|---|---|---|
| `KEYBOARD` | `"keyboard"` | Arrow keys, Home, End, Page keys |
| `PROGRAMMATIC` | `"programmatic"` | `set_value()`, `set_offset()`, etc. |
| `MOUSE_DRAG` | `"mouse_drag"` | Handle drag |
| `WHEEL` | `"wheel"` | Mouse scroll wheel |

<a id="formmodel-and-formfield"></a>

### FormModel and FormField — [Back to Top](#table-of-contents)

`FormModel` aggregates typed `FormField` instances with per-field validation and optional cross-field validation rules.

```python
from gui_do import FormModel, FormField, ValidationRule, FieldError

def min_length(n: int) -> ValidationRule:
    def rule(value) -> str | None:
        if len(str(value)) < n:
            return f"Must be at least {n} characters."
        return None
    return rule

form = FormModel()

name_field  = form.add_field("name", "", validators=[min_length(2)], required=True)
email_field = form.add_field("email", "")
age_field   = form.add_field("age", 0)

# Cross-field validator
def check_age(f: FormModel) -> list[FieldError] | None:
    if f.field("age").value.value < 18:
        return [FieldError("age", "Must be 18 or older.")]
    return None

form.add_cross_validator(check_age)

# Wire to a TextInputControl
name_field.value.subscribe(lambda v: name_input.set_value(v))

# Validate on submit
if form.validate_all():
    values = form.get_values()    # dict[str, Any]
    form.commit_all()
else:
    errors = form.get_errors()    # list[FieldError]

form.reset_all()    # revert all fields to last committed values
```

**`FormField[T]` API:**

```python
field.name                    # str
field.value                   # ObservableValue[T]
field.is_dirty                # bool — uncommitted change exists
field.is_valid                # bool
field.errors                  # list[str]
field.first_error             # str or None

field.add_validator(rule)     # add a ValidationRule at runtime
field.validate()              # bool — run validators, update errors
field.commit()                # accept current value as baseline
field.reset()                 # revert to baseline

# Subscribe to error changes
unsub = field.on_errors_changed(lambda errors: print(errors))
```

`ValidationRule = Callable[[Any], Optional[str]]` — return a string message on failure, `None` on success.

`FieldError(field_name, message)` — returned by `form.get_errors()` and cross validators.

**`FormModel` aggregate API:**

```python
form.field("name")            # FormField by name
form.fields                   # dict[str, FormField]
form.is_valid                 # bool — all fields valid and no cross errors
form.is_dirty                 # bool — any field has uncommitted change
form.cross_errors             # list[FieldError] from cross validators
form.validate_all()           # bool — validate all fields + cross validators
form.commit_all()             # commit all fields
form.reset_all()              # reset all fields and clear cross errors
form.get_values()             # dict[str, Any] snapshot
form.get_errors()             # list[FieldError] all field + cross errors
```

---

<a id="scheduling-and-animation"></a>

## Scheduling and Animation — [Back to Top](#table-of-contents)

<a id="taskscheduler"></a>

### TaskScheduler — [Back to Top](#table-of-contents)

`app.scheduler` runs background tasks on a thread pool. Tasks can post incremental results back to the UI thread via a message method. Results are dispatched during `app.update()` within a time budget to avoid frame jank.

```python
from gui_do import TaskScheduler, TaskEvent

def background_logic(params):
    # Runs on a worker thread
    result = do_heavy_work(params["path"])
    return result

def on_message(partial_result):
    # Called on the UI thread with incremental updates
    progress_bar.value = partial_result

app.scheduler.add_task(
    task_id="import_file",
    logic=background_logic,
    parameters={"path": "data.csv"},
    message_method=on_message,
)

# Suspend / resume individual tasks
app.scheduler.suspend_tasks("import_file")
app.scheduler.resume_tasks("import_file")

# Suspend / resume all tasks
app.scheduler.suspend_all()
app.scheduler.resume_all()

# Pause entire scheduler (e.g., during scene switch)
app.scheduler.set_execution_paused(True)
app.scheduler.is_execution_paused()

# Remove tasks
app.scheduler.remove_tasks("import_file")
app.scheduler.remove_all()
app.scheduler.shutdown()

# Recommended worker count for the current machine
workers = TaskScheduler.recommended_worker_count()
```

`TaskEvent(operation, task_id, error)` appears in the scheduler's finished and failed event lists.

<a id="timers"></a>

### Timers — [Back to Top](#table-of-contents)

`app.timers` provides frame-driven repeating and one-shot callbacks. Timers fire during `app.update()`.

```python
from gui_do import Timers

# Repeating timer
app.timers.add_timer("autosave", interval_seconds=30.0, callback=save_document)

# One-shot timer
app.timers.add_once("splash_hide", delay_seconds=3.0, callback=lambda: (setattr(splash, "visible", False)))

# Query
app.timers.has_timer("autosave")       # bool
app.timers.timer_ids()                 # list of all timer ids

# Cancel
app.timers.remove_timer("autosave")
app.timers.cancel_all()                # returns int count removed

# Change interval without losing elapsed progress
app.timers.reschedule("autosave", new_interval_seconds=60.0)
```

<a id="tweenmanager"></a>

### TweenManager — [Back to Top](#table-of-contents)

`app.tweens` interpolates object attributes over time. All tweens are driven by `app.update()`.

```python
from gui_do import TweenManager, TweenHandle, Easing

# Animate an attribute from its current value to an end value
handle = app.tweens.tween(
    target=panel,
    attr="rect",                      # any attribute with tuple or float value
    end_value=(100, 100, 300, 200),   # target rect (or float)
    duration_seconds=0.4,
    easing=Easing.EASE_OUT,
    on_complete=lambda: print("done"),
    tag="panel_anim",
)

# Animate a plain float attribute
app.tweens.tween(label, "alpha", 0.0, 0.3, easing=Easing.EASE_IN)

# Low-level: call an arbitrary function each frame with eased t (0.0–1.0)
def on_frame(t: float) -> None:
    panel.rect.x = int(start_x + (end_x - start_x) * t)

handle2 = app.tweens.tween_fn(
    duration_seconds=0.5,
    fn=on_frame,
    easing=Easing.EASE_IN_OUT,
    on_complete=None,
    tag="slide",
)

# TweenHandle API
handle.tween_id                     # int
handle.is_complete                  # bool
handle.is_cancelled                 # bool
handle.elapsed_fraction()           # float 0.0–1.0 progress
handle.cancel()                     # cancel this tween

# Cancel by manager
app.tweens.cancel(handle)
app.tweens.cancel_all_for_tag("panel_anim")  # cancel all tweens with tag
app.tweens.cancel_all()                       # cancel all active tweens
```

`Easing` members: `LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`.

Custom easing: pass any `Callable[[float], float]` or a string `"linear"`, `"ease_in"`, `"ease_out"`, `"ease_in_out"`.

---

<a id="overlay-and-notifications"></a>

## Overlay and Notifications — [Back to Top](#table-of-contents)

<a id="overlaymanager"></a>

### OverlayManager — [Back to Top](#table-of-contents)

`app.overlay` manages a stack of floating `OverlayPanelControl` instances that receive input priority over the scene.

```python
from gui_do import OverlayManager, OverlayHandle

panel = OverlayPanelControl("popup", Rect(200, 150, 400, 300))
panel.add(LabelControl("msg", Rect(210, 160, 380, 30), "Popup content"))

handle: OverlayHandle = app.overlay.show(
    owner_id="my_popup",
    control=panel,
    dismiss_on_outside_click=True,
    dismiss_on_escape=True,
    on_dismiss=lambda: print("closed"),
)

# OverlayHandle API
handle.dismiss()          # close programmatically
handle.is_open            # bool

# OverlayManager API
app.overlay.hide("my_popup")           # hide by owner_id; returns bool
app.overlay.hide_all()                 # hide all; returns count
app.overlay.has_overlay("my_popup")    # bool
app.overlay.overlay_count()            # int
app.overlay.point_in_any_overlay(pos)  # bool — is pos inside any overlay?
```

<a id="toastmanager"></a>

### ToastManager — [Back to Top](#table-of-contents)

`app.toasts` shows ephemeral notification banners in a corner of the screen.

```python
from gui_do import ToastManager, ToastHandle, ToastSeverity

handle: ToastHandle = app.toasts.show(
    message="File saved.",
    title="Success",                        # optional header
    severity=ToastSeverity.SUCCESS,
    duration_seconds=3.0,                   # None = stays until dismissed
    icon=None,                              # reserved for future use
)

# ToastHandle API
handle.dismiss()         # close immediately
handle.is_visible        # bool

# Trigger via EventBus
app.events.publish("toast", {
    "message": "Operation complete.",
    "severity": "success",
    "duration_seconds": 4.0,
})
```

`ToastSeverity` members: `INFO`, `SUCCESS`, `WARNING`, `ERROR`.

<a id="dialogmanager"></a>

### DialogManager — [Back to Top](#table-of-contents)

`app.dialogs` provides modal alert, confirm, and prompt dialogs (lazily initialized on first access).

```python
from gui_do import DialogManager, DialogHandle

# Alert dialog
handle = app.dialogs.show_alert(
    title="Error",
    message="File not found.",
    button_label="OK",
    on_close=lambda: print("dismissed"),
    width=320,
)

# Confirm dialog
handle = app.dialogs.show_confirm(
    title="Delete?",
    message="This action cannot be undone.",
    confirm_label="Delete",
    cancel_label="Cancel",
    on_confirm=lambda: delete_item(),
    on_cancel=lambda: print("cancelled"),
    width=320,
    dangerous=True,              # True = confirm button styled as destructive
)

# Prompt dialog
handle = app.dialogs.show_prompt(
    title="Rename",
    prompt="Enter a new name:",
    default_value="Untitled",
    placeholder="Name",
    max_length=128,
    masked=False,
    on_submit=lambda text: rename_item(text),
    on_cancel=lambda: print("cancelled"),
    width=320,
)

# DialogHandle API
handle.dismiss()         # close programmatically
handle.is_open           # bool
```

<a id="contextmenumanager"></a>

### ContextMenuManager — [Back to Top](#table-of-contents)

`ContextMenuManager` displays a click-positioned context menu via `OverlayManager`. It auto-dismisses on outside click or Escape.

```python
from gui_do import ContextMenuManager, ContextMenuItem, ContextMenuHandle

cm = ContextMenuManager(app)

handle: ContextMenuHandle = cm.show(
    pos=(mouse_x, mouse_y),
    items=[
        ContextMenuItem("Cut",   action=on_cut,  enabled=True),
        ContextMenuItem("Copy",  action=on_copy, enabled=True),
        ContextMenuItem("",      separator=True),           # divider
        ContextMenuItem("Paste", action=on_paste, enabled=clipboard_has_content),
        ContextMenuItem("Delete", action=on_delete, enabled=True),
    ],
    on_dismiss=lambda: print("menu closed"),
)

# ContextMenuHandle API
handle.menu_id            # str
handle.dismiss()          # close programmatically
handle.is_open            # bool

# ContextMenuManager API
cm.dismiss("menu_id")     # bool
cm.dismiss_all()          # int — count dismissed
cm.has_menu("menu_id")    # bool
```

`ContextMenuItem(label, action=None, enabled=True, separator=False, icon=None)`. Set `separator=True` for a horizontal divider (label is ignored).

<a id="dragdropmanager"></a>

### DragDropManager — [Back to Top](#table-of-contents)

`app.drag_drop` coordinates mouse drag-and-drop sessions. It routes mouse events from `app.process_event()` to the appropriate `UiNode` hooks automatically once a drag is initiated.

```python
from gui_do import DragDropManager, DragPayload

# Query drag state
app.drag_drop.is_active          # bool — drag threshold met
app.drag_drop.active_payload     # DragPayload or None
```

Drag-and-drop is implemented by overriding hooks on `UiNode` subclasses:

```python
from gui_do import DragPayload
import pygame

class DraggableCard(UiNode):
    def on_drag_start(self, event) -> "DragPayload | None":
        # Called on mouse-down; return a payload to begin a drag
        ghost = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        ghost.fill((100, 150, 200, 160))
        return DragPayload(
            drag_id="card",
            data={"id": self.card_id},
            ghost_surface=ghost,
            ghost_offset=(0, 0),
        )

    def on_drag_end(self, accepted: bool) -> None:
        # Called when drag ends; accepted=True if a drop target accepted it
        pass

class DropZone(UiNode):
    def accepts_drop(self, payload: DragPayload) -> bool:
        return payload.drag_id == "card"

    def on_drag_enter(self, payload: DragPayload) -> None:
        self.highlight = True
        self.invalidate()

    def on_drag_leave(self, payload: DragPayload) -> None:
        self.highlight = False
        self.invalidate()

    def on_drop(self, payload: DragPayload, pos) -> bool:
        self.receive_card(payload.data["id"])
        return True   # True = accepted
```

`DragPayload(drag_id, data=None, ghost_surface=None, ghost_offset=(0, 0))`.

---

<a id="command-history"></a>

## Command History — [Back to Top](#table-of-contents)

A bounded undo/redo stack. Commands implement the `Command` protocol. Transactions group multiple commands into a single undoable unit.

```python
from gui_do import CommandHistory, Command, CommandTransaction

class RenameCommand:
    """Implements the Command protocol."""
    def __init__(self, node, old_name: str, new_name: str):
        self.description = f"Rename '{old_name}' → '{new_name}'"
        self._node = node
        self._old = old_name
        self._new = new_name

    def execute(self) -> None:
        self._node.name = self._new

    def undo(self) -> None:
        self._node.name = self._old

history = CommandHistory(max_size=100)

# Push and execute a command
history.push(RenameCommand(node, "old", "new"))

# Push without executing (e.g. command was already applied)
history.push(RenameCommand(node, "old", "new"), execute=False)

# Undo / redo
if history.can_undo:
    history.undo()
if history.can_redo:
    history.redo()

# Inspect the stack
history.undo_description    # str or None
history.redo_description    # str or None
history.undo_stack_size     # int
history.redo_stack_size     # int

# Transactions
tx = history.begin_transaction("Bulk edit")
history.push(cmd_a)         # added to open transaction
history.push(cmd_b)
history.end_transaction()   # commits as one undo entry

# Or as a context manager (via begin/end):
tx = history.begin_transaction("Paste")
history.push(paste_cmd)
history.end_transaction()
```

`Command` protocol — implement `description: str`, `execute() -> None`, and `undo() -> None`.

`CommandTransaction(description)`: `add(command)`, `execute()`, `undo()`, `len()`.

---

<a id="feature-system"></a>

## Feature System — [Back to Top](#table-of-contents)

Features are the primary unit for organizing application logic. Each Feature owns a rect in the scene, manages its own controls, and receives lifecycle events.

<a id="feature"></a>

### Feature — [Back to Top](#table-of-contents)

`Feature` is the abstract base class. Override lifecycle methods to build UI and respond to updates.

```python
from gui_do import Feature, FeatureMessage

class StatusBarFeature(Feature):
    def __init__(self):
        super().__init__("status_bar")
        self._label = None

    def build_ui(self, app, rect, ui):
        # ui exposes constructor types: ui.label_control_cls, ui.button_control_cls, etc.
        self._label = app.scene.add(ui.label_control_cls("status_lbl", rect, "Ready"))

    def on_mount(self, app) -> None:
        app.events.subscribe("status", self._on_status, scope=self.name)

    def on_unmount(self, app) -> None:
        app.events.unsubscribe_scope(self.name)

    def on_update(self, app, dt_seconds: float) -> None:
        pass  # called every frame while mounted

    def on_message(self, message: FeatureMessage) -> None:
        if message.topic == "refresh":
            self._label.text = "Refreshed"

    def _on_status(self, payload) -> None:
        self._label.text = str(payload)
```

**`Feature` lifecycle:**

| Override | Called when |
|---|---|
| `build_ui(app, rect, ui)` | Feature is being constructed; build your controls here |
| `on_mount(app)` | Feature is added to the FeatureManager |
| `on_unmount(app)` | Feature is removed from the FeatureManager |
| `on_update(app, dt_seconds)` | Every frame while mounted |
| `on_message(message)` | A `FeatureMessage` is routed to this feature |

<a id="directfeature"></a>

### DirectFeature — [Back to Top](#table-of-contents)

`DirectFeature` handles pygame-style events directly, as if it were a control. Override `handle_event()` and draw to `app.surface` from `update()` or a preamble.

```python
from gui_do import DirectFeature

class BackgroundFeature(DirectFeature):
    def build_ui(self, app, rect, ui):
        self._rect = rect

    def handle_event(self, event, app) -> bool:
        if event.kind == EventType.MOUSE_BUTTON_DOWN:
            return True
        return False

    def on_update(self, app, dt_seconds: float) -> None:
        pygame.draw.rect(app.surface, (30, 30, 40), self._rect)
```

<a id="logicfeature"></a>

### LogicFeature — [Back to Top](#table-of-contents)

`LogicFeature` separates a UI-building phase from a headless logic host. The logic host runs on the background scheduler. Override `build_logic(params)` for the threaded work and `build_ui(app, rect, ui)` for the controls.

```python
from gui_do import LogicFeature

class DataLoaderFeature(LogicFeature):
    def build_ui(self, app, rect, ui):
        self._status = app.scene.add(ui.label_control_cls("status", rect, "Loading..."))

    def build_logic(self, params):
        # Runs on a worker thread
        return load_data(params["source"])

    def on_logic_result(self, app, result) -> None:
        self._status.text = f"Loaded {len(result)} records"
```

<a id="routedfeature"></a>

### RoutedFeature — [Back to Top](#table-of-contents)

`RoutedFeature` routes incoming `FeatureMessage` objects to named handler methods by examining `message.command` or `message.topic`.

```python
from gui_do import RoutedFeature, FeatureMessage

class EditorFeature(RoutedFeature):
    def build_ui(self, app, rect, ui):
        pass

    def route_save(self, message: FeatureMessage, app) -> None:
        save_document(message.get("path"))

    def route_close(self, message: FeatureMessage, app) -> None:
        app.running = False
```

Method names follow the pattern `route_<command>`. Incoming messages with `command="save"` dispatch to `route_save`.

<a id="featuremessage"></a>

### FeatureMessage — [Back to Top](#table-of-contents)

The structured message envelope for inter-feature communication.

```python
from gui_do import FeatureMessage

msg = FeatureMessage(sender="toolbar", target="editor", payload={"command": "save", "path": "doc.txt"})

msg.sender           # str
msg.target           # str
msg.payload          # dict[str, Any]
msg.topic            # Optional[str] — payload["topic"] if present
msg.command          # Optional[str] — payload["command"] if present
msg.event            # Optional[str] — payload["event"] if present
msg["path"]          # dict item access
msg.get("path", "")  # dict get with default

# Factory helper
msg2 = FeatureMessage.from_payload("toolbar", "editor", {"command": "save"})
```

<a id="featuremanager"></a>

### FeatureManager — [Back to Top](#table-of-contents)

`app.features` hosts all mounted Feature instances.

```python
from gui_do import FeatureManager

# Mount a feature at a rect
app.features.mount(StatusBarFeature(), rect=Rect(0, 560, 800, 40))

# Remove a feature
app.features.remove("status_bar")

# Send a message to a feature by name
app.features.send_message(FeatureMessage("app", "editor", {"command": "refresh"}))
```

---

<a id="theme-and-graphics"></a>

## Theme and Graphics — [Back to Top](#table-of-contents)

<a id="colortheme"></a>

### ColorTheme — [Back to Top](#table-of-contents)

`app.theme` provides the colour palette and font rendering used by all controls.

```python
from gui_do import ColorTheme

# Palette attributes (RGB tuples)
app.theme.light          # light panel color
app.theme.medium         # medium panel color
app.theme.dark           # dark panel / shadow color
app.theme.background     # window background color
app.theme.highlight      # selection / focus highlight color
app.theme.text           # default text color
app.theme.shadow         # text shadow color

# Register a custom font role
app.theme.register_font_role("code", size=13, system_name="Courier New")

# Render text to a Surface
surf = app.theme.render_text("Hello", role="title", color=(255, 255, 255), shadow=True)

# List registered roles
app.theme.font_roles()   # tuple[str, ...]
```

Default roles: `"body"` (16 px), `"title"` (14 px bold), `"display"` (72 px bold). Controls also accept `"medium"` via the system default.

<a id="builtingraphicsfactory"></a>

### BuiltInGraphicsFactory — [Back to Top](#table-of-contents)

`app.graphics_factory` builds cached visual surfaces for controls (raised panels, button states, etc.). It is used internally by all built-in controls. Use it when building custom controls that need themed visual surfaces.

```python
from gui_do import BuiltInGraphicsFactory

factory = app.graphics_factory

visuals = factory.build_frame_visuals(rect)
selected = factory.resolve_visual_state(
    visuals,
    visible=True,
    enabled=True,
    armed=False,
    hovered=False,
)
# selected is a pygame.Surface ready to blit
```

---

<a id="telemetry"></a>

## Telemetry — [Back to Top](#table-of-contents)

gui_do includes an optional structured telemetry system for profiling frame timing, event dispatch, and scheduler behaviour.

```python
from gui_do import (
    configure_telemetry,
    telemetry_collector,
    TelemetryCollector,
    TelemetrySample,
    analyze_telemetry_records,
    analyze_telemetry_log_file,
    load_telemetry_log_file,
    render_telemetry_report,
)

# Enable telemetry and optionally log to a file
configure_telemetry(enabled=True, log_file="telemetry.jsonl")

# Access the global collector
collector = telemetry_collector()

# Analyze records from the current session
records = collector.get_records()       # list[TelemetrySample]
report = analyze_telemetry_records(records)
print(render_telemetry_report(report))

# Analyze a previously recorded log file
records = load_telemetry_log_file("telemetry.jsonl")
report = analyze_telemetry_log_file("telemetry.jsonl")
print(render_telemetry_report(report))
```

Telemetry is disabled by default and adds no overhead when off.

---

<a id="core-utilities"></a>

## Core Utilities — [Back to Top](#table-of-contents)

<a id="invalidationtracker"></a>

### InvalidationTracker — [Back to Top](#table-of-contents)

`app.invalidation` tracks which parts of the scene are dirty and need to be redrawn. The renderer uses it to return a minimal dirty rect list from `app.draw()`, enabling partial screen updates.

```python
from gui_do import InvalidationTracker

# Mark the entire scene dirty (forces a full redraw next frame)
app.invalidation.invalidate_all()

# Individual controls call node.invalidate() which propagates automatically
my_control.invalidate()
```

`app.draw()` returns a list of dirty rects (or `None` for a full-screen flip). Pass the result to `pygame.display.update()` for efficient partial updates.

```python
dirty = app.draw()
if dirty:
    pygame.display.update(dirty)
else:
    pygame.display.flip()
```
