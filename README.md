[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=LYfCgm7G95E"><img src="https://img.youtube.com/vi/LYfCgm7G95E/0.jpg" alt="Demo Video"></img></a>

---

## Overview

gui_do is a Python GUI framework built on pygame for teams that want a structured, testable way to build desktop interfaces. Its core model combines declarative specs for runtime composition, feature lifecycle hooks for predictable ownership, and reactive observables for automatic UI updates. Instead of hand-wiring every registry and manager, gui_do automates recurring infrastructure such as event routing, overlay dispatch, focus management, scene transitions, and lifecycle sequencing. The result is a framework that fits desktop tools, game UIs, simulations, and interactive applications while staying understandable as projects scale. If you are new, continue to TUTORIAL.md; if you need system-level reference detail, use MANUAL.md.

## Strengths

- Declarative runtime wiring: specs define what exists, and bootstrap assembles the runtime graph consistently.
- Feature lifecycle isolation: each feature owns build, bind_runtime, on_update, draw, and teardown responsibilities.
- Reactive state: ObservableValue, ObservableList, and ObservableDict push updates directly to subscribers.
- Composable overlays: dialogs, toasts, tooltips, command palette, and context menus share consistent routing behavior.
- Tiered API surface: the root package exports 32 tiers from high-level bootstrap entry points to low-level runtime systems.
- Scene management: scene-scoped features and transitions support multi-scene apps with clear boundaries.
- Persistence and migration: versioned workspace snapshots support save/restore workflows with migration paths.
- Accessibility and focus: semantic accessibility metadata, focus infrastructure, and live-region support are built in.
- Built-in diagnostics: telemetry, event capture/playback, and runtime inspection facilities are available out of the box.
- Extensible without framework edits: new behavior is introduced by adding features and specs, not patching core internals.

## Use Cases

gui_do fits a broad range of interactive software. It works well for developer tools and internal utilities such as dashboards, inspectors, and data explorers. It supports game-facing UI and HUD workloads with 2D graphics systems, scene orchestration, and audio cues. It is also a good match for interactive simulations and visualization tools where reactive controls and efficient rendering matter. For larger workspace-style applications, scene/window/task-panel composition supports multi-window flows. For early-stage products, constraint and flex layout systems help teams prototype quickly and evolve incrementally.

## Quick Look

```python
from types import SimpleNamespace
from pygame import Rect

from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)

    def build(self, host) -> None:
        self._label = host.main_root.add(LabelControl("counter_label", Rect(24, 24, 260, 36), "Count: 0"))

    def bind_runtime(self, host) -> None:
        self._unsubscribe = self._count.subscribe(lambda value: setattr(self._label, "text", f"Count: {value}"))

binding = HostApplicationBindingSpec(
    display_size=(800, 480),
    window_title="Quick Look",
    fonts={"default": {"file": None, "size": 16}},
    initial_scene_name="main",
    scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True, emit_scene_root_spec=True),),
    feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
)
host = SimpleNamespace()
config = build_host_application_config(binding)
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial — start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

TUTORIAL.md teaches gui_do by building a complete project from scratch and explaining both how and why each step exists. MANUAL.md is the full reference organized by system, with API tables, usage patterns, examples, integration recipes, and appendices.

## Installation

Install from the repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies: pygame and numpy.

## Project Structure

- gui_do/: framework library and root public API surface.
- demo_features/: runnable reference patterns using the folder-per-feature package layout.
- tests/: behavior and contract tests that validate runtime guarantees and API consistency.
- docs/: architecture and runtime contract specifications.
- TUTORIAL.md: step-by-step onboarding path.
- MANUAL.md: full system reference.

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features)
- [docs/](docs)
- [gui_do/__init__.py](gui_do/__init__.py)
