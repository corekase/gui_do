[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=LYfCgm7G95E"><img src="https://img.youtube.com/vi/LYfCgm7G95E/0.jpg" alt="Demo Video"></img></a>

---

## Project Header

gui_do is a Python GUI framework built on pygame for data-driven, desktop-style applications. You describe scenes, features, actions, and runtime behavior declaratively with specs, then let bootstrap assemble and wire the runtime. The framework centers on feature lifecycle methods and reactive state so UI updates flow from state changes instead of polling loops. It automates event routing, overlay dispatch, focus management, scene transitions, and lifecycle sequencing so application features can stay focused on domain behavior. gui_do is a strong fit for Python developers building internal tools, game UIs, simulations, and other interactive desktop applications.

## Strengths

- Declarative runtime wiring: specs describe what your app contains, and bootstrap builds and wires the runtime consistently.
- Feature lifecycle isolation: each feature owns build, bind, update, draw, and shutdown responsibilities with clear boundaries.
- Reactive state: `ObservableValue`, `ObservableList`, and `ObservableDict` let UI react to data changes without polling.
- Composable overlays: dialogs, toasts, tooltips, command palette, and context menus share consistent routing behavior.
- Tiered API surface: 32 public tiers let teams start high-level and drop lower only when they need more control.
- Scene management: multi-scene applications can switch with transitions and keep scene-scoped routing deterministic.
- Persistence and migration: workspace state can be saved, restored, and evolved through versioned snapshot migration.
- Accessibility and focus: semantic accessibility metadata, focus rings, and live-region patterns are built into runtime flow.
- Built-in diagnostics: telemetry spans, event recording/playback, and runtime inspection hooks support operational debugging.
- Extensible architecture: new features compose behavior by implementing lifecycle methods rather than changing framework internals.

## Use Cases

gui_do works well for developer tools and internal utilities such as inspectors, dashboards, and data explorers. It also supports game-facing interfaces and HUD workflows with scene graph, tile map, particle, and audio facilities. For interactive simulations, reactive state and deterministic updates make parameter explorers and visual experiments straightforward to structure. Data-heavy tools benefit from collection controls, filtering/sorting pipelines, and dirty-region-aware rendering. Multi-window workbench apps can combine scene navigation with panel and window presentation systems, and rapid layout iteration is supported by constraint and flex/grid layout options.

## Quick Look

```python
import pygame
from pygame import Rect

from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    PanelControl,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)

    def build(self, host) -> None:
        host.root = host.app.add(PanelControl("root", host.screen_rect.copy(), draw_background=False), scene_name="main")
        self.label = host.root.add(LabelControl("count_label", Rect(24, 24, 280, 40), "Count: 0"))

    def bind_runtime(self, host) -> None:
        self.unsubscribe = self.count.subscribe(lambda value: setattr(self.label, "text", f"Count: {value}"))

class AppHost:
    def __init__(self) -> None:
        config = build_host_application_config(HostApplicationBindingSpec(
            display_size=(960, 540),
            window_title="Quick Look",
            fonts={"default": {"file": None, "size": 16}},
            initial_scene_name="main",
            scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
            feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
        ))
        bootstrap_host_application(self, config)

AppHost().app.run_entrypoint(target_fps=60)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial - start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

[TUTORIAL.md](TUTORIAL.md) teaches gui_do by building a full project from scratch, with continuous explanation of both how and why each step works. [MANUAL.md](MANUAL.md) is the deep reference organized by system, with API tables, patterns, examples, integration recipes, and appendices for long-term maintenance.

## Installation

Install from the repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies: pygame and numpy.

## Project Structure

- `gui_do/`: framework library code and the authoritative public root API.
- `demo_features/`: runnable reference patterns using the folder-per-feature package model with each feature package `__init__.py` as its public import surface.
- `tests/`: behavioral, contract, and integration tests.
- `docs/`: architecture boundaries and runtime operating contracts.
- `TUTORIAL.md`: full learning path that builds a complete application.
- `MANUAL.md`: comprehensive system and API reference.

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features)
- [docs/](docs)
- [gui_do/__init__.py](gui_do/__init__.py)
