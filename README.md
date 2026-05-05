[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

# gui_do

### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=OVj54_BhDO4"><img src="https://img.youtube.com/vi/OVj54_BhDO4/0.jpg" alt="Demo Video"></img></a>

---

gui_do is a Python GUI framework built on pygame that uses declarative specs, a feature lifecycle model, and reactive state to wire applications together automatically. You describe your application structure in data objects — specs — and the bootstrap system reads those specs to handle event routing, overlay dispatch, focus management, scene transitions, and lifecycle sequencing without requiring manual coordination between components. Features are self-contained units that own their build, bind, update, and draw phases; the framework guarantees correct ordering and clean teardown. gui_do is designed for Python developers building desktop tools, game interfaces, interactive simulations, and data-visualization applications.

---

## Strengths

**Declarative runtime wiring.** Specs describe what the application contains; the bootstrap builds how everything connects. Features never need to know each other's internals.

**Feature lifecycle isolation.** Every feature owns its `build`, `bind_runtime`, `on_update`, `draw`, and `shutdown_runtime` phases. The framework calls them in the correct order and tears them down cleanly on scene exit.

**Reactive state.** `ObservableValue`, `ObservableList`, and `ObservableDict` notify subscribers when their content changes. Setting `.value` fires all registered callbacks immediately — no polling loop needed. `ComputedValue` derives new values from existing observables automatically.

**Composable overlays.** Dialogs, toasts, tooltips, context menus, a command palette, and a shortcut-help overlay are all first-class overlay types with consistent event routing and lifecycle management. See MANUAL.md §8.8.

**Tiered API surface.** 32 tiers from high-level bootstrap helpers down to a 2D scene graph, audio cues, and a pixel-buffer rendering backend. Use what you need; ignore what you do not.

**Scene management.** Multi-scene applications with animated transitions, per-scene event routing, per-scene schedulers, and scene-scoped state restoration.

**Persistence and migration.** Workspace state is saved and restored with versioned snapshots and a BFS migration graph — adding new settings fields never breaks old saves.

**Accessibility and focus.** A semantic accessibility tree, focus rings, tab ordering, and live-region announcements are built into the control model and wired automatically via specs.

**Built-in diagnostics.** Telemetry spans in all high-frequency paths, a property inspector, event recorder/playback, and a debug overlay give you visibility into application behavior at runtime.

**Extensible without framework changes.** New features add behavior by implementing lifecycle methods. The data-driven wiring layer means adding a feature to a scene is a one-line spec entry, not a wiring change.

---

## Use Cases

**Developer tools and internal utilities.** Dashboards, data explorers, parameter inspectors, and monitoring tools built on the sortable `ListViewControl`, `DataGridControl`, property inspector panel, and persistent workspace state.

**Game interfaces and HUDs.** Particle systems, tile maps, a 2D scene graph with `Camera2D`, sprite-sheet animation, and audio cues via `SoundEventBus` integrate naturally with the feature lifecycle.

**Interactive simulations.** Cellular automata, physics visualizations, and parameter explorers can use the canvas and dirty-region rendering system for efficient per-frame updates alongside standard UI controls.

**Data visualization tools.** Sortable and filterable lists, grids with `CollectionView`, charts rendered to a `CanvasControl`, and dirty-region tracking for partial redraws.

**Multi-window workbench applications.** Tabbed panels, floating tool windows, task panels, a command palette, and `DockWorkspace` compose into full workbench layouts managed by the scene and window systems.

**Rapid prototyping.** The constraint layout, flex layout, and cell-caret layout systems let you iterate on UI geometry quickly. Declarative specs mean wiring changes are data edits, not code restructuring.

For step-by-step guidance on building with gui_do, start with [TUTORIAL.md](TUTORIAL.md). For the complete API reference, see [MANUAL.md](MANUAL.md).

---

## Quick Look

One feature, one observable value, one reactive label — bootstrapped from declarative specs:

```python
import pygame
from pygame import Rect
from gui_do import (
    Feature, FeatureSpec, HostApplicationBindingSpec, LabelControl,
    ButtonControl, ObservableValue, SceneBundleBindingSpec,
    build_host_application_config, bootstrap_host_application,
)
class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self._count = ObservableValue(0)
        self._sub = None

    def build(self, host) -> None:
        self._label = host.app.add(LabelControl("lbl", Rect(24, 24, 260, 32), "Count: 0"), scene_name="main")
        host.app.add(ButtonControl("btn", Rect(24, 68, 120, 32), "+1", on_click=self._increment), scene_name="main")

    def bind_runtime(self, host) -> None:
        self._sub = self._count.subscribe(lambda v: setattr(self._label, "text", f"Count: {v}"))

    def shutdown_runtime(self, host) -> None:
        if self._sub:
            self._sub()
            self._sub = None

    def _increment(self) -> None:
        self._count.value += 1

class Host: pass
config = build_host_application_config(HostApplicationBindingSpec(
    display_size=(640, 200), window_title="Quick Look",
    fonts={"default": {"size": 14}}, initial_scene_name="main",
    scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),),
    feature_entries=(FeatureSpec(attr_name="counter_feature", factory=CounterFeature),),
))
if __name__ == "__main__":
    pygame.init()
    host = Host()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=60)
```

`bootstrap_host_application` reads the config, initializes all systems, and populates `host` with attributes (`host.app`, `host.screen_rect`, one attribute per `FeatureSpec.attr_name`). `run_entrypoint` starts the frame loop. Pressing Escape exits (because `bind_escape_to_exit=True`).

For a full explanation of every step above, see [TUTORIAL.md](TUTORIAL.md). For the complete API reference, see [MANUAL.md](MANUAL.md).

---

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial — start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

**TUTORIAL.md** teaches the framework by building a complete two-feature application from scratch, explaining both how and why at every step. A reader who finishes the tutorial understands the gui_do programming model well enough to build their own feature-complete application.

**MANUAL.md** is the comprehensive reference organized by system, with API tables, usage patterns, minimal examples, advanced patterns, integration recipes, and appendices. It covers all 32 API tiers and every major subsystem in depth.

---

## Installation

```
python -m pip install -e . --no-deps
```

Run from the repository root. The `--no-deps` flag skips resolving binary package dependencies that you may already have installed.

Requires `pygame` and `numpy`. numpy is used internally for pixel buffer operations via `PixelArray`.

---

## Project Structure

```
gui_do/           Library source — 32 API tiers, all exports through __init__.py
demo_features/    Runnable reference patterns, organized as folder-per-feature packages
tests/            Contract and behavioral tests covering every major system
docs/             Architecture boundary and runtime operating contracts
TUTORIAL.md       Step-by-step tutorial (start here)
MANUAL.md         Complete developer reference
```

`demo_features/` follows the canonical folder-per-feature pattern: each subfolder is one feature package, `__init__.py` is the sole public surface, and internal files are organized by concern (`*_feature.py`, `*_specs.py`, `*_presenter.py`). Reading any demo feature package alongside the tutorial and manual is the fastest way to see gui_do patterns in production-quality code.

---

## See Also

- [TUTORIAL.md](TUTORIAL.md) — step-by-step guide; builds a complete project from scratch
- [MANUAL.md](MANUAL.md) — complete system reference with API tables and integration recipes
- [`demo_features/`](demo_features/) — living reference patterns for every major gui_do subsystem
- [`docs/`](docs/) — architecture boundary specs and runtime operating contracts
- [`gui_do/__init__.py`](gui_do/__init__.py) — authoritative public API; all 32 tiers listed with comments
