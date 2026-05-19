[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=JLnkEEAQ43Q"><img src="https://img.youtube.com/vi/JLnkEEAQ43Q/0.jpg" alt="Demo Video"></img></a>

---

## Overview

gui_do is a Python GUI framework built on pygame for desktop tools, game interfaces, simulations, and interactive applications. Its primary model is declarative runtime wiring: you describe scenes, features, actions, and runtime facilities with specs, then bootstrap turns those declarations into a running app. Feature behavior stays imperative through lifecycle methods, while the framework automates event routing, overlay dispatch, focus handling, scene transitions, and runtime sequencing. Reactive state primitives such as ObservableValue, ObservableList, and ObservableDict keep UI updates automatic and explicit. If you want a complete hands-on build path, read [TUTORIAL.md](TUTORIAL.md), and for full system detail use [MANUAL.md](MANUAL.md).

## Strengths

- Declarative runtime wiring: You declare structure with specs and let bootstrap build the runtime graph deterministically.
- Feature lifecycle isolation: Each feature owns build, bind_runtime, handle_event, on_update, draw, and shutdown_runtime boundaries.
- Reactive state: ObservableValue, ObservableList, ObservableDict, and ComputedValue propagate updates without polling loops.
- Composable overlays: Dialogs, toasts, tooltips, command palette, context menus, and shortcut help share consistent routing behavior.
- Tiered public surface: 32 tiers expose a clear path from high-level bootstrap APIs down to graphics, audio, and migration layers.
- Scene management: Scene bundles support transitions, runtime startup policies, per-scene roots, and scene-scoped facilities.
- Persistence and migration: Workspace snapshots and versioned migration utilities support durable state restoration over time.
- Accessibility and focus: Semantic accessibility tree support, focus scopes, focus rings, and live announcements are built in.
- Diagnostics and observability: Telemetry spans, event recording/playback, introspection registries, and inspectors aid debugging.
- Advanced routed runtime faculties: RoutedRuntimeSpec can declaratively wire policy engines, effect lifetime orchestration, event pipelines, durable queues, capability contracts, projections, dependency validation, workflow orchestration, recompute orchestration, QoS policies, health probes, replay harnesses, and hot-swap management.

See [MANUAL.md](MANUAL.md) for architecture and per-system details, and [TUTORIAL.md](TUTORIAL.md) for a complete project walk-through.

## Use Cases

gui_do fits a broad range of Python applications. It is strong for internal developer tools such as dashboards, inspectors, and operational consoles where reactive state and overlays matter. It also supports game-adjacent UI and HUD workflows with graphics, particles, tile maps, scene graph, and audio cues. For interactive simulations and data exploration, it provides stateful controls, virtualization, and scheduling primitives that keep updates predictable. Multi-window workbench layouts, task-panel workflows, and rapid layout prototyping with constraint and flex systems are all first-class patterns. For deeper design rationale and contracts, use [MANUAL.md](MANUAL.md), then use [TUTORIAL.md](TUTORIAL.md) to build your own end-to-end app.

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

class QuickLookFeature(Feature):
    def __init__(self):
        super().__init__("quick_look", scene_name="main")
        self.count = ObservableValue(0)

    def build(self, host):
        root = host.app.add(PanelControl("quick_root", Rect(40, 40, 360, 120), draw_background=True), scene_name="main")
        self.label = root.add(LabelControl("quick_label", Rect(16, 16, 320, 40), "Count: 0"))

    def bind_runtime(self, host):
        self.countSubscription = self.count.subscribe(lambda value: setattr(self.label, "text", f"Count: {value}"))

class Host:
    pass

host = Host()
config = build_host_application_config(HostApplicationBindingSpec(
    display_size=(900, 520),
    window_title="gui_do Quick Look",
    fonts={"default": {"file": None, "size": 16}},
    initial_scene_name="main",
    scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
    feature_entries=(FeatureSpec("quick_feature", QuickLookFeature),),
))
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

For a complete multi-feature app, continue to [TUTORIAL.md](TUTORIAL.md). For full API and systems reference, use [MANUAL.md](MANUAL.md).

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial — start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

TUTORIAL.md teaches gui_do by building one complete project from scratch and explaining both how and why each step exists. MANUAL.md is the comprehensive systems reference with API tables, integration patterns, runtime contracts, and appendices.

## Installation

From the repository root:

```bash
python -m pip install -e . --no-deps
```

Dependency note: gui_do requires pygame and numpy.

## Project Structure

- gui_do/: framework library and all tiered public APIs.
- demo_features/: runnable reference patterns organized as one folder per feature package with package-root import surfaces.
- tests/: contract and behavioral tests for runtime guarantees, systems, and controls.
- docs/: architecture and runtime contract specifications.
- TUTORIAL.md: guided end-to-end learning path.
- MANUAL.md: complete system and API reference.

For deeper details per subsystem, jump into [MANUAL.md](MANUAL.md).

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features)
- [docs/](docs)
- [`gui_do/__init__.py`](gui_do/__init__.py)
