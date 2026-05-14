[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=LYfCgm7G95E"><img src="https://img.youtube.com/vi/LYfCgm7G95E/0.jpg" alt="Demo Video"></img></a>

---

## Overview

gui_do is a Python GUI framework built on pygame for scene-based desktop applications that need structure, not ad hoc callback sprawl. Its central model combines declarative specs with feature lifecycle methods and reactive state primitives, so you describe topology once and let bootstrap wiring do the heavy lifting. It automates event routing, overlay dispatch, focus behavior, scene transitions, and lifecycle sequencing so feature code can stay domain-focused. The framework is aimed at Python developers building internal tools, game UIs, simulations, and rich interactive desktop apps. Start with TUTORIAL.md for a build-from-scratch path and use MANUAL.md for complete system-level reference.

## Strengths

- Declarative runtime wiring: specs describe intent while bootstrap helpers assemble runtime wiring and lifecycle ownership; see MANUAL.md (8.1).
- Feature lifecycle isolation: each feature owns build, bind, update, draw, and teardown boundaries for predictable maintenance; see MANUAL.md (8.2).
- Reactive state: ObservableValue, ObservableList, and ObservableDict remove polling loops and push UI updates through subscriptions; see MANUAL.md (8.4).
- Composable overlays: dialogs, toasts, tooltips, command surfaces, and shortcut overlays share consistent dispatch paths; see MANUAL.md (8.8).
- Tiered API surface: 32 exported tiers let teams stay high-level first and drop lower only when needed; see MANUAL.md Appendix D.
- Scene management: multi-scene applications use declarative scene bundles and transition policies; see MANUAL.md (8.1, 8.9, 8.10).
- Persistence and migration: workspace snapshots and migration helpers support forward evolution of saved state; see MANUAL.md (8.11, 13).
- Accessibility and focus: semantic accessibility tree, focus routing, and announcements are first-class runtime systems; see MANUAL.md (8.7).
- Built-in diagnostics: telemetry, introspection models, and event tooling support operational debugging; see MANUAL.md (8.16).
- Extensible lifecycle architecture: new behavior is added through feature methods and runtime specs, not framework forks; see MANUAL.md (6, 7, 9).

## Use Cases

gui_do fits a broad range of production-style interactive software. It works well for developer tools and internal utilities such as inspectors, dashboards, and data explorers where deterministic input routing and scene composition matter. It is also suited to game-facing UI and HUD workflows that need 2D rendering systems, scene graph facilities, animation timing, and audio cues. For simulation and data-heavy apps, reactive state plus collection controls and dirty-region rendering support responsive visual feedback while keeping update costs bounded. Teams building workbench-style apps can combine scene models, overlays, and window/task-panel patterns for multi-surface workflows. For deeper system choices across these use cases, use MANUAL.md system chapters 8.1 through 8.16.

## Quick Look

```python
from gui_do import (
    ButtonControl,
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    SceneBundleBindingSpec,
    SceneTransitionStyle,
    bootstrap_host_application,
    build_host_application_config,
)
class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._sub = None
    def build(self, host):
        self._label = LabelControl("count_label", (32, 32, 260, 32), "Count: 0")
        host.main_root.add(self._label)
        host.main_root.add(ButtonControl("inc_button", (32, 72, 160, 34), "Increment", on_click=self._increment))
    def bind_runtime(self, host):
        self._sub = self._count.subscribe(lambda value: setattr(self._label, "text", f"Count: {value}"))
    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None
    def _increment(self):
        self._count.value += 1
class QuickLookHost:
    def __init__(self):
        config = build_host_application_config(HostApplicationBindingSpec(display_size=(900, 560), window_title="gui_do quick look", fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}}, initial_scene_name="main", scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", transition_style=SceneTransitionStyle.FADE, make_initial=True, emit_scene_root_spec=True, scene_root_id="main_root"),), feature_entries=(FeatureSpec("counter_feature", CounterFeature),)))
        bootstrap_host_application(self, config)
host = QuickLookHost()
host.app.run_entrypoint(target_fps=60)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial - start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

TUTORIAL.md teaches the framework by building one complete project from scratch with reasoning at each step, while MANUAL.md is the full reference surface organized by system chapter with API details, usage patterns, integration recipes, and appendices.

## Installation

Install locally from repository root:

```bash
python -m pip install -e . --no-deps
```

gui_do requires pygame and numpy.

## Project Structure

- gui_do/: framework library with the public root API and tiered subsystems.
- demo_features/: runnable reference patterns organized as one folder per feature package, with each package __init__.py as the only public cross-package import surface.
- tests/: contract, behavior, and integration tests across systems.
- docs/: architecture boundaries and runtime operating contracts.
- TUTORIAL.md: build-first learning path.
- MANUAL.md: complete theory and API reference.

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features/)
- [docs/](docs/)
- [gui_do/__init__.py](gui_do/__init__.py)
