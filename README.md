[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

Latest Demo (click):

<a href="https://www.youtube.com/watch?v=wkEmwIOquCo"><img src="https://img.youtube.com/vi/wkEmwIOquCo/0.jpg" alt="Demo Video"></img></a>

# gui_do

gui_do is a pygame GUI toolkit for building scene-driven desktop applications with one package-level public API for controls, layout, input routing, background work, overlays, theming, state, and feature composition. It is designed for tools, editors, dashboards, simulation frontends, and other application UIs that benefit from explicit runtime services and reusable controls. The exported surface in `gui_do.__all__` is the authoritative public boundary.

<a id="table-of-contents"></a>

## Table of Contents

- [Quick Start](#quick-start)
- [Overview](#overview)
- [Minimal Runnable Example](#minimal-runnable-example)
- [Package Management](#package-management)
  - Start a New Project
  - Add to or Update an Existing Project
- [Application Bootstrap](#application-bootstrap)
  - Display Creation
  - GuiApplication
  - UiEngine
  - run_entrypoint
  - Scene Management
  - SceneSpatialIndex
- [Controls](#controls)
  - Display and Container Controls
  - Text Controls
  - TextFlow and TextSpan
  - Selection, Range, and Data Controls
  - Canvas, Scroll, and Advanced Inputs
- [Layout](#layout)
  - LayoutAxis
  - LayoutManager
  - ConstraintLayout
  - FlexLayout
  - GridLayout
  - FlowLayout and FlowItem
  - DockWorkspace and DockWorkspacePanel
  - WindowTilingManager
  - LayoutAnimator
  - LayoutPass
  - ResponsiveLayout and Breakpoint
  - SnapGrid, AlignmentGuide, SnapComposer, and SnapTarget
  - Viewport
- [Events and Input](#events-and-input)
  - GuiEvent and EventManager
  - EventBus
  - Signal and SignalConnection
  - ActionManager
  - ActionMiddleware and ActionContext
  - ActionDescriptor and ActionRegistry
  - KeyChordManager
  - InputMap and InputBinding
  - FocusManager
  - FocusRing
  - FocusScopeManager
  - WindowFocusManager
  - GestureRecognizer
  - InputSnapshot
  - ValueChangeReason and ValueChangeCallback
  - EventRecorder and EventPlayback
- [Data and State](#data-and-state)
  - ObservableValue, ComputedValue, and PresentationModel
  - ObservableList and ObservableDict
  - ObservableStream
  - CollectionView and CollectionViewQuery
  - Binding and BindingGroup
  - SelectionModel
  - InvalidationTracker
  - FormModel
  - FormSchema
  - ValidationPipeline and Validators
  - WizardFlow, WizardStep, and WizardHandle
  - CommandHistory
  - DocumentModel
  - StateMachine, Router, and HierarchicalStateMachine
  - SettingsRegistry
  - TextFormatter
  - VirtualItemSource and FixedItemSource
  - SortFilterProxySource
  - AsyncDataProvider
  - DataCache and CacheStats
  - ListDiffCalculator
  - ObjectPool
  - SceneSnapshot and NodeSnapshot
  - WorkspaceState and WorkspacePersistenceManager
- [Scheduling and Animation](#scheduling-and-animation)
  - TaskScheduler
  - CooperativeScheduler
  - Timers
  - SceneTimeline
  - TweenManager
  - AnimationSequence
  - AnimationStateMachine
  - TransitionManager
  - Debouncer and Throttler
- [Overlay and Runtime Services](#overlay-and-runtime-services)
  - OverlayManager and OverlayHandle
  - PopupPlacement
  - TooltipManager and TooltipHandle
  - ToastManager and ToastHandle
  - DialogManager and DialogHandle
  - ContextMenuManager and ContextMenuHandle
  - DragDropManager and DragPayload
  - TransferData and TransferManager
  - FileDialogManager, FileDialogOptions, and FileDialogHandle
  - ResizeManager
  - ClipboardManager
  - CommandPaletteManager, CommandEntry, and CommandPaletteHandle
  - ShortcutHelpOverlay
  - CanvasViewport
  - CursorManager
  - ErrorBoundary
- [Menu System](#menu-system)
  - MenuBarControl and MenuEntry
    - SceneMenuStripControl
  - MenuBarManager
- [Notification System](#notification-system)
  - NotificationCenter and NotificationRecord
  - NotificationPanelControl
- [Scene Transitions](#scene-transitions)
  - SceneTransitionManager and SceneTransitionStyle
- [Feature System](#feature-system)
  - Feature Types and FeatureMessage
  - FeatureManager
  - Feature Layout Helpers
- [Theme and Graphics](#theme-and-graphics)
  - ColorTheme
  - ThemeManager and DesignTokens
  - ScopedTheme and ScopedThemeManager
  - BuiltInGraphicsFactory
  - FontManager
  - FontRoleRegistry
  - ShapeRenderer
  - VectorPath
  - SurfaceCompositor and Layer
  - SurfaceEffects
  - DirtyRegionTracker
  - DrawContext and DrawPhase
  - AssetRegistry
  - DebugOverlay
- [Game and Media](#game-and-media)
  - SpriteSheet and FrameAnimation
  - AnimatedImageControl
  - TileSet and TileMap
  - ParticleSystem
- [Localization](#localization)
  - StringTable and LocaleRegistry
- [Introspection](#introspection)
  - ui_property and PropertyDescriptor
  - PropertyRegistry
  - PropertyInspectorModel and PropertyInspectorPanel
- [Telemetry](#telemetry)
- [Public API Index](#public-api-index)

---

## Quick Start [Back to Top](#table-of-contents)

```bash
pip install -e .
```

gui_do is not published to PyPI. Install it from a local clone with the command above, or see the [Package Management](#package-management) section for project bootstrap and update workflows.

```python
from pygame import Rect
from gui_do import create_display, GuiApplication, LabelControl

surface = create_display((800, 600))
app = GuiApplication(surface)
app.scene.add(LabelControl("hello", Rect(24, 24, 280, 32), "Hello, gui_do"))
app.run_entrypoint(target_fps=60)
```

---

## Overview [Back to Top](#table-of-contents)

**Application structure.** Every gui_do application starts with a `GuiApplication` bound to a pygame display surface. The application owns the active scene graph and a set of scene-local services: `TaskScheduler`, `Timers`, `TweenManager`, `OverlayManager`, `DragDropManager`, `WindowTilingManager`, `LayoutManager`, `FocusManager`, and `ActionManager`. When you call `app.switch_scene(name)`, those services are swapped out for the new scene's equivalents automatically, so multi-screen applications stay isolated without custom bookkeeping. The `UiEngine` class drives the main loop — it calls `GuiApplication.process_event`, `app.update`, and `app.draw` each frame, advancing every scene-local service at the correct point in the frame pipeline.

**Scene graph and controls.** Each scene is a tree of `UiNode` subclasses. Every node has a `Rect`, a `control_id`, visibility, and enabled-state, and optionally participates in focus traversal through a `tab_index`. Adding a control is always `parent.add(child)`. `PanelControl` is the general-purpose container; `WindowControl` is a floating draggable window panel that integrates with `WindowTilingManager`. The built-in control set covers labels, buttons, toggles, button groups, sliders, scrollbars, spinners, range sliders, text inputs, text areas, rich text labels, list views, data grids, trees, tabs, dropdowns, color pickers, splitters, scroll views, canvas surfaces, images, and frames. Custom controls subclass `PanelControl` or `UiNode` directly.

**Input and events.** Raw pygame events are normalized into `GuiEvent` objects by `EventManager` before being dispatched. Controls never see raw pygame events. `GuiEvent` exposes semantic helpers (`is_key_down`, `is_mouse_down`, `pos`, `rel`, `kind`) and carries `EventType` and `EventPhase` metadata so routing-aware code can distinguish capture, target, and bubble phases. `ActionManager` maps keys to named callbacks and respects scene and window scope. `KeyChordManager` layers multi-step sequential chords on top of `ActionManager`. `InputMap` bridges physical key-to-action bindings, supports persistence through `SettingsRegistry`, and can be hot-reloaded. `FocusManager` owns keyboard focus and Tab traversal; `FocusScopeManager` constrains traversal to a declared subtree for modal dialogs and dropdowns. `GestureRecognizer` detects composed pointer gestures such as double-click, long-press, and swipe from the same `GuiEvent` stream. `EventBus` is the separate publish/subscribe channel for non-input runtime signals between features and services.

**Layout.** gui_do offers multiple composable layout strategies. `LayoutManager` is a simple grid-placement helper. `ConstraintLayout` anchors controls relative to a container rect. `FlexLayout` computes row/column arrangements with grow/shrink factors. `GridLayout` positions controls in explicit rows and columns with fixed, auto-sized, or fractional track sizing. `DockWorkspace` models IDE-style pane splits as a serializable tree of `DockPane`, `DockTabs`, and `DockSplit` nodes, rendered through `DockWorkspacePanel`. `LayoutAnimator` intercepts any of these layout engines and tweens each control from old to new rect. `LayoutPass` is a two-pass measure/arrange protocol for content-wrapping and auto-sized containers. `ResponsiveLayout` hot-swaps the active layout engine based on container width breakpoints.

**Data and state.** The observable layer (`ObservableValue`, `ComputedValue`, `ObservableList`, `ObservableDict`) provides the reactive primitives that let UI controls stay in sync with application state without polling. `Binding` and `BindingGroup` wire observables directly to control attributes in one-way or two-way modes. `SelectionModel` is a shared multi-mode selection state for data controls. `FormModel` and `FormSchema` manage field validation, dirty tracking, and commit/reset. `CommandHistory` supplies undo/redo with transaction grouping. `DocumentModel` tracks content, revision, and dirty state for editor-style workflows. `StateMachine` models finite-state transitions. `SettingsRegistry` is a namespaced, persistable settings store where every declared setting is an `ObservableValue`. `WorkspacePersistenceManager` and `WorkspaceState` coordinate full session save/restore across scenes, features, and settings.

**Scheduling and animation.** `TaskScheduler` runs callables on a thread pool and delivers results, progress messages, and failures back to the UI thread during the normal frame update. `Timers` handles frame-driven repeating and one-shot callbacks. `TweenManager` animates any numeric attribute or function over time with configurable easing curves. `AnimationSequence` chains or parallelizes tweens declaratively. `TransitionManager` connects control visibility and enabled-state transitions to tween choreography. `Debouncer` and `Throttler` rate-limit callbacks without OS timer APIs, using the frame-driven `Timers` service.

**Overlay and runtime services.** `OverlayManager` draws transient panels above the scene graph. `ToastManager` shows timed or persistent status banners. `DialogManager` provides alert, confirm, and prompt modals without requiring custom panel management. `ContextMenuManager` renders pointer-anchored flyout menus using `ContextMenuItem` rows, and `MenuBarControl` plus `MenuBarManager` compose top-level horizontal menu bars from the same item type. `FileDialogManager` surfaces native-style open and save file choosers. `DragDropManager` coordinates typed drag sessions across controls. `TransferManager` manages a clipboard slot and an in-flight drag payload using the multi-format `TransferData` envelope. `ClipboardManager` provides a thin safe wrapper around the system clipboard. `CommandPaletteManager` shows a searchable launcher using the overlay system. `TooltipManager` renders hover-delay hint labels. `ResizeManager` propagates display-size changes to registered layout instances. `CursorManager` is a priority-stack cursor manager that resolves the highest-priority active cursor shape and calls `pygame.mouse.set_cursor` only when the shape changes. `ErrorBoundary` catches exceptions in child control draw/update paths and substitutes a placeholder visual so the rest of the scene stays running.

**Feature composition.** `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature` are the lifecycle base classes for reusable application modules. A `FeatureManager` registered on `GuiApplication` drives build, bind_runtime, configure_accessibility, update, and draw hooks for every feature. Features communicate through typed `FeatureMessage` envelopes; logic features expose command endpoints that other features can call without tight coupling. `WorkspacePersistenceManager` can save and restore per-feature state as part of a full session snapshot.

**Theme and graphics.** `ColorTheme` is the semantic palette and text-rendering helper used by the runtime. It owns a `FontManager` for role-based font resolution and exposes `render_text(text, role=...)` for immediate glyph rendering. `ThemeManager` manages named token sets with reactive `active_theme` and `active_tokens` observables. `ScopedThemeManager` maintains a push/pop scope stack for per-subtree token overrides. `BuiltInGraphicsFactory` caches visual surfaces for built-in controls. The `ui_property` decorator and `PropertyRegistry` annotate control attributes with display metadata for debug inspectors and property panels, surfaced through `PropertyInspectorModel` and `PropertyInspectorPanel`.

**Suitable applications.** gui_do is aimed at desktop-style tools, editors, dashboards, internal utilities, and simulation frontends where explicit runtime services and structured feature composition matter more than CSS-style document layout. It pairs well with applications that have significant background work (schedulers, file I/O, compute tasks) feeding reactive UI state, multiple scenes or view modes with shared services, and runtime extensibility through the feature and action-registry systems.

---

## Minimal Runnable Example [Back to Top](#table-of-contents)

```python
from pygame import Rect
from gui_do import ButtonControl, create_display, GuiApplication, LabelControl


def main() -> None:
    surface = create_display((640, 480), fullscreen=False, vsync=False)
    app = GuiApplication(surface)

    status = app.scene.add(LabelControl("status", Rect(20, 20, 220, 30), "Ready"))

    def on_click() -> None:
        status.text = "Clicked"

    app.scene.add(ButtonControl("go", Rect(20, 64, 120, 32), "Click", on_click=on_click))
    app.run_entrypoint(target_fps=60)


if __name__ == "__main__":
    main()
```

---

## Package Management [Back to Top](#table-of-contents)

The repository includes `scripts/manage.py` for consumer-project bootstrap and upgrade flows. The tool supports `init`, `apply`, `verify`, `check`, and `update` so a developer can start from a clean library-first checkout or sync a newer gui_do version into an existing project.

### Start a New Project

Use `init` in a cloned or downloaded gui_do repository when you want to strip bundled demo content and keep the library plus its support files:

```bash
python scripts/manage.py init --verify
```

Optional scaffold generation:

```bash
python scripts/manage.py init --scaffold --scaffold-file myapp.py --scaffold-package features --verify
```

Useful flags:

- `--dry-run` previews changes.
- `--skip-doc-sync` skips README and docs synchronization.
- `--skip-workflow-sync` skips CI workflow synchronization.

### Add to or Update an Existing Project

Use `check` before copying gui_do into another project:

```bash
python scripts/manage.py check --target D:/Code/my_app
```

Then use `update` to copy the current library-only directories and root files into the target project and run `apply` there:

```bash
python scripts/manage.py update --target D:/Code/my_app --verify
```

The update flow copies `gui_do/`, `scripts/`, `tests/`, `docs/`, `README.md`, and the packaging files that define the public package contract.

---

## Application Bootstrap [Back to Top](#table-of-contents)

### Display Creation

`create_display(size, *, fullscreen=True, scaled=True, vsync=True)` creates and returns a pygame display surface. It calls `pygame.init()` internally, so callers do not need a separate `pygame.init()` call. It also requests vertical synchronization with graceful fallback when the display driver cannot provide it.

```python
from gui_do import create_display

# Fullscreen with vsync (scaled to fit physical display)
surface = create_display((1920, 1080))

# Windowed, no vsync
surface = create_display((1024, 768), fullscreen=False, vsync=False)

# Fullscreen, no scaling
surface = create_display((1920, 1080), scaled=False)
```

The helper suppresses the pygame-ce `"no fast renderer available"` warning and silently degrades to `vsync=0` when hardware vsync is unavailable, so your application does not need to manage that fallback.

### GuiApplication

`GuiApplication(surface)` is the runtime root. It owns the active scene, scene-local services, event normalization, rendering orchestration, and feature coordination.

```python
from gui_do import create_display, GuiApplication

surface = create_display((1024, 720))
app = GuiApplication(surface)
```

Common application properties:

| Attribute | Type | Notes |
|---|---|---|
| `app.scene` | scene root | Active scene graph root |
| `app.focus` | `FocusManager` | Keyboard focus and traversal |
| `app.actions` | `ActionManager` | Key-to-action routing |
| `app.events` | `EventBus` | Pub/sub messaging |
| `app.scheduler` | `TaskScheduler` | Scene-local background tasks |
| `app.timers` | `Timers` | Scene-local frame timers |
| `app.tweens` | `TweenManager` | Scene-local tween animation |
| `app.overlay` | `OverlayManager` | Overlay stack |
| `app.drag_drop` | `DragDropManager` | Drag session state |
| `app.layout` | `LayoutManager` | Grid placement helper |
| `app.window_tiling` | `WindowTilingManager` | Floating-window tiling |
| `app.theme` | `ColorTheme` | Active theme object |
| `app.graphics_factory` | `BuiltInGraphicsFactory` | Cached built-in visuals |
| `app.window_focus` | `WindowFocusManager` | Ctrl+Tab window-cycling focus |
| `app.features` | `FeatureManager` | Feature registration and lifecycle |
| `app.toasts` | `ToastManager` | App-level toast banners |
| `app.dialogs` | `DialogManager` | Lazy modal dialog service |

Common application methods:

- `app.add(node, scene_name=None)` adds a root node to the active or named scene.
- `app.create_scene(name)` creates or returns a named scene.
- `app.switch_scene(name)` activates a scene.
- `app.scene_names()` lists registered scenes.
- `app.has_scene(name)` checks whether a scene exists.
- `app.remove_scene(name)` removes a non-active scene.
- `app.process_event(event)`, `app.update(dt_seconds)`, and `app.draw()` form the low-level runtime loop.

### UiEngine

`UiEngine` is the packaged event loop. It forwards pygame events through `GuiApplication.process_event(...)`, advances scene-local services, and draws each frame.

```python
import pygame
from gui_do import UiEngine

engine = UiEngine(app, target_fps=60)
engine.run()
pygame.quit()
```

Use `max_frames=` when you want a bounded run for tests or deterministic demos.

### run_entrypoint

`GuiApplication.run_entrypoint(target_fps, *, WORKSPACE_SAVE, workspace_manager, workspace_path)` is the preferred top-level entrypoint for production scripts. It wraps `UiEngine.run()` with full exception handling, optional workspace save/restore, `pygame.quit()`, and a final `raise SystemExit(exit_code)` so callers never need to manage teardown.

```python
from gui_do import create_display, GuiApplication

surface = create_display((1024, 720))
app = GuiApplication(surface)
# ... build scene ...
app.run_entrypoint(target_fps=120)
```

With automatic workspace persistence:

```python
from gui_do import create_display, GuiApplication, DEFAULT_WORKSPACE_STATE_PATH

surface = create_display((1024, 720))
app = GuiApplication(surface)
# ... build scene ...
app.run_entrypoint(target_fps=120, WORKSPACE_SAVE=True, workspace_path=DEFAULT_WORKSPACE_STATE_PATH)
```

Parameters:

| Parameter | Default | Notes |
|---|---|---|
| `target_fps` | `120` | Frame rate cap passed to `UiEngine` |
| `WORKSPACE_SAVE` | `False` | Load workspace on startup; save on exit |
| `workspace_manager` | `None` | `WorkspacePersistenceManager` instance; created automatically when `None` |
| `workspace_path` | `DEFAULT_WORKSPACE_STATE_PATH` | JSON path for workspace state |

### Scene Management

Each scene has its own scheduler, timers, tween manager, overlay manager, drag-drop manager, tiling manager, and theme/graphics bundle. That keeps multi-screen applications isolated without custom bookkeeping.

```python
app.create_scene("main")
app.create_scene("settings")

app.switch_scene("settings")
print(app.active_scene_name)
print(app.scene_names())
```

Standalone helpers such as `ContextMenuManager`, `FileDialogManager`, `SceneTransitionManager`, `ResizeManager`, `ThemeManager`, and `CommandPaletteManager` are instantiated explicitly and composed with the current application or scene services as needed.

### SceneSpatialIndex

`SceneSpatialIndex` is a uniform-grid spatial index for fast point and rect queries against a scene graph. It builds an internal cell map over all node bounding rects so hit-testing, rubber-band selection, and drag-drop zone detection run in O(1) average case rather than O(n) full-scene walks.

```python
from gui_do import SceneSpatialIndex

index = SceneSpatialIndex(cell_size=64)

# Build from the active scene:
index.build(app.scene)

# Point hit-test — returns nodes in BFS order:
nodes = index.query_point(mx, my)

# Rect range query (rubber-band selection):
selected = index.query_rect(selection_rect)

# Incremental update when one node moves:
index.update_node(my_node)
```

Rebuild via `index.build(scene)` on scene change or full layout reflow. Use `index.update_node(node)` for incremental single-node moves during drag operations.

---

## Controls [Back to Top](#table-of-contents)

All built-in controls are added to a scene or container with `parent.add(child)` and expose geometry, visibility, enable/disable, focus, and draw/update behavior through the public control classes exported at the package root.

### Display and Container Controls

Use these for structure, chrome, and general interaction:

- `PanelControl` is the general-purpose rectangular container.
- `LabelControl` renders single-line text with `align="left"`, `"center"`, or `"right"`.
- `ButtonControl` exposes click and focused keyboard activation.
- `ToggleControl` holds a boolean pushed state.
- `ButtonGroupControl` gives radio-style mutually exclusive selection by group name.
- `ArrowBoxControl` is a directional button with repeat support.
- `FrameControl` draws a decorative border.
- `ImageControl` displays a file path, `Path`, or `pygame.Surface`.
- `ProgressBarControl` shows determinate or indeterminate (animated marquee) progress.
- `WindowControl` is a floating draggable titled window.
- `TaskPanelControl` is an auto-hide task strip.
- `OverlayPanelControl` is the overlay-safe panel used by services such as dialogs and menus.

```python
from pygame import Rect
from gui_do import ButtonControl, LabelControl, PanelControl, ToggleControl

panel = app.scene.add(PanelControl("panel", Rect(20, 20, 340, 180)))
panel.add(LabelControl("title", Rect(12, 12, 200, 24), "Settings"))
panel.add(ButtonControl("save", Rect(12, 48, 100, 28), "Save", on_click=lambda: None))
panel.add(ToggleControl("autosave", Rect(12, 84, 140, 28), "On", "Off", pushed=True))
```

### Text Controls

`TextInputControl`, `TextAreaControl`, and `RichLabelControl` cover editable single-line input, editable multi-line input, and styled rich text.

```python
from gui_do import RichLabelControl, TextAreaControl, TextInputControl

name_input = TextInputControl(
    "name",
    Rect(20, 20, 240, 28),
    placeholder="Project name",
    on_submit=lambda value: print("submit", value),
)

notes = TextAreaControl(
    "notes",
    Rect(20, 60, 320, 140),
    value="Initial text",
    read_only=False,
)

hint = RichLabelControl(
    "hint",
    Rect(20, 210, 320, 60),
    text="**Bold**, _italic_, and `code` spans are supported.",
)
```

### TextFlow and TextSpan

`TextFlow` is a paragraph layout engine for mixed-style text with word-wrap. It renders a sequence of `TextSpan` objects as multi-line text onto a surface, resolving font metrics through the active `ColorTheme`. Use it when `RichLabelControl` is not enough — for example, inline help panels, tooltips with mixed formatting, or canvas-embedded annotations.

```python
from gui_do import TextFlow, TextSpan

spans = [
    TextSpan("Status: ", role="body"),
    TextSpan("OK", bold=True, color=(80, 200, 80), role="body"),
    TextSpan("\nDetails are shown below.", role="body"),
]

flow = TextFlow(width=320, line_spacing=4)
flow.set_content(spans)
flow.layout(app.theme)      # re-call after width or content changes

# In draw():
used_height = flow.render(surface, x=20, y=40)
```

`TextSpan` fields: `text`, `bold`, `italic`, `color` (RGB/RGBA or `None` for theme default), `role` (font role name).

### Selection, Range, and Data Controls

gui_do includes small-value controls and larger selection/data controls in the same public surface:

- `SliderControl` and `ScrollbarControl` report a new value plus optional `ValueChangeReason`.
- `SpinnerControl` is numeric input with buttons, keyboard input, and wheel support.
- `RangeSliderControl` exposes `low_value` and `high_value`.
- `DropdownControl` selects one `DropdownOption` and calls `on_change(value, index)`.
- `ListViewControl` renders `ListItem` rows with single or multi-select.
- `DataGridControl` displays `GridColumn` and `GridRow` tables.
- `TreeControl` renders hierarchical `TreeNode` data.
- `TabControl` switches among `TabItem` definitions.
- `SplitterControl` provides two resizable panes.

```python
from gui_do import (
    DropdownControl,
    DropdownOption,
    ListItem,
    ListViewControl,
    RangeSliderControl,
    SpinnerControl,
)

spinner = SpinnerControl("count", Rect(20, 20, 120, 28), value=5, min_value=0, max_value=20)
price = RangeSliderControl("range", Rect(20, 60, 260, 28), min_value=0, max_value=100, low_value=20, high_value=80)

choices = DropdownControl(
    "color",
    Rect(20, 100, 180, 28),
    options=[DropdownOption("Red", "red"), DropdownOption("Blue", "blue")],
    on_change=lambda value, index: print(value, index),
)

items = [ListItem("Alpha"), ListItem("Beta"), ListItem("Gamma")]
listing = ListViewControl("list", Rect(20, 140, 220, 150), items=items, on_select=lambda index, item: print(item.label))
```

### Canvas, Scroll, and Advanced Inputs

Use these controls when the built-in list/form controls are not enough:

- `CanvasControl` gives you a bounded event queue of `CanvasEventPacket` values for custom drawing and interaction.
- `ScrollViewControl` hosts child controls in content-local coordinates and clips them to a viewport.
- `ColorPickerControl` provides inline HSV picking plus hex text entry.
- `AnimatedImageControl` displays a `FrameAnimation` (from a `SpriteSheet`) as a scene-graph node; call `tick(dt)` once per frame.

```python
from gui_do import AnimatedImageControl, CanvasControl, ColorPickerControl, LabelControl, ScrollViewControl

canvas = CanvasControl("canvas", Rect(20, 20, 300, 180), max_events=256)

scroll = ScrollViewControl("scroll", Rect(340, 20, 220, 180), content_height=400, scroll_y=True)
scroll.add(LabelControl("row1", Rect(0, 0, 180, 24), "Scrollable row"), 0, 0)
scroll.add(LabelControl("row2", Rect(0, 0, 180, 24), "Another row"), 0, 36)

picker = ColorPickerControl("picker", Rect(20, 220, 220, 200), color=(255, 128, 0))
```

---

## Layout [Back to Top](#table-of-contents)

### LayoutAxis

`LayoutAxis.HORIZONTAL` and `LayoutAxis.VERTICAL` are the axis enums used by `SliderControl`, `ScrollbarControl`, `SplitterControl`, and related layout helpers.

### LayoutManager

`LayoutManager` is a small grid-placement helper for consistent row/column spacing.

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

### ConstraintLayout

`ConstraintLayout` and `AnchorConstraint` support anchor-relative positioning inside a container or window-sized parent rect.

```python
from gui_do import AnchorConstraint, ConstraintLayout

layout = ConstraintLayout()
layout.add(AnchorConstraint(save_button, left=12, bottom=12, width=100, height=28))
layout.apply(Rect(0, 0, 640, 480))
```

### FlexLayout

`FlexLayout` computes row or column layouts using `FlexItem`, `FlexDirection`, `FlexAlign`, and `FlexJustify`.

```python
from gui_do import FlexAlign, FlexDirection, FlexItem, FlexJustify, FlexLayout

layout = FlexLayout(direction=FlexDirection.ROW, gap=8, align=FlexAlign.CENTER, justify=FlexJustify.START)
items = [
    FlexItem(name_input, basis=180, grow=1),
    FlexItem(save_button, basis=100, grow=0),
]
layout.apply(items, Rect(20, 20, 420, 32))
```

### FlowLayout and FlowItem

`FlowLayout` wraps child controls left-to-right (or top-to-bottom in vertical mode), inserting automatic line breaks when the available cross dimension is exhausted. `FlowItem` describes per-child sizing hints. Unlike `FlexLayout`, `FlowLayout` adapts to a variable number of items without requiring a fixed row/column count. `apply(container_rect)` returns the total used height.

```python
from gui_do import FlowItem, FlowLayout

layout = FlowLayout(gap_x=8, gap_y=8)
for btn in toolbar_buttons:
    layout.add(FlowItem(node=btn))

used_height = layout.apply(container_rect)
```

Use `FlowItem` width/height arguments to constrain individual items: `FlowItem(node=img, width=64, height=64)`. Omit size arguments to let the item's current `rect` dimensions be used.

### DockWorkspace and DockWorkspacePanel

`DockWorkspace` is a serializable pane-layout model that represents an IDE-style dock arrangement as a tree of `DockPane`, `DockTabs`, and `DockSplit` nodes. The model carries no rendering logic; it is persisted via `to_dict` / `from_dict` and can be embedded inside a `WorkspaceState` for full session save/restore.

- `DockPane` — a single named content slot with a `pane_id`, `title`, and `payload` dict.
- `DockTabs` — a tab group that owns an ordered list of `DockPane` nodes and tracks the `active_pane_id`.
- `DockSplit` — a horizontal or vertical split whose children are any mix of pane/tabs/split nodes with proportional `ratios`.
- `DockWorkspace` — the root container; provides `find_pane`, `remove_pane`, and serialization helpers.
- `DockWorkspacePanel` — a `UiNode` control that renders the top-level `DockTabs` or `DockPane` of a `DockWorkspace` as a clickable tab strip.

```python
from gui_do import DockPane, DockSplit, DockTabs, DockWorkspace, DockWorkspacePanel
from pygame import Rect

workspace = DockWorkspace(
    DockSplit("horizontal", children=[
        DockTabs("left", panes=[DockPane("files", "Files"), DockPane("outline", "Outline")]),
        DockPane("editor", "Editor"),
    ], ratios=[0.25, 0.75]),
)

panel = DockWorkspacePanel("dock_panel", Rect(0, 0, 800, 36), workspace,
                           on_change=lambda pid: print("active pane", pid))
app.scene.add(panel)

state = workspace.to_dict()          # persist
workspace2 = DockWorkspace.from_dict(state)  # restore
```

### WindowTilingManager

`WindowTilingManager` arranges visible `WindowControl` nodes without overlap inside the active scene. It is scene-local through `app.window_tiling`.

```python
tiling = app.window_tiling
tiling.prime_registration()
tiling.configure(gap=12, padding=12, avoid_task_panel=True, relayout=False)
tiling.set_enabled(True)
tiling.arrange_windows()
print(tiling.read_settings())
```

### GridLayout

`GridLayout` positions children into a structured grid of rows and columns with configurable track sizes, gaps, and cell spanning. `GridTrack` defines each track's sizing (`int` for fixed pixels, `"auto"` for largest child size, or `"Nfr"` for fractional remainder of available space). `GridPlacement` specifies where each node sits with optional row and column spanning.

```python
from gui_do import GridLayout, GridTrack, GridPlacement

layout = GridLayout(
    row_tracks=[GridTrack("auto"), GridTrack("1fr"), GridTrack(40)],
    col_tracks=[GridTrack("1fr"), GridTrack("1fr")],
    gap=8,
)

layout.place(header,  GridPlacement(row=0, col=0, colspan=2))
layout.place(sidebar, GridPlacement(row=1, col=0))
layout.place(content, GridPlacement(row=1, col=1))
layout.place(footer,  GridPlacement(row=2, col=0, colspan=2))

layout.apply(container_rect)
for node in layout.nodes():
    node.invalidate()
```

### LayoutAnimator

`LayoutAnimator` intercepts layout reflows and tweens each child from its current rect to its new computed rect, replacing instant position jumps with smooth animated transitions. It works with both `FlexLayout` and `ConstraintLayout`.

```python
from gui_do import LayoutAnimator, Easing

animator = LayoutAnimator(app.tweens, duration=0.25, easing=Easing.EASE_OUT)

# Animate a FlexLayout reflow after adding a child:
animator.apply_flex(flex_layout, items, container_rect)

# Animate a ConstraintLayout reflow after a resize:
animator.apply_constraint(constraint_layout, parent_rect)

animator.cancel()
```

### LayoutPass

`LayoutPass` is a two-pass measure/arrange protocol that separates sizing queries from final placement, enabling content-wrapping containers and auto-sized overlays. Any class implementing `measure(available)` and `arrange(rect)` satisfies the protocol. `MeasureContext` and `ArrangeContext` carry constraints and final rects through each pass. `LayoutRoot` wraps a layout engine with dirty tracking and drives both passes only when the layout is marked dirty.

```python
from gui_do import LayoutRoot

root = LayoutRoot(layout=my_layout, invalidation=app.invalidation)
root.mark_dirty()        # call when content changes
root.update(container_rect)   # runs measure + arrange only when dirty
```

### ResponsiveLayout and Breakpoint

`ResponsiveLayout` wraps any set of layout managers and hot-swaps the active one based on the current container width. When the container is resized, call `update(width)` to let the manager evaluate its `Breakpoint` list and switch layouts automatically. `active_breakpoint` is a reactive `ObservableValue` subscribers can watch.

```python
from gui_do import ResponsiveLayout, Breakpoint, FlexLayout, GridLayout, FlexDirection

narrow = FlexLayout(FlexDirection.COLUMN, gap=4)
wide   = GridLayout(col_tracks=[...], row_tracks=[...], gap=8)

responsive = ResponsiveLayout(default_layout=narrow)
responsive.add_breakpoint(Breakpoint("medium", min_width=480, layout=wide))
responsive.add_breakpoint(Breakpoint("narrow", min_width=0,   layout=narrow))

responsive.active_breakpoint.subscribe(lambda name: print("Layout ->", name))

# Per resize event:
if responsive.update(panel.rect.width):
    do_layout_pass(responsive.active_layout)
```

`Breakpoint` fields are `name`, `min_width`, and `layout`. Breakpoints are evaluated in descending `min_width` order; the first matching one wins.

### SnapGrid, AlignmentGuide, SnapComposer, and SnapTarget

These helpers add grid and edge-alignment snapping for drag-and-drop layout editors and vector drawing tools. `SnapGrid` snaps a point or rect to the nearest grid intersection. `AlignmentGuide` finds shared-edge alignment opportunities between the dragged rect and other rects. `SnapComposer` combines both in one step. `SnapTarget` is the exported per-candidate record.

```python
from gui_do import AlignmentGuide, SnapComposer, SnapGrid, SnapTarget

grid = SnapGrid(cell_w=16, cell_h=16)
snapped = grid.snap_point(drag_x, drag_y)
snapped_rect = grid.snap_rect(dragged_rect)

# Draw the grid on an overlay surface for visual feedback:
grid.draw_grid(overlay_surface, viewport_rect, color=(80, 80, 80), alpha=80)

# Find alignment guides against other controls:
guide = AlignmentGuide([ctrl.rect for ctrl in sibling_controls])
targets: list[SnapTarget] = guide.find_snap_targets(dragged_rect, threshold_px=8)

# Combined snap (grid then guide):
composer = SnapComposer(grid=grid, guides=guide)
final_rect = composer.snap(dragged_rect, threshold_px=8)
```

### Viewport

`Viewport` encapsulates scroll offset and zoom level with coordinate transforms between screen space and content space. It is shared between scroll containers, `CanvasControl`, `DataGridControl`, and similar controls so that animated scrolling, snap-to-item, minimap projection, and rubber-band zoom compose without per-control reimplementation.

```python
from gui_do import Viewport

vp = Viewport(content_size=(2000, 1500), viewport_size=(800, 600))

vp.scroll_to(0, 200)
vp.scroll_by(0, 50)
vp.clamp()

vp.set_zoom(2.0, anchor=(400, 300))

local_pt  = vp.screen_to_local((mx, my))
screen_pt = vp.local_to_screen((lx, ly))
vis       = vp.visible_rect()    # pygame.Rect in content coordinates

vp.subscribe(lambda: my_canvas.invalidate())
```

---

## Events and Input [Back to Top](#table-of-contents)

### GuiEvent and EventManager

`EventManager` normalizes raw pygame input into `GuiEvent`. Controls and services consume `GuiEvent`, not raw pygame events.

```python
event.is_key_down(pygame.K_RETURN)
event.is_mouse_down(button=1)
event.is_mouse_up(button=1)
event.is_mouse_motion()
event.is_mouse_wheel()
event.pos
event.rel
event.raw_pos
event.raw_rel
event.kind
```

`EventType` and `EventPhase` are also exported for routing-aware code.

### EventBus

`EventBus` is a scoped publish/subscribe channel for non-input runtime events.

```python
bus = app.events
subscription = bus.subscribe("task.done", lambda payload: print(payload), scope="main")
bus.publish("task.done", {"result": 42}, scope="main")
bus.unsubscribe(subscription)
```

Use `once(...)` for one-shot subscriptions and `unsubscribe_scope(...)` to remove all handlers in one scope.

### Signal and SignalConnection

`Signal` is a typed class-level event descriptor for `UiNode` subclasses. Declare a `Signal` as a class attribute to give instances strongly-typed, zero-cost-when-unconnected publish/subscribe behavior. `SignalConnection` is the returned connection handle.

```python
from gui_do import Signal, SignalConnection

class MySlider(SliderControl):
    value_changed: Signal[float] = Signal()

slider = MySlider(...)

# Connect:
conn: SignalConnection = slider.value_changed.connect(lambda v: print("value:", v))

# Connect once (auto-disconnects after first emit):
slider.value_changed.connect_once(lambda v: do_one_time_thing(v))

# Disconnect:
conn.disconnect()
```

`Signal` integrates with `Binding` via the `control_change_signal` argument for two-way bindings on custom controls.

### ActionManager

`ActionManager` maps keys to named actions with optional scene and active-window scoping.

```python
import pygame

actions = app.actions
actions.register_action("save", lambda event: (print("save"), True)[1])
actions.bind_key(pygame.K_s, "save", scene="editor", window_only=False)
```

For a one-call setup, use `register_and_bind(...)`.

### ActionMiddleware and ActionContext

`ActionMiddleware` is a composable interception protocol layered on top of `ActionManager`. Each middleware receives an `ActionContext` plus the next handler in the chain, and returns `True` (consumed) or `False`. Middlewares are added via `app.actions.add_middleware(...)` and run LIFO so the most-recently added middleware runs first.

`ActionContext` carries `action_name`, `event`, and an `extras` dict for out-of-band data.

```python
from gui_do import ActionContext

class LoggingMiddleware:
    def __call__(self, ctx: ActionContext, next_handler) -> bool:
        print(f"[action] {ctx.action_name}")
        return next_handler(ctx)

app.actions.add_middleware(LoggingMiddleware())

# Inline guard — block destructive actions in read-only mode:
def read_only_guard(ctx: ActionContext, next_handler) -> bool:
    if app.read_only and ctx.action_name.startswith("edit."):
        return False
    return next_handler(ctx)

app.actions.add_middleware(read_only_guard)
app.actions.remove_middleware(read_only_guard)
```

### ActionDescriptor and ActionRegistry

`ActionDescriptor` is a self-contained action definition that centralises label, category, shortcut hint, and enablement/checked-state logic so that the command palette, menus, toolbars, and keyboard routing all read from one source. `ActionRegistry` is a process-wide catalog of descriptors.

```python
from gui_do import ActionDescriptor, ActionRegistry

registry = ActionRegistry()

registry.declare(
    "file.save",
    "Save",
    callback=lambda ctx, evt: (do_save(), True)[1],
    category="File",
    shortcut_hint="Ctrl+S",
    description="Save the current document",
    enabled=lambda ctx: ctx.document.is_dirty,
)

desc = registry.get("file.save")
if desc and desc.is_enabled(context):
    desc.invoke(context)

# Iterate by category:
for action in registry.by_category("File"):
    print(action.action_id, action.label)
```

`ActionDescriptor` fields: `action_id`, `label`, `callback`, `category`, `shortcut_hint`, `description`, `enabled` (bool or predicate), `checked` (bool or predicate), `metadata`.

### InputMap and InputBinding

`InputMap` is a persistence-aware action-to-key binding table that bridges physical inputs to logical action names. Features declare default bindings with `declare(...)`, application code or user settings override them with `bind(...)`, and `apply(actions)` pushes all current bindings into an `ActionManager`. `InputBinding` is the exported binding record.

```python
import pygame
from gui_do import InputMap, InputBinding

imap = InputMap()

# Declare defaults (typically in feature.build):
imap.declare("edit.copy",  key=pygame.K_c, mod=pygame.KMOD_CTRL, label="Copy")
imap.declare("file.save",  key=pygame.K_s, mod=pygame.KMOD_CTRL, label="Save")

# Apply to ActionManager:
app.actions.register_action("edit.copy",  lambda _e: do_copy())
app.actions.register_action("file.save",  lambda _e: do_save())
imap.apply(app.actions)

# Override at runtime:
imap.bind("edit.copy", key=pygame.K_c, mod=pygame.KMOD_CTRL | pygame.KMOD_SHIFT)

# Persist user remaps:
from gui_do import SettingsRegistry
registry = SettingsRegistry("settings.json")
imap.save(registry)
imap.load(registry)   # on next launch
```

Call `imap.bindings()` to get the full list of `InputBinding` records for displaying a keybinding settings panel.

### KeyChordManager

`KeyChordManager` dispatches multi-key sequential chords on top of an existing `ActionManager`. A `KeyChord` is a sequence of `ChordStep` values (key code + optional modifier mask). The manager intercepts `KEY_DOWN` events, accumulates partial-chord state, and fires the matched action when the full sequence completes within the configured timeout.

```python
import pygame
from gui_do import KeyChordManager, KeyChord, ChordStep

manager = KeyChordManager(app.actions, app.timers, timeout_ms=1500)

# Ctrl+K then Ctrl+C
manager.bind(
    KeyChord(steps=[
        ChordStep(key=pygame.K_k, mod=pygame.KMOD_CTRL),
        ChordStep(key=pygame.K_c, mod=pygame.KMOD_CTRL),
    ]),
    action_name="editor.copy_line",
)

# In handle_event:
if manager.process_event(event):
    return True
```

Pass `mod=0` on a `ChordStep` to match any modifiers. `KeyChordManager` delegates to the supplied `ActionManager` so chords coexist with simple key bindings in the same instance.

### FocusManager

`FocusManager` controls keyboard focus. Controls participate by exposing `tab_index >= 0` and accepting focus.

```python
focus = app.focus
focus.set_focus(name_input, via_keyboard=False)
print(focus.focused_node)
```

### FocusRing

`FocusRing` is a composable, bounded focus traversal ring with optional trap and chain semantics. Declare node ids in order; Tab / Shift+Tab cycle within the ring. Set `trap=True` to prevent Tab from ever leaving the ring (modal dialog behavior). Set `wrap=False` to let Tab fall through to a `parent` ring at boundaries. Rings may be dynamically mutated while open.

```python
from gui_do import FocusRing

# Modal dialog — Tab never escapes:
dialog_ring = FocusRing(
    node_ids=["ok_button", "cancel_button", "text_input"],
    trap=True,
)

next_id = dialog_ring.advance(current_id, forward=True)   # Tab
prev_id = dialog_ring.advance(current_id, forward=False)  # Shift+Tab

# Dynamic updates:
dialog_ring.insert("new_field", after="text_input")
dialog_ring.remove("cancel_button")

# Check membership:
dialog_ring.contains("ok_button")  # True
```

Chain rings by passing `parent=outer_ring` and setting `wrap=False` so a non-trapping ring delegates boundary advances to its parent.

### FocusScopeManager

`FocusScopeManager` constrains Tab traversal to a declared subtree while a scope is active, preventing focus from escaping into background controls. It integrates with `FocusManager` through a push/pop scope stack. Use it when opening modal overlays, dialogs, or dropdowns.

```python
from gui_do import FocusScope, FocusScopeManager

scope_mgr = FocusScopeManager(app.focus)

scope = scope_mgr.push(dialog_panel, scope_id="main-dialog")

# On close:
scope_mgr.pop(scope)

# Or pop the most-recently pushed scope:
scope_mgr.pop_top()
```

Multiple scopes may be stacked. The innermost scope is always active.

### WindowFocusManager

`WindowFocusManager` tracks which `WindowControl` node holds "window focus" — distinct from the per-control keyboard focus managed by `FocusManager` — and drives the dashed-rectangle visual hint drawn around the focused window. It is available as `app.window_focus` and cycles windows on Ctrl+Tab / Ctrl+Shift+Tab.

```python
# Cycle window focus forward (Ctrl+Tab):
app.window_focus.cycle(app.scene, forward=True, app=app)

# Cycle backward (Ctrl+Shift+Tab):
app.window_focus.cycle(app.scene, forward=False, app=app)

# Read the currently window-focused node:
print(app.window_focus.focused_window)

# Query whether the hint overlay should be drawn (used by the renderer):
if app.window_focus.should_draw_window_focus_hint():
    draw_hint()
```

`revalidate(scene)` is called automatically each frame by `GuiApplication.update()`. It advances focus to the next available window if the current one becomes hidden or disabled, and clears focus when no candidates remain. `update(dt_seconds)` advances the hint timeout timer.

### GestureRecognizer

`GestureRecognizer` detects composed pointer gestures — double-click, long-press, and swipe — from a stream of `GuiEvent` objects. Attach one recognizer per interactive node that needs gesture semantics.

```python
from gui_do import GestureRecognizer

gr = GestureRecognizer(
    on_double_click=lambda pos: zoom_in(pos),
    on_long_press=lambda pos: show_context_menu(pos),
    on_swipe=lambda direction, velocity: handle_swipe(direction, velocity),
)

# In update():
gr.update(dt_seconds)

# In handle_event():
gr.process_event(event)
```

All detection thresholds (`double_click_ms`, `long_press_ms`, `swipe_min_px`, etc.) are configurable at construction time.

### InputSnapshot

`InputSnapshot` is an immutable per-frame snapshot of pointer and keyboard state, assembled once at the start of each frame from the normalized event stream. Passing it to every system that reads input eliminates fragmented per-system bookkeeping and makes input queries deterministic for the entire frame.

```python
from gui_do import InputSnapshot

snapshot = InputSnapshot.build(events=normalized_events, previous=last_snapshot)

if snapshot.is_button_just_pressed(1):
    start_drag()

if snapshot.is_key_down(pygame.K_SHIFT):
    extend_selection()

hovered_id = snapshot.hover_chain[0] if snapshot.hover_chain else None
wheel = snapshot.accumulated_wheel_delta  # summed across all wheel events this frame
```

Fields: `pointer_pos`, `pointer_delta`, `buttons_held`, `buttons_just_pressed`, `buttons_just_released`, `modifiers`, `keys_just_pressed`, `keys_just_released`, `accumulated_wheel_delta`, `hover_chain`.

### ValueChangeReason and ValueChangeCallback

`ValueChangeReason` tags slider- and scrollbar-style callbacks with the source of the change. Members are `KEYBOARD`, `PROGRAMMATIC`, `MOUSE_DRAG`, and `WHEEL`.

`ValueChangeCallback` is the exported type alias for the callback signature: `Callable[[TValue, ValueChangeReason], None]`. Attach a callback as the `on_change` argument of `SliderControl` or `ScrollbarControl`.

```python
from gui_do import SliderControl, ValueChangeReason

def on_change(value: float, reason: ValueChangeReason) -> None:
    print(value, reason)

slider = SliderControl("zoom", Rect(20, 20, 240, 24), LayoutAxis.HORIZONTAL, 0.0, 100.0, 50.0, on_change=on_change)
```

The `on_change` callback receives two positional arguments. Omit the second argument to use a one-argument callback — backward compatibility is preserved at dispatch time.

### EventRecorder and EventPlayback

`EventRecorder` captures a time-stamped log of `GuiEvent` objects. Recordings can be saved to a JSON file and replayed. `EventPlayback` re-injects recorded events through a handler at the original relative timing, driven by a frame-elapsed accumulator with no OS timer APIs. `RecordedEvent` is the exported per-event record type.

```python
from gui_do import EventRecorder, EventPlayback

# Recording:
recorder = EventRecorder()
recorder.start()

# After normalizing each event in your loop:
# recorder.record(gui_event)

events = recorder.stop()
recorder.save("my_macro.json")

# Playback:
log = EventRecorder.load_file("my_macro.json")
player = EventPlayback(log, handler=app.process_event)
player.start()

# Per frame:
player.update(dt_seconds)

if not player.is_playing:
    print("Playback complete")
```

Typical uses include integration tests (record known-good interactions and replay in CI), user macros, and tutorial walkthroughs.

---

## Data and State [Back to Top](#table-of-contents)

### ObservableValue, ComputedValue, and PresentationModel

`ObservableValue` is the base reactive primitive. `ComputedValue` derives a read-only value from other observables. `PresentationModel` is a small subscription-owning base class for view-model style objects.

```python
from gui_do import ComputedValue, ObservableValue, PresentationModel

a = ObservableValue(2)
b = ObservableValue(3)
total = ComputedValue(lambda: a.value + b.value, deps=[a, b])
total.subscribe(lambda value: print("total", value))


class CounterModel(PresentationModel):
    def __init__(self) -> None:
        super().__init__()
        self.count = ObservableValue(0)


a.value = 10
```

### ObservableList and ObservableDict

`ObservableList` and `ObservableDict` are reactive collection primitives that fire registered listeners with a `CollectionChange` event on every mutation. `ChangeKind` values are `ADDED`, `REMOVED`, `REPLACED`, `CLEARED`, and `MOVED`. `CollectionChange` carries `kind`, `index`, `key`, `old_value`, and `new_value`.

```python
from gui_do import ChangeKind, CollectionChange, ObservableDict, ObservableList, ListItem

items = ObservableList([ListItem("Alpha"), ListItem("Beta")])
items.subscribe(lambda change: list_view.set_items(items.snapshot()))

items.append(ListItem("Gamma"))
items.remove_at(0)

settings = ObservableDict({"volume": 1.0})
settings.subscribe(lambda change: print(change.key, "->", change.new_value))
settings["volume"] = 0.5
```

### ObservableStream

`ObservableStream` wraps any `ObservableValue`, `Signal` instance, or callable subscription source and provides operator chaining so that multi-step reactive pipelines can be expressed declaratively. All operators are lazy — no callbacks are wired until `subscribe` is called.

Available operators: `map`, `filter`, `distinct_until_changed`, `debounce`, `throttle`, `merge`, `zip`, `take_until`, `take`, `pairwise`.

```python
from gui_do import ObservableStream, ObservableValue

speed = ObservableValue(0.0)

stream = (
    ObservableStream(speed)
    .distinct_until_changed()
    .filter(lambda v: v > 0)
    .map(lambda v: round(v, 1))
)

unsub = stream.subscribe(lambda v: label.__setattr__("text", f"{v} m/s"))
# Later:
unsub()
```

`merge` combines multiple streams and emits from whichever fires first. `take_until` auto-unsubscribes on a stop-signal's first emission. `pairwise` emits `(previous, current)` tuples for change-delta math.

### CollectionView and CollectionViewQuery

`CollectionView` is a materialized, filterable, sortable, and projectable pipeline over any iterable or callable source. `CollectionViewQuery` is the filter/sort/project specification applied during each `refresh`.

```python
from gui_do import CollectionView, CollectionViewQuery

# Build a view of in-stock products sorted by price:
query = CollectionViewQuery(
    filters=[lambda p: p.in_stock],
    sort_key=lambda p: p.price,
)
view = CollectionView(lambda: product_repository.all(), query=query)

# Read items:
for product in view.items:
    print(product.name, product.price)

# Subscribe to refresh notifications:
unsub = view.subscribe(lambda: grid.set_items(view.items))

# Reapply after the underlying source changes:
view.refresh()
unsub()
```

`CollectionViewQuery` fields: `filters` (list of predicates), `sort_key`, `reverse`, `projector`. All fields are optional. `CollectionView.set_source` replaces the underlying source and triggers a refresh.

### Binding and BindingGroup

`Binding` wires an `ObservableValue` to a named attribute on a target object so that changes on either side propagate automatically. `BindingGroup` collects multiple bindings and disposes them together.

```python
from gui_do import Binding, BindingGroup, ObservableValue

zoom = ObservableValue(1.0)

# One-way: model → control
b = Binding(zoom, slider, "value", mode="one_way")

# Two-way: model ↔ control
b = Binding(zoom, slider, "value", mode="two_way", control_change_signal="on_change")
b.dispose()

group = BindingGroup()
group.add(Binding(zoom, slider, "value"))
group.add(Binding(label_text, label, "text"))
group.dispose()
```

Modes: `"one_way"` (default), `"one_way_to_source"`, `"two_way"`. Pass `to_control` and `to_source` callables for type conversion.

### SelectionModel

`SelectionModel` is a shared observable selection state for data controls. Decoupling selection from rendering lets multiple controls (a list view, a preview pane, a toolbar counter) share one source of truth. Modes are `SINGLE` (default), `MULTI`, and `RANGE`.

```python
from gui_do import SelectionModel, SelectionMode

model = SelectionModel(mode=SelectionMode.MULTI, item_count=100)
model.subscribe(lambda m: list_view.invalidate())
model.select(5)
model.toggle(10)
print(model.selected_indices)   # frozenset({5, 10})

# Range selection:
model2 = SelectionModel(mode=SelectionMode.RANGE, item_count=100)
model2.set_anchor(3)
model2.set_active(8)
print(model2.selected_indices)  # frozenset({3, 4, 5, 6, 7, 8})
```

### InvalidationTracker

`InvalidationTracker` collects dirty regions and can promote to full redraw when necessary.

```python
tracker = app.invalidation
tracker.set_screen_size((800, 600))
tracker.invalidate_rect(Rect(20, 20, 100, 40))
is_full, dirty_rects = tracker.begin_frame()
tracker.end_frame()
```

### FormModel

`FormModel` manages named `FormField` instances, per-field validation, cross-field validation, dirty tracking, and commit/reset behavior.

```python
from gui_do import FieldError, FormModel

form = FormModel()
name = form.add_field("name", "", required=True)
email = form.add_field("email", "")

name.value.value = "Alice"
form.add_cross_validator(
    lambda model: None if model.field("email").value.value else [FieldError("email", "Email required")]
)

ok = form.validate_all()
print(ok, form.get_errors())
form.commit_all()
```

`ValidationRule` is the callable type exported for field validators, and `FieldError` is the exported error record type.

### ValidationPipeline and Validators

The standalone validator system composes reusable validation logic without requiring a full `FormModel`. `ValidationPipeline` runs validators in order, collects all errors, and returns a `ValidationResult`. The built-in validators cover the most common field constraints; `CustomValidator` wraps any callable; `DependentValidator` receives the full context dict for cross-field rules.

```python
from gui_do import (
    CustomValidator, DependentValidator, LengthValidator, PatternValidator,
    RangeValidator, RequiredValidator, ValidationPipeline, ValidationResult,
)

pipeline = ValidationPipeline([
    RequiredValidator("Name is required"),
    LengthValidator(min_length=2, max_length=64, message="2–64 characters"),
    PatternValidator(r"^[A-Za-z ]+$", message="Letters and spaces only"),
])

result: ValidationResult = pipeline.validate("Alice")
print(result.ok)      # True
print(result.errors)  # []

result2 = pipeline.validate("")
print(result2.ok)        # False
print(result2.errors[0]) # "Name is required"

# Cross-field rule — receives the enclosing context dict:
pipeline.add(DependentValidator(
    lambda v, ctx: None if ctx.get("agree_terms") else "Must accept terms",
))
```

Built-in validators: `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`. `Validator` is the protocol type alias.

### WizardFlow, WizardStep, and WizardHandle

`WizardFlow` coordinates a sequential multi-step form where each step is validated before advancing. `WizardStep` declares the title, field keys, and optional `on_validate` / `on_enter` / `on_leave` hooks. `WizardHandle` is the return type of `advance()`. `progress` is an `ObservableValue[float]` (0.0 – 1.0) that can be bound to a `ProgressBarControl`.

```python
from gui_do import WizardFlow, WizardStep

steps = [
    WizardStep(
        title="Name",
        fields=["first_name", "last_name"],
        on_validate=lambda d: [] if d.get("first_name") else ["First name required"],
    ),
    WizardStep(title="Email", fields=["email"]),
    WizardStep(title="Confirm", fields=[]),
]

wizard = WizardFlow(steps, on_complete=lambda data: save(data), on_cancel=lambda: None)
wizard.progress.subscribe(lambda v: progress_bar.__setattr__("value", v))

ok, errors = wizard.advance({"first_name": "Alice", "last_name": "Smith"})
ok, errors = wizard.advance({"email": "alice@example.com"})
ok, errors = wizard.advance({})   # final step — calls on_complete

wizard.back()    # return to previous step
wizard.cancel()  # calls on_cancel and resets state
```

### FormSchema

`FormSchema` is a declarative, reusable field specification that can stamp out pre-configured `FormModel` instances or validate a plain dict of values without building a UI.

```python
from gui_do import FieldError, FormSchema, SchemaField

schema = FormSchema([
    SchemaField("username", default="", label="Username", required=True),
    SchemaField("age",      default=0,  label="Age",      required=False),
])

# Build a FormModel pre-populated with the schema's fields and defaults:
form = schema.build_form()
form.field("username").value.value = "alice"
errors: list[FieldError] = schema.validate_values({"username": "alice", "age": 30})

# Get a dict of field defaults:
print(schema.defaults())   # {"username": "", "age": 0}
```

`SchemaField` fields: `name`, `default`, `label`, `required`, `validators`. `FormSchema.apply_to` writes values into an existing `FormModel`; `FormSchema.extract_from` reads current values back out.

### CommandHistory

`CommandHistory` implements bounded undo/redo stacks and `CommandTransaction` grouping for objects matching the exported `Command` protocol.

```python
history = CommandHistory(max_size=100)
history.push(my_command)
history.undo()
history.redo()

with history.transaction("Bulk edit") as tx:
    tx.add(cmd_a)
    tx.add(cmd_b)
```

### DocumentModel

`DocumentModel` is a generic document state container for editor-style applications. It tracks content, file path, revision number, and a dirty flag — making it easy to wire a Save button that is enabled only when unsaved changes exist.

```python
from gui_do import DocumentModel

doc = DocumentModel("main", content="Hello, world")
doc.set_content("Updated text")
print(doc.is_dirty)     # True
doc.save("notes.txt")   # writes to disk and updates saved_revision
print(doc.is_dirty)     # False

# Custom save/load callables:
import json
doc.save("data.json", saver=lambda path, c: path.write_text(json.dumps(c)))
doc.load("data.json",  loader=lambda path:   json.loads(path.read_text()))
```

`DocumentModel` fields: `document_id`, `content`, `path`, `metadata`, `revision`, `saved_revision`. `is_dirty` is `True` when `revision != saved_revision`.

### StateMachine, Router, and HierarchicalStateMachine

`StateMachine` models finite-state transitions with observable current state. `Router` models application navigation history and can switch scenes when supplied with a `GuiApplication`. `HierarchicalStateMachine` extends `StateMachine` with composite states, history states, and parallel (orthogonal) regions.

```python
from gui_do import HierarchicalStateMachine, Router, StateMachine

sm = StateMachine("idle")
sm.add_state("running")
sm.add_transition("idle", "running", trigger="start")
sm.current.subscribe(lambda value: print("state", value))
sm.trigger("start")

router = Router()
router.register("/home", "home_scene")
router.register("/settings", "settings_scene")
router.push("/home", app=app)
router.push("/settings", app=app)
router.pop(app=app)

# Hierarchical — composite sub-machine:
inner = HierarchicalStateMachine("idle_a")
inner.add_transition("idle_a", "busy_a", trigger="work")

outer = HierarchicalStateMachine("outer_idle")
outer.add_composite("active", inner, initial="idle_a")
outer.add_transition("outer_idle", "active", trigger="activate")
outer.trigger("activate")
print(outer.sub_current("active"))  # "idle_a"

# History — resumes last sub-state on re-entry:
outer2 = HierarchicalStateMachine("home")
outer2.add_history("wizard", inner, initial="idle_a")
```

### SettingsRegistry

`SettingsRegistry` is a namespaced settings store where each declared setting is backed by an `ObservableValue`. `SettingDescriptor` is the exported metadata object used for introspection.

```python
from gui_do import SettingsRegistry

settings = SettingsRegistry("settings.json")
volume = settings.declare("audio", "volume", 1.0, label="Master Volume")
volume.subscribe(lambda value: print("volume", value))

settings.load()
settings.set_value("audio", "volume", 0.5)
settings.save()
```

### TextFormatter

Formatters control how user-typed text is displayed in a `TextInputControl` and how the display value is parsed back to a raw storage string. Attach a formatter via the `formatter` constructor argument.

- `NumericFormatter` — integer or float with optional thousands separator and min/max bounds validation.
- `PatternFormatter` — positional mask (phone number, date, IP address) using `#` slots for digit positions.
- `FixedPatternFormatter` — like `PatternFormatter` but requires all digit slots to be filled for validation to pass.
- `TextFormatter` — the protocol type alias documenting the required `format`, `parse`, `validate`, and `adjust_cursor` interface for custom formatters.

```python
from gui_do import FixedPatternFormatter, NumericFormatter, PatternFormatter, TextInputControl

age_input = TextInputControl(
    "age", rect,
    formatter=NumericFormatter(decimals=0, min_value=0, max_value=100),
)

phone_input = TextInputControl(
    "phone", rect,
    formatter=PatternFormatter("(###) ###-####"),
)
```

### VirtualItemSource and FixedItemSource

Data controls accept an optional `source` argument implementing `VirtualItemSource`. The control calls `item_at(index)` only for visible indices, so sources may fetch pages lazily or compute items on demand. `FixedItemSource` wraps a plain Python list for small to medium in-memory datasets.

```python
from gui_do import FixedItemSource, ListItem, ListViewControl

source = FixedItemSource([ListItem("Alpha"), ListItem("Beta"), ListItem("Gamma")])
list_view = ListViewControl("list", rect, source=source)

source.append(ListItem("Delta"))
list_view.invalidate()
```

Custom sources implement three methods: `item_count() -> int`, `item_at(index: int) -> Any`, and `item_height(index: int) -> int`.

### AsyncDataProvider

`AsyncDataProvider` wraps a `TaskScheduler` task with an `IDLE → LOADING → LOADED / FAILED` state machine and notifies subscribers on every transition. Controls render a loading indicator, an error message, or the loaded content by inspecting `provider.state`. Call `provider.update()` once per frame to advance state transitions.

```python
from gui_do import AsyncDataProvider, LoadState, LoadStateKind

provider = AsyncDataProvider(scheduler=app.scheduler)

def _fetch_records():
    return load_json("records.json")   # runs on a background thread

provider.subscribe(lambda state: my_list.invalidate())
provider.load(_fetch_records)
provider.update()   # call once per frame

state = provider.state
if state.is_loading:
    draw_spinner(surface, rect)
elif state.is_failed:
    draw_error(surface, rect, state.error)
elif state.is_loaded:
    draw_items(surface, rect, state.data)
```

`LoadStateKind` values are `IDLE`, `LOADING`, `LOADED`, and `FAILED`. Use `provider.cancel()` to abort an in-flight load and `provider.load(fn)` to reload.

### SortFilterProxySource

`SortFilterProxySource` wraps any `VirtualItemSource` (including `FixedItemSource` and `ObservableList`) and applies composable filter, sort-key, and optional group-by transforms. The proxy recomputes its visible index list on demand and notifies subscribers so data controls refresh automatically.

```python
from gui_do import SortFilterProxySource, FixedItemSource, ListItem, ListViewControl

base = FixedItemSource([ListItem("Banana"), ListItem("Apple"), ListItem("Cherry")])
proxy = SortFilterProxySource(base)

# Filter to items starting with 'A':
proxy.set_filter(lambda item: item.label.startswith("A"))

# Sort alphabetically:
proxy.set_sort_key(lambda item: item.label)

# Wire to a list view:
list_view = ListViewControl("list", rect, source=proxy)
proxy.subscribe(lambda: list_view.invalidate())

# Change filter at runtime — subscribers are notified:
proxy.set_filter(None)   # clear filter; shows all items
```

Attach to an `ObservableList` for live mutation tracking by subscribing `proxy.invalidate` to the list's change events.

### DataCache and CacheStats

`DataCache` is a typed LRU cache with optional TTL per entry. On miss, `get_or_load(key, factory)` calls the factory and caches its result. `on_evicted` and `on_invalidated` are `Signal` instances for reactive cache-event handling. `CacheStats` is a snapshot of hit/miss/eviction counters.

```python
from gui_do import DataCache, CacheStats

cache: DataCache[str, dict] = DataCache(max_size=256)

cache.put("user:42", user_data)
val = cache.get("user:42")          # → user_data or None

# Load-on-miss:
user = cache.get_or_load("user:42", lambda: fetch_user(42))

# TTL (seconds):
timed_cache: DataCache[str, bytes] = DataCache(max_size=100, ttl_seconds=30.0)

cache.on_evicted.subscribe(lambda kv: print("evicted", kv[0]))
cache.on_invalidated.subscribe(lambda k: print("invalidated", k))

stats: CacheStats = cache.stats()
print(stats.hit_rate)
```

`CacheStats` fields: `size`, `hits`, `misses`, `evictions`, `invalidations`, `hit_rate`.

### ListDiffCalculator

`ListDiffCalculator` computes the minimal edit sequence (inserts, removes, moves) to transform one list into another using the Myers algorithm. Use it to animate list-view updates or to reconcile reactive data collections. `ListDiff`, `DiffInsert`, `DiffRemove`, and `DiffMove` are the exported result types.

```python
from gui_do import DiffInsert, DiffRemove, ListDiff, ListDiffCalculator

diff: ListDiff = ListDiffCalculator.diff(["a", "b", "c"], ["b", "c", "e"])
# diff.removes → [DiffRemove(index=0, item="a")]
# diff.inserts → [DiffInsert(index=2, item="e")]

# With a key function for object lists:
diff2 = ListDiffCalculator.diff(old_items, new_items, key_fn=lambda x: x.id)

# Apply in-place:
ListDiffCalculator.apply_to_list(target_list, diff)
```

### ObjectPool

`ObjectPool` is a typed, thread-safe object recycler that reduces GC pressure in hot allocation paths. A `reset` callable clears transient state before an object re-enters the pool. The pool is guarded by a lock so it can be shared between background workers and the main frame thread.

```python
from gui_do import ObjectPool

pool: ObjectPool[MyEvent] = ObjectPool(
    factory=lambda: MyEvent.__new__(MyEvent),
    reset=lambda e: e.clear(),
    max_size=64,
)
pool.preallocate(16)

event = pool.acquire()
# … fill event fields …
pool.release(event)

stats = pool.stats()  # {"size": 15, "hits": 1, "misses": 0, "discards": 0}
```

### SceneSnapshot and NodeSnapshot

`SceneSnapshot` serializes and restores the rect, visibility, and enabled-state of nodes identified by `control_id`. It integrates with `CommandHistory` for structural undo/redo and with `SettingsRegistry` for workspace persistence. Only data state is serialized; callbacks and subscriptions are not touched. `NodeSnapshot` is the exported per-node record type.

```python
from gui_do import SceneSnapshot

# Capture current layout:
before = SceneSnapshot.capture(app.scene)

# ... user moves or resizes controls ...

# Restore:
before.restore(app.scene)

# Persist to disk:
before.save("workspace.json")

# Load and restore on next launch:
snap = SceneSnapshot.load("workspace.json")
snap.restore(app.scene)
```

Each `NodeSnapshot` carries `control_id`, `rect`, `visible`, `enabled`, and an `extra` dict for app-specific string payload.

### WorkspaceState and WorkspacePersistenceManager

`WorkspaceState` is a serializable session payload that bundles the active scene name, a `SceneSnapshot` dict, per-feature state blobs, settings values, and an optional dock layout. `WorkspacePersistenceManager` coordinates capture and restore across the scene, a `FeatureManager`, and any registered `SettingsRegistry` blocks.

```python
from gui_do import WorkspacePersistenceManager, WorkspaceState

manager = WorkspacePersistenceManager()
manager.register_settings("app", app.settings)   # optional

# Capture full session state:
state = manager.capture(app, feature_manager=app.features)
state.save("session.json")

# Restore on next launch:
state = WorkspaceState.load("session.json")
manager.restore(state, app, feature_manager=app.features)
```

`WorkspaceState` fields: `version`, `active_scene_name`, `scene_snapshot`, `feature_states`, `settings_blocks`, `metadata`, `dock_state`. `WorkspaceState.save` / `WorkspaceState.load` write and read JSON.

`DEFAULT_WORKSPACE_STATE_PATH` is the package-level default path constant (`~/.gui_do/workspace_state.json`) used by `run_entrypoint` and available for direct use when wiring `WorkspacePersistenceManager` manually.

```python
from gui_do import DEFAULT_WORKSPACE_STATE_PATH

print(DEFAULT_WORKSPACE_STATE_PATH)  # Path('/home/user/.gui_do/workspace_state.json')
```

---

## Scheduling and Animation [Back to Top](#table-of-contents)

### TaskScheduler

`TaskScheduler` runs background callables in a thread pool and lets the UI poll for completions, failures, and task messages during `update()`.

```python
def work(task_id, payload):
    return payload * 2


app.scheduler.add_task("double", work, parameters=21)
finished = app.scheduler.update()
if "double" in finished:
    print(app.scheduler.pop_result("double"))
```

Use `send_message(...)` for in-flight task progress, `get_failed_tasks()` for errors, and `clear_events()` after consuming finished/failed event lists.

### CooperativeScheduler

`CooperativeScheduler` runs generator coroutines on the frame thread — no background threads or OS timer APIs. Complex multi-step sequences (tutorials, cutscenes, test scripts) can be written as linear `yield`-based generator functions. Yield tokens control suspension: `Pause` waits one frame, `Sleep` waits N seconds, `WaitForEvent` suspends until an `EventBus` topic fires, `WaitForSignal` waits for a `Signal`, `WaitUntil` waits for a predicate, and `WaitForAll` waits for a list of other handles.

```python
from gui_do import (
    CooperativeScheduler, CoroutineHandle,
    Pause, Sleep, WaitForSignal, WaitUntil, WaitForAll,
)

scheduler = CooperativeScheduler()

def intro_sequence():
    show_title()
    yield Sleep(1.5)
    fade_in_logo()
    yield Sleep(2.0)
    yield WaitUntil(lambda: user_pressed_any_key())
    start_game()

handle: CoroutineHandle = scheduler.start(intro_sequence())

# In your frame update:
scheduler.update(dt_seconds)

# Cancel at any time:
handle.cancel()
print(handle.is_done)
```

### Timers

`Timers` is a frame-driven repeating and one-shot timer registry.

```python
timers = app.timers
timers.add_timer("blink", 0.5, lambda: print("tick"))
timers.add_once("intro", 2.0, lambda: print("ready"))
timers.remove_timer("blink")
```

### SceneTimeline

`SceneTimeline` schedules callbacks at precise time offsets, fires looping events, and supports labeled seek points and duration-spanning region callbacks. All time tracking is frame-driven; call `update(dt)` once per frame. No OS timer APIs are used.

```python
from gui_do import SceneTimeline

timeline = SceneTimeline()

timeline.at(0.0,  lambda: spawn_title())
timeline.at(1.5,  lambda: fade_in_logo())
timeline.at(4.0,  lambda: start_music())
timeline.after(5.0, lambda: show_menu())    # relative to play() start

# Duration-spanning region callbacks:
timeline.between(1.5, 4.0, on_enter=show_logo, on_exit=hide_logo)

# Looping:
timeline.loop_every(0.5, lambda: blink_cursor())

# Seek labels:
timeline.label("intro_end", t=4.0)
timeline.seek_to_label("intro_end")

timeline.on_complete(lambda: show_end_screen())
timeline.play()

# Per frame:
timeline.update(dt_seconds)
```

### TweenManager

`TweenManager` animates numeric attributes or arbitrary functions over time. `TweenHandle` lets you cancel a tween or inspect completion.

```python
from gui_do import Easing

handle = app.tweens.tween(button.rect, "x", 240, 0.25, easing=Easing.EASE_IN_OUT)
print(handle.elapsed_fraction())
handle.cancel()
```

Use `tween_fn(...)` when you want eased callback-driven animation instead of direct attribute interpolation.

### AnimationSequence

`AnimationSequence` builds sequential and parallel animation flows on top of `TweenManager`. `AnimationHandle` cancels remaining steps.

```python
from gui_do import AnimationSequence

sequence = AnimationSequence(app.tweens)
handle = (
    sequence
    .then(target=button.rect, attr="x", end_value=200, duration_seconds=0.2)
    .wait(0.1)
    .parallel([
        {"target": button.rect, "attr": "x", "end_value": 260, "duration_seconds": 0.2},
        {"target": button.rect, "attr": "y", "end_value": 140, "duration_seconds": 0.2},
    ])
    .start()
)
```

### AnimationStateMachine

`AnimationStateMachine` connects control state changes (hover, press, idle, …) to `TweenManager`-driven `AnimationSequence` chains without requiring each control to manage tween cancellation and sequence selection. `AnimationTransitionMode` controls how an in-progress animation responds to a state change: `INTERRUPT` cancels immediately, `COMPLETE_THEN_TRANSITION` lets it finish, and `REVERSE_THEN_TRANSITION` plays it backward before switching.

```python
from gui_do import AnimationStateMachine, AnimationTransitionMode

asm = AnimationStateMachine(app.tweens)

def _hover_seq(seq):
    seq.then(target=button, attr="alpha", end_value=1.0, duration_seconds=0.1)

def _idle_seq(seq):
    seq.then(target=button, attr="alpha", end_value=0.85, duration_seconds=0.15)

asm.register_state("idle",  _idle_seq)
asm.register_state("hover", _hover_seq)
asm.register_transition("hover", "idle",
                         mode=AnimationTransitionMode.COMPLETE_THEN_TRANSITION)

asm.set_state("hover")
asm.set_state("idle")
asm.on_state_changed(lambda name: print("→", name))
```

### TransitionManager

`TransitionManager` connects control state changes (show, hide, enable, disable) to `TweenManager`-driven animations without requiring each control to write tween choreography manually. `TransitionSpec` declares the attribute to animate, start and end values, and duration. `TransitionEvent` values are `SHOW`, `HIDE`, `ENABLE`, and `DISABLE`. Multiple specs per event are supported for simultaneous multi-attribute animations.

```python
from gui_do import TransitionEvent, TransitionManager, TransitionSpec

tm = TransitionManager(app.tweens)

tm.register(
    overlay_panel,
    TransitionEvent.SHOW,
    TransitionSpec(attr="alpha", start_value=0.0, end_value=1.0, duration_seconds=0.25),
)
tm.register(
    overlay_panel,
    TransitionEvent.HIDE,
    TransitionSpec(attr="alpha", start_value=1.0, end_value=0.0, duration_seconds=0.2),
)

tm.on_show(overlay_panel)
tm.on_hide(overlay_panel)
```

Set `start_value=None` to read the current attribute value at trigger time, allowing graceful interruption of an in-progress animation.

### Debouncer and Throttler

`Debouncer` delays a callback until input is idle for a configurable period, restarting the timer on each new call. `Throttler` ensures a callback fires at most once per interval, discarding intermediate calls. Both use the frame-driven `Timers` service and require no OS-level timers.

```python
from gui_do import Debouncer, Throttler

# Debounce: wait 300 ms of inactivity before firing
debounce = Debouncer(delay_ms=300, callback=update_search, timers=app.timers)
text_input.on_change = lambda text: debounce.call(text)
debounce.cancel()
debounce.flush()   # fire immediately without waiting

# Throttle: fire at most once every 100 ms
throttle = Throttler(interval_ms=100, callback=update_preview)
scrollbar.on_change = lambda offset: throttle.call(offset)
```

---

## Overlay and Runtime Services [Back to Top](#table-of-contents)

### OverlayManager and OverlayHandle

`OverlayManager` owns transient overlay controls drawn above the scene graph. `OverlayHandle` dismisses a specific overlay and reports whether it is still open.

```python
from gui_do import LabelControl, OverlayPanelControl

panel = OverlayPanelControl("popup_panel", Rect(120, 120, 260, 120))
panel.add(LabelControl("msg", Rect(12, 12, 220, 24), "Hello from overlay"))
handle = app.overlay.show("popup", panel, dismiss_on_outside_click=True)
print(handle.is_open)
handle.dismiss()
```

### PopupPlacement

`PopupPlacement` computes where a transient popup should appear relative to an anchor rect so it stays on screen and flips sides when clipped. `Side` declares the preferred anchor side (`TOP`, `BOTTOM`, `LEFT`, `RIGHT`). `Alignment` controls cross-axis alignment (`START`, `CENTER`, `END`). `PlacementResult` carries the computed `rect` and the `actual_side` used. `compute_popup_rect` is a convenience standalone helper.

```python
from gui_do import Alignment, PlacementResult, PopupPlacement, Side, compute_popup_rect

placement = PopupPlacement(
    preferred_side=Side.BOTTOM,
    alignment=Alignment.START,
    offset=4,
)

result: PlacementResult = placement.compute(
    anchor_rect=button.rect,
    popup_size=(200, 120),
    screen_bounds=pygame.display.get_surface().get_rect(),
)
popup_panel.rect = result.rect

# Or with the one-call helper:
rect = compute_popup_rect(
    anchor=button.rect,
    popup_size=(200, 120),
    screen_bounds=pygame.display.get_surface().get_rect(),
    preferred_side=Side.BOTTOM,
)
```

### TooltipManager and TooltipHandle

`TooltipManager` tracks pointer hover state and renders a hint label after a configurable delay. Register any `UiNode` with a text string; `TooltipHandle` removes the registration when the control is destroyed.

```python
from gui_do import TooltipManager, TooltipHandle

tooltip_mgr = TooltipManager(default_delay_ms=500)
handle = tooltip_mgr.register(my_button, "Click to submit")

# In the scene update — supply the control_id of the currently hovered node, or None:
tooltip_mgr.update(dt_seconds, hovered_node_id=hovered_control_id)

# At the end of the draw pass:
if tooltip_mgr.is_visible:
    tooltip_mgr.draw(screen_surface, mouse_pos, app.theme)

# When the control is destroyed:
handle.unregister()
```

### ToastManager and ToastHandle

`ToastManager` shows transient or persistent banners. `ToastHandle` can dismiss a single toast.

```python
from gui_do import ToastSeverity

toast = app.toasts.show(
    "File saved",
    title="Success",
    severity=ToastSeverity.SUCCESS,
    duration_seconds=3.0,
)
```

Use `show_persistent(...)` for a toast that stays open until dismissed.

### DialogManager and DialogHandle

`DialogManager` provides alert, confirm, and prompt modals. `DialogHandle` dismisses a specific modal or reports whether it is open.

```python
app.dialogs.show_alert("Done", "Operation complete")
app.dialogs.show_confirm("Delete", "Delete file?", on_confirm=lambda: print("confirmed"))
app.dialogs.show_prompt("Rename", "New name", on_submit=lambda value: print(value))
```

### ContextMenuManager and ContextMenuHandle

`ContextMenuManager` renders a pointer-anchored menu from `ContextMenuItem` values. `ContextMenuHandle` closes a menu programmatically.

```python
from gui_do import ContextMenuItem, ContextMenuManager

menus = ContextMenuManager(app)
handle = menus.show(
    (x, y),
    [
        ContextMenuItem("Cut", action=lambda: None),
        ContextMenuItem("Copy", action=lambda: None),
        ContextMenuItem("", separator=True),
        ContextMenuItem("Paste", action=lambda: None),
    ],
)
```

### DragDropManager and DragPayload

`DragDropManager` coordinates typed drag sessions between source and target controls. `DragPayload` carries the drag kind and arbitrary data.

```python
from gui_do import DragPayload

payload = DragPayload(kind="file", data={"path": "notes.txt"})
app.drag_drop.begin_drag(payload)
```

### TransferData and TransferManager

`TransferData` is a multi-format transfer payload used for both clipboard and in-process drag exchanges. Each format is stored under a MIME-style key so consumers can request the most appropriate representation. `TransferManager` maintains a clipboard slot and an in-flight drag slot.

```python
from gui_do import TransferData, TransferManager

payload = TransferData(preferred_format="text/plain")
payload.set("text/plain", "Hello")
payload.set("application/json", '{"msg": "Hello"}')

tm = TransferManager()
tm.set_clipboard(payload)

data = tm.get_clipboard()
if data and data.has_format("text/plain"):
    print(data.get("text/plain"))

# Drag lifecycle:
tm.begin_drag(payload)
dropped = tm.end_drag()   # returns TransferData or None
```

### FileDialogManager, FileDialogOptions, and FileDialogHandle

`FileDialogManager` exposes separate open/save flows. `FileDialogOptions` configures title, start directory, filters, and selection rules. `FileDialogHandle` tracks the modal dialog state.

```python
from gui_do import FileDialogManager, FileDialogOptions

files = FileDialogManager(app)

files.show_open(
    FileDialogOptions(title="Open Image", filters=[("Images", [".png", ".jpg"]), ("All", ["*"])]),
    on_close=lambda paths: print(paths),
)

files.show_save(
    FileDialogOptions(title="Save As"),
    on_close=lambda paths: print(paths),
)
```

### ResizeManager

`ResizeManager` updates registered `ConstraintLayout` instances and notifies subscribers when the window size changes.

```python
from gui_do import ResizeManager

resize = ResizeManager(initial_size=(800, 600), event_bus=app.events)
resize.on_resize(lambda width, height: print(width, height))
resize.notify_resize(1024, 768)
```

### ClipboardManager

`ClipboardManager` is a thin wrapper over `pygame.scrap` with safe fallbacks when clipboard access is unavailable.

```python
from gui_do import ClipboardManager

ClipboardManager.copy("hello")
print(ClipboardManager.paste())
```

### CommandPaletteManager, CommandEntry, and CommandPaletteHandle

`CommandPaletteManager` shows a searchable command launcher using the overlay system. `CommandEntry` is the exported command record. `CommandPaletteHandle` closes an open palette or inspects its open state.

Construct with an `OverlayManager` and optionally an `app` for automatic background right-click registration. Passing `action_registry` auto-refreshes entries from an `ActionRegistry` on every `show()` call.

Calling `show(app)` when the palette is already visible closes it (toggle behavior). The keyboard arrow keys move the selection, and Enter or Space activate the selected command. The search input filters results in real time.

```python
import pygame
from gui_do import CommandEntry, CommandPaletteManager

palette = CommandPaletteManager(app.overlay)
palette.register(CommandEntry("save", "Save File", action=lambda: print("save"), category="File"))
palette.register(CommandEntry("open", "Open File", action=lambda: print("open"), category="File"))

# Open / toggle via F5 in specific scenes — single call handles registration and binding:
palette.bind_toggle_key(app, pygame.K_F5, scene=["main", "editor"])

# Or open programmatically:
handle = palette.show(app)
print(handle.is_open)
handle.close()
```

`CommandPaletteManager` methods:

- `register(entry)` — add or replace a `CommandEntry`.
- `register_action_registry(registry, *, context=None, category=None, clear_existing=False)` — bulk-register entries projected from an `ActionRegistry`; `category` filters to one category string.
- `unregister(entry_id)` — remove an entry by id; returns `True` if it existed.
- `entry_count()` / `entries()` — inspect registered entries.
- `show(app, *, rect=None)` — open the palette (or close it if already open); returns a `CommandPaletteHandle`.
- `hide()` — close the palette without executing a command.
- `bind_toggle_key(app, key, *, scene=None, action_id="command_palette_toggle")` — register an action and bind `key` so it calls `show()` as a toggle. `scene` may be a single scene name, a list of scene names, or `None` for global binding.
- `is_open` — property; `True` while the palette overlay is visible.

`CommandPaletteHandle` exposes `is_open` (property) and `close()`.

### ShortcutHelpOverlay

`ShortcutHelpOverlay` auto-generates a keyboard shortcut reference panel from the registered `ActionRegistry` and `KeyChordManager` — no manual maintenance needed. Sections and entries are sorted alphabetically within each category. The overlay is shown/hidden through the `OverlayManager`.

```python
from gui_do import ShortcutEntry, ShortcutHelpOverlay, ShortcutSection

help_overlay = ShortcutHelpOverlay(app)

help_overlay.show()
help_overlay.hide()
help_overlay.toggle()

for section in help_overlay.sections:
    print(f"[{section.title}]")
    for entry in section.entries:
        print(f"  {entry.chord_display:<20} {entry.label}")
```

`ShortcutSection` fields: `title`, `entries`. `ShortcutEntry` fields: `label`, `chord_display`, `description`, `category`.

### CanvasViewport

`CanvasViewport` provides portable pan/zoom coordinate transform math for `CanvasControl` users. It converts between screen space (relative to the canvas rect) and content space, supporting anchor-preserving zoom, pan, fit-to-content, and reset operations.

```python
from gui_do import CanvasViewport
import pygame

vp = CanvasViewport(content_size=(4096, 4096), min_scale=0.05, max_scale=16.0)

# Convert screen position to content coordinates:
content_pos = vp.to_canvas(packet.local_pos)

# Zoom toward the cursor:
factor = 1.1 if packet.wheel_delta > 0 else 1.0 / 1.1
vp.zoom_at(anchor=packet.local_pos, factor=factor)

# Pan from pointer motion:
vp.pan(packet.rel)

# Fit all content on screen:
vp.fit_content(canvas.rect.size)

# Reset to 1:1:
vp.reset()

# Transform a content rect to a screen rect for drawing:
screen_rect = pygame.Rect(
    *vp.to_screen(content_rect.topleft),
    content_rect.w * vp.scale,
    content_rect.h * vp.scale,
)
```

### ErrorBoundary

`ErrorBoundary` wraps a single child `UiNode` and silently catches exceptions thrown during `draw` or `handle_event`. When an error is caught the child is replaced by an error-placeholder visual so the rest of the scene continues rendering normally. Inspired by React error boundaries.

```python
from gui_do import ErrorBoundary

boundary = ErrorBoundary(
    child=my_control,
    on_error=lambda exc: logger.error("Control error", exc_info=exc),
    error_text="Widget unavailable",
)
scene.add(boundary)

if boundary.has_error:
    boundary.recover()
```

### CursorManager

`CursorManager` is a priority-stack cursor management service for pygame applications. Controls push cursor requests with a priority level; each frame the manager resolves the highest-priority active request and calls `pygame.mouse.set_cursor()` only when the resolved shape changes, avoiding redundant system calls. `CursorShape` is an enum of portable system cursor shapes backed by `pygame.SYSTEM_CURSOR_*` constants. `CursorHandle` releases a cursor request when no longer needed.

```python
from gui_do import CursorManager, CursorShape

cursor_mgr = CursorManager()

# Push a resize cursor during a splitter drag:
handle = cursor_mgr.push(CursorShape.RESIZE_H, priority=10)

# Per frame:
cursor_mgr.update()

# Release when the drag ends; the previous cursor is restored:
handle.release()

# Reset to the default arrow (e.g. on scene change):
cursor_mgr.reset()
```

Available shapes: `ARROW`, `TEXT`, `WAIT`, `CROSSHAIR`, `RESIZE_NW_SE`, `RESIZE_NE_SW`, `RESIZE_H`, `RESIZE_V`, `RESIZE_ALL`, `FORBIDDEN`, `HAND`.

---

## Menu System [Back to Top](#table-of-contents)

### MenuBarControl and MenuEntry

`MenuBarControl` renders a horizontal top-level menu bar. Each `MenuEntry` contains a label plus `ContextMenuItem` rows for its flyout.

```python
from gui_do import ContextMenuItem, MenuBarControl, MenuEntry

bar = MenuBarControl(
    "menubar",
    Rect(0, 0, 800, 28),
    entries=[
        MenuEntry("File", items=[ContextMenuItem("Open", action=lambda: None)]),
        MenuEntry("Edit", items=[ContextMenuItem("Undo", action=lambda: None)]),
    ],
)
app.scene.add(bar)
```

### SceneMenuStripControl

`SceneMenuStripControl` is a reusable dynamic menu strip for a target scene. The `Scenes` and `Windows` built-in sections are opt-in via `scenes_shown=True` and `windows_shown=True` (both default to `False`). A `File` section appears only when `file_items_provider` is set and returns items. It rebuilds entries before pointer interactions so scene names and window visibility toggles stay current. Use `extra_entries_provider` to inject additional top-level menus when needed.

```python
from gui_do import MenuEntry, SceneMenuStripControl

def extra_entries() -> list[MenuEntry]:
    return [MenuEntry("Tools", [...])]

menu = SceneMenuStripControl(
    "main_menu",
    Rect(0, 0, 1280, 28),
    app,
    scene_name="main",
    scenes_shown=True,
    windows_shown=True,
    extra_entries_provider=extra_entries,
    on_scene_selected=lambda scene: transitions.go(scene),
    on_window_toggled=lambda window, visible: sync_window_toggle(window, visible),
)
app.add(menu, scene_name="main")
```

### MenuBarManager

`MenuBarManager` is the feature-friendly registration layer for top-level menus. It accumulates menu contributions and builds one `MenuBarControl` in registration order.

```python
from gui_do import ContextMenuItem, MenuBarManager

manager = MenuBarManager()
manager.register_menu("File", [ContextMenuItem("Open", action=lambda: None)])
manager.register_menu("File", [ContextMenuItem("Save", action=lambda: None)])
manager.register_menu("View", [ContextMenuItem("Zoom In", action=lambda: None)])

bar = manager.build("menubar", Rect(0, 0, 800, 28), app)
app.scene.add(bar)
```

---

## Notification System [Back to Top](#table-of-contents)

### NotificationCenter and NotificationRecord

`NotificationCenter` stores an activity log, optionally sourced from `EventBus` topics. `NotificationRecord` is the exported record shape.

```python
from gui_do import NotificationCenter, NotificationRecord, ToastSeverity

notifications = NotificationCenter(app.events, max_records=200)
notifications.subscribe("build.done", severity=ToastSeverity.SUCCESS, title="Build")
notifications.unread_count.subscribe(lambda value: print("unread", value))
notifications.add(NotificationRecord("Deployment complete", severity=ToastSeverity.SUCCESS))
```

### NotificationPanelControl

`NotificationPanelControl` renders a `NotificationCenter` inside an overlay-friendly panel.

```python
from gui_do import NotificationPanelControl

panel = NotificationPanelControl("notifications", Rect(560, 40, 320, 420), notifications)
app.overlay.show("notifications", panel, dismiss_on_outside_click=True)
```

---

## Scene Transitions [Back to Top](#table-of-contents)

### SceneTransitionManager and SceneTransitionStyle

`SceneTransitionManager` animates scene changes instead of switching instantly. `SceneTransitionStyle` enumerates the built-in transition styles.

```python
from gui_do import SceneTransitionManager, SceneTransitionStyle

transitions = SceneTransitionManager(app, default_style=SceneTransitionStyle.FADE, default_duration=0.3)
transitions.set_style("editor", SceneTransitionStyle.SLIDE_LEFT, duration=0.25)
transitions.go("editor")
```

Available styles are `NONE`, `FADE`, `SLIDE_LEFT`, `SLIDE_RIGHT`, `SLIDE_UP`, and `SLIDE_DOWN`.

---

## Feature System [Back to Top](#table-of-contents)

### Feature Types and FeatureMessage

Features are the reusable lifecycle unit for gui_do application composition.

| Type | Purpose |
|---|---|
| `Feature` | Base lifecycle class |
| `DirectFeature` | Owns direct UI and direct draw/update hooks |
| `LogicFeature` | Provides pure logic endpoints for other features |
| `RoutedFeature` | Routes incoming feature messages by topic or command |

`FeatureMessage` is the exported envelope passed between features.

```python
from pygame import Rect
from gui_do import Feature, LabelControl


class StatusFeature(Feature):
    def build(self, host) -> None:
        self.label = host.scene.add(LabelControl("status", Rect(20, 20, 200, 24), "Ready"))

    def handle_event(self, host, event) -> bool:
        return False
```

Within a feature, use `self.send_message(...)`, `self.bind_logic(...)`, and `self.send_logic_message(...)` to communicate with other registered features.

### FeatureManager

`FeatureManager` registers features, validates host requirements, dispatches lifecycle hooks, and routes messages between features.

```python
features = app.features
features.register(StatusFeature("status", scene_name="main"), host=app)
features.build_features(app)
features.bind_runtime(app)
next_tab_index = features.configure_accessibility(app, 10)
features.send_message("status", "other_feature", {"command": "refresh"})
```

It also exposes direct-feature update/draw helpers, feature prewarm support, state save/restore, logic binding, and runnable registration.

### Feature Layout Helpers

`gui_do` exports a collection of helper functions and small types from `feature_lifecycle` that cover the repetitive wiring common to every feature: font-role setup, action registration, rect geometry, control placement, and window management.

**Font and action setup:**
- `setup_standard_font_roles(app)` — registers `body`, `title`, `caption`, and `code` font roles using the active theme font.
- `register_standard_actions(app)` — registers the common app-level actions (`file.new`, `file.open`, `file.save`, `edit.undo`, `edit.redo`, etc.) with `ActionManager`.

**Rect helpers:**
- `inset_rect(rect, inset)` — returns a rect shrunk by `inset` on all sides.
- `centered_horizontal_strip_layout(rect, strip_height)` — returns a rect centered vertically in `rect`.
- `split_slot_bounds(rect, n)` — splits `rect` into `n` equal horizontal slots; returns list.
- `partition_rects(rect, weights, axis)` — splits proportionally by `weights` along `axis` (`"x"` or `"y"`).

**Control placement:**
- `place_control(layout, control, label_text, ...)` — grid-place a control with an optional label in the current layout pass; returns a `PlacedControl`.
- `place_control_unlabeled(layout, control, ...)` — like `place_control` without a label cell.
- `register_placed_control(host, placed)` — register a `PlacedControl` with the scene so it participates in focus traversal and accessibility.
- `add_group_label(layout, text)` — adds a full-width group heading row to the current layout pass.

**Window management:**
- `create_anchored_feature_window(host, rect, title, ...)` — convenience for creating a titled, draggable feature `WindowControl` and registering it with the scene.
- `add_window_scene_menu_strip(host, ...)` — attach a `SceneMenuStrip` to a feature window.
- `set_window_visible_state(window, visible)` / `toggle_window_visibility(window)` — idiomatic show/hide helpers.
- `minimize_window_menu_entries(windows, app)` — build `MenuEntry` list for minimizing a set of windows from a menu.

**Small types:**
- `TabPanelManager` — manages tab-based panel switching within a feature window.
- `WindowRelativeRect` — a rect descriptor expressed relative to a parent window rect; resolved at build time.
- `FrameTimer` — per-feature frame-time accumulator for update-budget tracking.
- `PlacedControl` — named tuple returned by `place_control`; fields: `name`, `control`, `label`.
- `resolve_scene_selection_callback(host, cb)` — wraps a callback so it always references the currently active scene.

---

## Theme and Graphics [Back to Top](#table-of-contents)

### ColorTheme

`ColorTheme` is the built-in semantic palette plus text-rendering helper used by the runtime. The active scene theme is available as `app.theme`.

```python
theme = app.theme
text_surface = theme.render_text("Hello", role="body")
print(theme.font_roles())
```

`ColorTheme` also exposes `register_font_role(...)` for adding or replacing named font roles.

### ThemeManager and DesignTokens

`ThemeManager` manages named token sets and exposes reactive `active_theme` and `active_tokens` observables. `DesignTokens` is the exported token container.

```python
from gui_do import ThemeManager

theme_manager = ThemeManager()
theme_manager.register_theme("contrast", {"primary": (255, 220, 0), "background": (20, 20, 20)})
theme_manager.switch("contrast")
print(theme_manager.token("primary"))
```

### ScopedTheme and ScopedThemeManager

`ScopedTheme` holds a set of design-token overrides that apply to a declared UI subtree without changing the global theme. `ScopedThemeManager` manages a push/pop scope stack and resolves token names by climbing from the innermost scope to the global `DesignTokens`.

```python
from gui_do import ScopedTheme, ScopedThemeManager

dark_sidebar = ScopedTheme(
    {"surface": (20, 20, 30), "text": (230, 230, 240)},
    name="dark-sidebar",
)

scope_mgr = ScopedThemeManager(app.theme.active_tokens)

# Context-manager style:
with scope_mgr.scope(dark_sidebar):
    color = scope_mgr.resolve("surface")   # → (20, 20, 30)
    color = scope_mgr.resolve("primary")   # falls through to global tokens

# Manual push/pop:
scope_mgr.push(dark_sidebar)
color = scope_mgr.resolve("text")
scope_mgr.pop()
```

### BuiltInGraphicsFactory

`BuiltInGraphicsFactory` builds cached visual surfaces for built-in controls. It is exposed as `app.graphics_factory` and used internally by control drawing. When the active theme or fonts change, controls can invalidate themselves and rebuild against the current factory output.

### FontManager

`FontManager` is the role-based font registry used by `ColorTheme`. Through `app.theme.fonts`, you can register named roles and resolve font instances by role and size.

```python
fonts = app.theme.fonts
fonts.register_role("caption", size=12, bold=False)
font = fonts.font_instance("caption", size=12)
print(font.text_size("gui_do"))
```

### FontRoleRegistry

`FontRoleRegistry` is the centralized role-definition manager for font roles. Define role specs once, then apply them to a `FontManager` (directly or through `ColorTheme.fonts`) so all scenes and features resolve consistent typography roles.

```python
from gui_do import FontRoleRegistry

registry = FontRoleRegistry()
registry.define("body", size=16)
registry.define("caption", size=12)

# Apply role definitions to any scene that needs them.
registry.apply(app, scene_name="main")

body_font = app.theme.fonts.font_instance("body", size=16)
```

### ShapeRenderer

`ShapeRenderer` exposes static drawing helpers for common decorated shapes that `pygame.draw` does not provide natively. All methods draw onto a caller-supplied `pygame.Surface` and return `None`.

```python
from gui_do import ShapeRenderer

ShapeRenderer.rounded_rect(surface, color=(60, 120, 200), rect=btn.rect, radius=6)
ShapeRenderer.pill(surface, color=(180, 60, 60), rect=label.rect)
ShapeRenderer.gradient_rect(surface, top_color=(40, 40, 40), bottom_color=(20, 20, 20),
                             rect=panel.rect, horizontal=False)
ShapeRenderer.drop_shadow(surface, rect=card.rect, radius=8, shadow_color=(0, 0, 0, 80),
                           offset=(2, 4))
ShapeRenderer.check_mark(surface, color=(60, 200, 60), rect=checkbox.rect, thickness=2)
```

### VectorPath

`VectorPath` is a resolution-independent 2D path builder. Paths are constructed from movement commands and rendered onto any `pygame.Surface` at draw time. Paths are immutable once built — `transform` returns a new `VectorPath` without mutating the original.

```python
from gui_do import VectorPath

path = (
    VectorPath()
    .move_to(0, 0)
    .line_to(100, 0)
    .cubic_bezier(cp1=(120, 0), cp2=(120, 60), end=(100, 60))
    .arc(center=(50, 60), radius=50, angle_start=0, angle_end=180)
    .close()
)

path.fill(surface, color=(80, 140, 220))
path.stroke(surface, color=(20, 60, 140), width=2)

if path.contains_point(mx, my):
    hover_path = True

scaled = path.transform(translate=(10, 10), scale=2.0, rotate=45.0)
```

### SurfaceCompositor and Layer

`SurfaceCompositor` manages Z-ordered named layers and composites them onto the screen each frame. Each `Layer` has its own off-screen `pygame.Surface`; draw into the layer surface during the frame, then call `compose` to blit all visible layers in Z order with per-layer opacity.

```python
from gui_do import Layer, SurfaceCompositor

compositor = SurfaceCompositor(screen)
compositor.add_layer("background", z_index=0, opacity=1.0, visible=True)
compositor.add_layer("ui",         z_index=10, opacity=1.0)
compositor.add_layer("hud",        z_index=20, opacity=0.85)

bg_surface = compositor.layer_surface("background")
bg_surface.fill((20, 20, 30))

compositor.set_layer_opacity("hud", 0.5)
compositor.set_layer_visible("hud", False)

compositor.compose(screen, dirty_rects=None)  # pass dirty_rects for partial updates
```

### SurfaceEffects

`SurfaceEffects` applies post-processing to a surface and returns a new surface. Uses numpy when available for performance; falls back to pure Python otherwise.

```python
from gui_do import SurfaceEffects

blurred  = SurfaceEffects.blur(surface, radius=4)
grey     = SurfaceEffects.greyscale(surface)
tinted   = SurfaceEffects.tint(surface, color=(80, 40, 160), alpha=128)
bright   = SurfaceEffects.brightness(surface, factor=1.3)
pixel    = SurfaceEffects.pixelate(surface, block_size=8)
vignette = SurfaceEffects.vignette(surface, strength=0.6)
```

### DirtyRegionTracker

`DirtyRegionTracker` accumulates dirty rects during a frame and provides a consolidated list for partial-display update. Integrate with `pygame.display.update(rects)` to skip unchanged areas of the screen.

```python
from gui_do import DirtyRegionTracker

tracker = DirtyRegionTracker()
tracker.mark_dirty(control.rect)
tracker.mark_dirty(tooltip.rect)

if tracker.has_dirty:
    rects = tracker.consume_dirty_regions()  # resets tracker
    pygame.display.update(rects)

# Force a full redraw:
tracker.mark_all_dirty(screen.get_rect())
```

### DrawContext and DrawPhase

`DrawContext` is the render context passed to every `UiNode.draw()` call. It carries the current target surface, clip rect, draw phase, opacity, and local offset. `DrawPhase` is an enum that controls which layer of the node's visual is currently being drawn.

```python
from gui_do import DrawContext, DrawPhase

# DrawPhase enum values:
DrawPhase.BACKGROUND   # drawn first — fills, shadows
DrawPhase.FOREGROUND   # text, icons, content
DrawPhase.OVERLAY      # borders, selections, badges
DrawPhase.DEBUG        # developer diagnostics (zero cost when disabled)

# In a custom UiNode.draw():
def draw(self, ctx: DrawContext) -> None:
    if ctx.phase == DrawPhase.BACKGROUND:
        ctx.surface.fill(self.bg_color, ctx.clip_rect)
    elif ctx.phase == DrawPhase.FOREGROUND:
        child_ctx = ctx.clip_to(self.inner_rect())
        for child in self._children:
            child.draw(child_ctx)
```

`ctx.clip_to(rect)` returns a sub-`DrawContext` for child drawing with an adjusted clip and offset.

### AssetRegistry

`AssetRegistry` is a reference-counted surface and font cache with optional file hot-reload. Call `check_hot_reload()` on a timer or each frame to detect changed files; modified assets are reloaded and all subscribers notified automatically.

```python
from gui_do import AssetRegistry

assets = AssetRegistry()
surf = assets.get_surface("icons/play.png", size=(32, 32))
assets.release_surface("icons/play.png", size=(32, 32))

# Hot-reload check (compares os.stat mtime):
assets.check_hot_reload()

stats = assets.stats()
# {"surfaces": {"loaded": 5, "refs": 12}, "fonts": {"loaded": 2, "refs": 8}}
```

### DebugOverlay

`DebugOverlay` is a developer diagnostic layer drawn during `DrawPhase.DEBUG`. It has zero production cost when `enabled = False`. It renders widget bounding rects color-coded by node type, the current focus chain, dirty region flashes, the hovered node highlight, a live FPS counter, and a rolling event log tail. Wire it into your feature's draw call for zero-configuration introspection.

```python
from gui_do import DebugOverlay

debug = DebugOverlay()
debug.enabled = True
debug.log_event("pointer_down")

# In your render loop — after all scene drawing:
debug.draw(screen, scene, theme, focused_id=focus.focused_node, hovered_id=hovered, fps=fps)
```

---

## Game and Media [Back to Top](#table-of-contents)

### SpriteSheet and FrameAnimation

`SpriteSheet` slices a surface atlas into indexed frames in left-to-right, top-to-bottom order (0-based). `FrameAnimation` drives frame-sequenced playback from a sheet. Call `anim.update(dt)` per frame and `anim.draw(surface, pos)` to render at a position. `current_surface` exposes the current frame surface for custom drawing.

```python
from gui_do import FrameAnimation, SpriteSheet

sheet = SpriteSheet(atlas_surface, frame_w=64, frame_h=64)
anim  = FrameAnimation(sheet, frames=[0, 1, 2, 3, 4, 3, 2, 1], fps=12, loop=True)

# Per frame:
anim.update(dt)
anim.draw(surface, (100, 200))

# Control:
anim.pause()
anim.play()
anim.reset()
anim.seek_frame(3)
```

### AnimatedImageControl

`AnimatedImageControl` is a scene-graph `UiNode` that renders a `FrameAnimation` directly into a layout rect. Set `scale=True` (default) to fill the rect; set `scale=False` to blit at native frame size clipped to the rect. Swap animations at runtime via `ctrl.animation = new_anim`.

```python
from gui_do import AnimatedImageControl, FrameAnimation, SpriteSheet

sheet = SpriteSheet(atlas_surface, frame_w=64, frame_h=64)
anim  = FrameAnimation(sheet, frames=list(range(8)), fps=12)
ctrl  = AnimatedImageControl("player", Rect(100, 100, 64, 64), animation=anim)
app.scene.add(ctrl)

# In update:
ctrl.tick(dt)
```

### TileSet and TileMap

`TileSet` slices a surface atlas into indexed tiles. `TileMap` manages a 2D grid of tile IDs and renders only tiles visible within the camera rect (frustum culling). Tile ID `TileSet.EMPTY` (`-1`) skips a cell. Coordinate helpers: `tile_to_world(col, row)` and `world_to_tile(x, y)`.

```python
from gui_do import TileMap, TileSet
from pygame import Rect

tile_set = TileSet(atlas_surface, tile_w=32, tile_h=32)
tile_map = TileMap(tile_w=32, tile_h=32, cols=20, rows=15, tile_set=tile_set)

tile_map.fill(0)                    # fill entire map with tile 0
tile_map.set_tile(5, 3, 2)         # place tile 2 at column 5, row 3
tile_map.fill_rect(0, 0, 5, 5, 1)  # fill 5×5 top-left block with tile 1

camera_rect = Rect(scroll_x, scroll_y, screen_w, screen_h)
tile_map.draw(surface, camera_rect, offset=(0, 0))
```

### ParticleSystem

`ParticleSystem` is a frame-driven 2D particle emitter that draws using `pygame.draw` — no separate assets required. `Emitter` configures spawn parameters. Set `rate=0` for one-shot burst mode. Call `ps.update(dt)` and `ps.draw(surface)` each frame.

```python
from gui_do import Emitter, ParticleSystem

ps = ParticleSystem()
burst = Emitter(
    x=200, y=200,
    rate=0, burst_count=60,
    lifetime=(0.5, 1.5),
    speed=(80, 200),
    angle_range=(0, 360),
    size=(3, 7),
    colors=[(255, 80, 80), (80, 255, 80), (80, 80, 255)],
    gravity=300,
)
ps.add_emitter(burst)

# Per frame:
ps.update(dt)
ps.draw(surface)

ps.remove_emitter(burst)
ps.clear()
```

---

## Localization [Back to Top](#table-of-contents)

### StringTable and LocaleRegistry

`StringTable` is a flat key-to-text mapping for one locale. `LocaleRegistry` holds multiple tables, exposes a reactive `current_locale` observable, and provides `t(key)` for locale-aware string look-up. When the active locale changes, subscribers are notified automatically so UI strings can be refreshed without manual tracking.

```python
from gui_do import StringTable, LocaleRegistry

registry = LocaleRegistry(default_locale="en")
registry.register(StringTable("en", {
    "app.title":     "My Application",
    "button.ok":     "OK",
    "button.cancel": "Cancel",
}))
registry.register(StringTable("es", {
    "app.title":     "Mi Aplicación",
    "button.ok":     "Aceptar",
    "button.cancel": "Cancelar",
}))

# Look up a string with the active locale:
label.text = registry.t("app.title")          # "My Application"

# Switch locale — subscribers are notified:
registry.set_locale("es")
label.text = registry.t("app.title")          # "Mi Aplicación"

# React to locale changes:
registry.current_locale.subscribe(lambda _: refresh_ui())

# Fall back to a literal when a key is missing:
label.text = registry.t("missing.key", fallback="Unknown")
```

Call `registry.available_locales()` to list registered locale IDs and `registry.current_locale.value` to read the active locale ID.

---

## Introspection [Back to Top](#table-of-contents)

### ui_property and PropertyDescriptor

`ui_property` is a decorator that annotates Python `property` descriptors on `UiNode` subclasses with display metadata: `label`, `type`, `min`, `max`, `group`, and `read_only`. `PropertyDescriptor` is the exported metadata record holding those fields. This lets tooling such as debug inspectors, settings panels, and theme editors discover and render a control's properties without hard-coding its internals.

```python
from gui_do import ui_property

class MyControl(PanelControl):
    def __init__(self, ...):
        super().__init__(...)
        self._alpha: float = 1.0

    @property
    @ui_property(label="Opacity", type="float", min=0.0, max=1.0, group="Appearance")
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, v: float) -> None:
        self._alpha = float(v)
        self.invalidate()
```

### PropertyRegistry

`PropertyRegistry` scans class hierarchies and collects `ui_property`-annotated descriptors. `property_registry` is the module-level singleton instance used by controls and tooling alike.

```python
from gui_do import property_registry, PropertyDescriptor

# Retrieve all annotated descriptors for a class:
descs = property_registry.descriptors_for(MyControl)
for d in descs:
    print(d.name, d.label, d.type, d.group)

# All classes that have registered properties:
classes = property_registry.all_classes()
```

Descriptors are automatically collected the first time `descriptors_for` is called for a class and cached for subsequent look-ups.

### PropertyInspectorModel and PropertyInspectorPanel

`PropertyInspectorModel` wraps a live object and surfaces its `ui_property`-annotated attributes as `InspectedProperty` records, grouped by the `group` field of each `PropertyDescriptor`. `PropertyInspectorPanel` renders the model as a scrollable two-column panel (label | value).

```python
from gui_do import PropertyInspectorModel, PropertyInspectorPanel, InspectedProperty
from pygame import Rect

model = PropertyInspectorModel(my_button)

# Read all properties:
for prop in model.properties():           # List[InspectedProperty]
    print(prop.descriptor.label, prop.value)

# Read by group:
for group, props in model.grouped().items():
    print(f"-- {group} --")
    for p in props:
        print(" ", p.descriptor.name, "=", p.value)

# Set a property value programmatically:
model.set_value("width", 200)

# Render as a scrollable panel:
panel = PropertyInspectorPanel("inspector", Rect(0, 0, 300, 400), model)
app.scene.add(panel)
panel.refresh()   # call after mutating the target object
```

`InspectedProperty` fields: `descriptor` (`PropertyDescriptor`), `value` (current attribute value). `PropertyInspectorPanel` is read-only by default.

---

## Telemetry [Back to Top](#table-of-contents)

gui_do includes opt-in runtime telemetry plus offline analysis helpers.

```python
from gui_do import (
    TelemetrySample,
    analyze_telemetry_log_file,
    configure_telemetry,
    render_telemetry_report,
    telemetry_collector,
)

configure_telemetry(enabled=True, log_file="telemetry.jsonl", max_samples=10000)
collector = telemetry_collector()
collector.record(TelemetrySample(feature_name="render", duration_ms=12.4))

analysis = analyze_telemetry_log_file("telemetry.jsonl")
print(render_telemetry_report(analysis))
```

The telemetry exports are `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_records`, `analyze_telemetry_log_file`, `load_telemetry_log_file`, and `render_telemetry_report`.

---

## Public API Index [Back to Top](#table-of-contents)

The following list is the complete public package export surface from `gui_do.__all__`, grouped by concept.

### Application and Loop

- `create_display`
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
- `SceneMenuStripControl`
- `TreeControl`
- `TreeNode`
- `NotificationPanelControl`
- `ScrollViewControl`
- `SpinnerControl`
- `RangeSliderControl`
- `ColorPickerControl`
- `TextFlow`
- `TextSpan`
- `ProgressBarControl`
- `AnimatedImageControl`

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
- `FlowLayout`
- `FlowItem`
- `GridLayout`
- `GridTrack`
- `GridPlacement`
- `LayoutAnimator`
- `LayoutPass`
- `MeasureContext`
- `ArrangeContext`
- `LayoutRoot`
- `ResponsiveLayout`
- `Breakpoint`
- `DockPane`
- `DockTabs`
- `DockSplit`
- `DockWorkspace`
- `DockWorkspacePanel`
- `SnapGrid`
- `AlignmentGuide`
- `SnapComposer`
- `SnapTarget`
- `Viewport`

### Events, Input, and Core Runtime

- `Signal`
- `SignalConnection`
- `ActionManager`
- `ActionDescriptor`
- `ActionRegistry`
- `ActionContext`
- `ActionMiddleware`
- `EventManager`
- `EventBus`
- `FocusManager`
- `FocusScope`
- `FocusScopeManager`
- `FocusRing`
- `WindowFocusManager`
- `FontManager`
- `FontRoleRegistry`
- `EventPhase`
- `EventType`
- `GuiEvent`
- `ValueChangeCallback`
- `ValueChangeReason`
- `InvalidationTracker`
- `GestureRecognizer`
- `InputSnapshot`
- `KeyChordManager`
- `KeyChord`
- `ChordStep`
- `InputMap`
- `InputBinding`
- `EventRecorder`
- `EventPlayback`
- `RecordedEvent`

### Data and State

- `ObservableValue`
- `PresentationModel`
- `ComputedValue`
- `ObservableList`
- `ObservableDict`
- `ObservableStream`
- `ChangeKind`
- `CollectionChange`
- `CollectionView`
- `CollectionViewQuery`
- `Binding`
- `BindingGroup`
- `SelectionModel`
- `SelectionMode`
- `FormModel`
- `FormField`
- `ValidationRule`
- `FieldError`
- `Validator`
- `RequiredValidator`
- `RangeValidator`
- `LengthValidator`
- `PatternValidator`
- `CustomValidator`
- `DependentValidator`
- `ValidationPipeline`
- `ValidationResult`
- `WizardFlow`
- `WizardStep`
- `WizardHandle`
- `FormSchema`
- `SchemaField`
- `CommandHistory`
- `DocumentModel`
- `Command`
- `CommandTransaction`
- `StateMachine`
- `HierarchicalStateMachine`
- `SettingsRegistry`
- `SettingDescriptor`
- `Router`
- `RouteEntry`
- `TextFormatter`
- `NumericFormatter`
- `PatternFormatter`
- `FixedPatternFormatter`
- `VirtualItemSource`
- `FixedItemSource`
- `SortFilterProxySource`
- `AsyncDataProvider`
- `LoadState`
- `LoadStateKind`
- `DataCache`
- `CacheStats`
- `ListDiffCalculator`
- `ListDiff`
- `DiffInsert`
- `DiffRemove`
- `DiffMove`
- `ObjectPool`
- `SceneSnapshot`
- `NodeSnapshot`
- `WorkspaceState`
- `WorkspacePersistenceManager`
- `DEFAULT_WORKSPACE_STATE_PATH`

### Scheduling and Animation

- `TaskEvent`
- `TaskScheduler`
- `CooperativeScheduler`
- `CoroutineHandle`
- `Pause`
- `Sleep`
- `WaitForEvent`
- `WaitForSignal`
- `WaitUntil`
- `WaitForAll`
- `Timers`
- `SceneTimeline`
- `TweenManager`
- `TweenHandle`
- `Easing`
- `AnimationSequence`
- `AnimationHandle`
- `AnimationStateMachine`
- `AnimationTransitionMode`
- `TransitionManager`
- `TransitionSpec`
- `TransitionEvent`
- `Debouncer`
- `Throttler`

### Overlay and Runtime Services

- `OverlayManager`
- `OverlayHandle`
- `PopupPlacement`
- `PlacementResult`
- `Side`
- `Alignment`
- `compute_popup_rect`
- `TooltipManager`
- `TooltipHandle`
- `ToastManager`
- `ToastHandle`
- `ToastSeverity`
- `DialogManager`
- `DialogHandle`
- `DragDropManager`
- `DragPayload`
- `TransferData`
- `TransferManager`
- `ContextMenuManager`
- `ContextMenuItem`
- `ContextMenuHandle`
- `FileDialogManager`
- `FileDialogOptions`
- `FileDialogHandle`
- `ResizeManager`
- `ClipboardManager`
- `CommandPaletteManager`
- `CommandEntry`
- `CommandPaletteHandle`
- `ShortcutHelpOverlay`
- `ShortcutSection`
- `ShortcutEntry`
- `CanvasViewport`
- `CursorManager`
- `CursorHandle`
- `CursorShape`
- `ErrorBoundary`

### Menu and Notifications

- `MenuBarManager`
- `NotificationCenter`
- `NotificationRecord`

### Features and Scene Composition

- `Feature`
- `DirectFeature`
- `LogicFeature`
- `RoutedFeature`
- `FeatureMessage`
- `FeatureManager`
- `SceneTransitionManager`
- `SceneTransitionStyle`
- `TabPanelManager`
- `WindowRelativeRect`
- `FrameTimer`
- `PlacedControl`
- `resolve_scene_selection_callback`
- `minimize_window_menu_entries`
- `set_window_visible_state`
- `toggle_window_visibility`
- `create_anchored_feature_window`
- `add_window_scene_menu_strip`
- `inset_rect`
- `centered_horizontal_strip_layout`
- `split_slot_bounds`
- `partition_rects`
- `place_control`
- `place_control_unlabeled`
- `register_placed_control`
- `add_group_label`
- `setup_standard_font_roles`
- `register_standard_actions`

### Theme and Graphics

- `BuiltInGraphicsFactory`
- `ColorTheme`
- `ThemeManager`
- `DesignTokens`
- `ScopedTheme`
- `ScopedThemeManager`
- `ShapeRenderer`
- `VectorPath`
- `SurfaceCompositor`
- `Layer`
- `SurfaceEffects`
- `DirtyRegionTracker`
- `DrawContext`
- `DrawPhase`
- `AssetRegistry`
- `DebugOverlay`

### Game and Media

- `SpriteSheet`
- `FrameAnimation`
- `AnimatedImageControl`
- `TileSet`
- `TileMap`
- `ParticleSystem`
- `Emitter`
- `ParticleLayer`

### Localization

- `StringTable`
- `LocaleRegistry`

### Introspection

- `ui_property`
- `PropertyDescriptor`
- `PropertyRegistry`
- `property_registry`
- `PropertyInspectorModel`
- `InspectedProperty`
- `PropertyInspectorPanel`

### Spatial

- `SceneSpatialIndex`

### Telemetry

- `TelemetryCollector`
- `TelemetrySample`
- `configure_telemetry`
- `telemetry_collector`
- `analyze_telemetry_records`
- `analyze_telemetry_log_file`
- `load_telemetry_log_file`
- `render_telemetry_report`
