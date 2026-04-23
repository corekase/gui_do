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

## What Changed Recently

This repository has moved to a stricter, explicitly documented contract model.

- Public API export surface is exact and locked by tests.
- Scene runtime is isolated by default:
  - inactive scenes suspend their scheduler execution
  - inactive scenes suspend scene timers
  - scene-scoped parts and screen lifecycle callbacks run only in their active scene
- Part lifecycle is framework-managed:
  - `bind_runtime(...)` is tracked centrally
  - `shutdown_runtime(...)` runs on unregister and app shutdown
- Scheduler fairness was hardened for low-core machines:
  - worker count uses `TaskScheduler.recommended_worker_count()`
  - per-frame message-dispatch budget is FPS-aware (`~12%` of frame time, clamped to `0.5-4.0 ms`)
- Input paths use canonical `GuiEvent` normalization at ingress.

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
