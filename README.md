[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do

### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=OVj54_BhDO4"><img src="https://img.youtube.com/vi/OVj54_BhDO4/0.jpg" alt="Demo Video"></img></a>

---

**gui_do** is a Python GUI framework built on pygame that brings a declarative, feature-lifecycle-oriented programming model to interactive desktop applications. Instead of wiring widgets imperatively, you describe application structure with data specs, and the bootstrap system reads those specs to initialize every system automatically — event routing, overlay dispatch, focus management, scene transitions, and lifecycle sequencing all happen without boilerplate. Reactive state objects (`ObservableValue`, `ObservableList`, `ObservableDict`) propagate changes to the UI instantly when their values change, with no polling required. gui_do is suited to Python developers building desktop tools, game interfaces, interactive simulations, data explorers, and multi-scene workbench applications.

## Strengths

- **Declarative runtime wiring** — `HostApplicationBindingSpec` and companion spec types describe what your application does; `bootstrap_host_application` builds everything from those descriptions automatically.
- **Feature lifecycle isolation** — every unit of functionality is a `Feature` subclass that owns its `build`, `bind_runtime`, `on_update`, `draw`, and `shutdown_runtime` phases independently of every other feature.
- **Reactive state** — `ObservableValue`, `ObservableList`, and `ObservableDict` notify subscribers when their content changes, so labels and controls update themselves without polling loops.
- **Composable overlays** — dialogs, toasts, tooltips, context menus, and the command palette share a unified routing infrastructure and are composable without framework modification.
- **Tiered API surface** — 32 tiers of exported names from high-level bootstrap helpers down to 2D scene graph, audio, and constraint layout, so you reach for exactly as much framework as your application needs.
- **Scene management** — multi-scene apps with animated slide and crossfade transitions, per-scene event routing, and scene-scoped lifecycle sequencing built in.
- **Persistence and migration** — workspace state is saved and restored across sessions with versioned snapshot migration; missing settings keys are silently skipped without aborting restore.
- **Accessibility and focus** — a semantic accessibility tree, configurable focus rings, and live region announcements support screen-reader-friendly application structure.
- **Built-in diagnostics** — telemetry spans in high-frequency paths, an event recorder and playback engine, and a property inspector panel for runtime introspection.
- **Extensible without framework changes** — new features add behavior by implementing lifecycle methods; the framework never needs to be modified to support new application patterns.

## Use Cases

**Developer tools and internal utilities.** gui_do's sortable list views, data grids, property inspectors, and reactive state make it well-suited to dashboards, configuration explorers, and debug front-ends.

**Game interfaces and HUDs.** The 2D scene graph (`SceneGraph2D`, `Node2D`, `Camera2D`), particle system, tile map, sprite sheet animation, and audio cue bus (`SoundEventBus`) give you the rendering primitives that game UIs need.

**Interactive simulations.** The cooperative scheduler, tween and animation state machine, dirty-region tracker, and canvas controls support cellular automata, physics visualizations, and parameter explorers that need smooth, frame-accurate updates.

**Data visualization tools.** `CollectionView`, `DataGridControl`, `ListViewControl`, `SortFilterProxySource`, and virtual item sources let you display and filter large data sets without reimplementing windowing logic.

**Multi-window workbench applications.** Tabbed windows, task panels, floating tool windows, dock workspaces, and scene navigation give you the chrome to build IDEs, editors, and workbench-style applications.

**Rapid prototyping.** The constraint layout engine (`ConstraintLayout`, `ConstraintLayoutEngine`), flex layout, flow layout, and responsive layout let you compose layouts declaratively, reducing the distance between design and working UI.

## Quick Look

The listing below shows the complete pattern: a `Feature` with reactive state, a button wired to an observable, and the three-line bootstrap sequence that starts the app.

```python
from pygame import Rect
from gui_do import (
    Feature, ObservableValue, LabelControl, ButtonControl, PanelControl,
    SceneBundleBindingSpec, HostApplicationBindingSpec,
    build_host_application_config, bootstrap_host_application,
)

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = self._sub = None

    def build(self, host):
        panel = host.app.add(
            PanelControl("root", host.screen_rect, draw_background=False),
            scene_name="main",
        )
        self._label = panel.add(LabelControl("lbl", Rect(20, 20, 300, 40), "Count: 0"))
        panel.add(ButtonControl("btn", Rect(20, 70, 140, 36), "Increment",
                                on_click=self._inc))

    def _inc(self):
        self._count.value += 1

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}")
        )

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None

config = build_host_application_config(HostApplicationBindingSpec(
    display_size=(800, 600), window_title="Counter",
    fonts={"default": {"file": "assets/font.ttf", "size": 14}},
    initial_scene_name="main",
    scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", pretty_name="Main"),),
    feature_entries=(("_counter", CounterFeature),),
))

class MyApp:
    def __init__(self): bootstrap_host_application(self, config)

MyApp().app.run_entrypoint(target_fps=60)
```

For a complete step-by-step explanation of every line above, see [TUTORIAL.md](TUTORIAL.md). For API details, see [MANUAL.md](MANUAL.md).

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial — start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

TUTORIAL.md teaches the framework by building a complete two-feature application from scratch, explaining both how and why at every step. By the end, you will understand the full gui_do programming model — reactive state, feature lifecycle, declarative bootstrap, actions, and cross-feature communication.

MANUAL.md is the comprehensive reference organized by system, covering all 32 API tiers with detailed tables, usage patterns, integration recipes, and appendices. It is the document to consult when you need exact API signatures, behavioral guarantees, or advanced composition patterns.

## Installation

Install from the repository root as a local editable package (no binary dependency compilation required):

```bash
python -m pip install -e . --no-deps
```

gui_do requires `pygame` and `numpy`. Install both before or after the above command:

```bash
python -m pip install pygame numpy
```

Verify the install:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

## Project Structure

```
gui_do/           Library source — 32 API tiers exported from gui_do/__init__.py
demo_features/    Runnable reference patterns — one folder per feature or scene cluster
tests/            Contract and behavioral test suite
docs/             Architecture boundary and runtime operating contracts
TUTORIAL.md       Step-by-step tutorial — start here
MANUAL.md         Complete system reference
```

Each folder under `demo_features/` is a self-contained feature package. Its `__init__.py` is the sole public surface used by the bootstrap; file organization inside the folder is free to change without affecting any external code. This is the established layout pattern for gui_do applications.

## See Also

- [TUTORIAL.md](TUTORIAL.md) — primary learning resource; builds a complete application from zero
- [MANUAL.md](MANUAL.md) — comprehensive system and API reference
- [demo_features/](demo_features/) — living reference patterns showing features, scenes, scheduling, graphics, accessibility, and more
- [docs/](docs/) — architecture boundary contracts, runtime operating contracts, and public API stability policy
- [gui_do/\_\_init\_\_.py](gui_do/__init__.py) — authoritative public API surface (all 32 tiers)
