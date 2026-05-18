[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=v1HKccjVcOw"><img src="https://img.youtube.com/vi/v1HKccjVcOw/0.jpg" alt="Demo Video"></img></a>

---

## Overview

gui_do is a Python GUI framework built on pygame, designed around declarative specs, feature lifecycle orchestration, and reactive state primitives. You describe your app with binding specs, and the runtime wires scenes, features, overlays, actions, and supporting systems in a deterministic order. This model automates a large amount of glue code, including event routing, overlay dispatch, focus handling, scene transitions, and lifecycle sequencing. It is a strong fit for Python developers building desktop tools, game-facing interfaces, simulation UIs, and other interactive applications. For guided learning and deeper system details, continue in [TUTORIAL.md](TUTORIAL.md) and [MANUAL.md](MANUAL.md).

## Strengths

- Declarative runtime wiring: You declare `HostApplicationBindingSpec` and related specs; bootstrap builds and binds the runtime graph for you.
- Feature lifecycle isolation: Each feature owns `build`, `bind_runtime`, `handle_event`, `on_update`, `draw`, and `shutdown_runtime` within clear boundaries.
- Reactive state primitives: `ObservableValue`, `ObservableList`, and `ObservableDict` update UI behavior from state change notifications rather than polling loops.
- Composable overlays and command surfaces: Dialogs, toasts, tooltips, command palettes, and context menus share consistent routing through overlay managers.
- Tiered public API: A 32-tier root export surface spans high-level bootstrap helpers down to graphics, forms, dataflow, and migration facilities.
- Scene and presentation management: Multi-scene flows, transition styles, scene roots, and window/task-panel presentation models are built in.
- Persistence and migration: Workspace snapshots, restore reporting, and migration helpers support durable application state evolution.
- Accessibility and focus systems: Focus scopes/rings, accessibility nodes/roles, and live announcements are available as first-class facilities.
- Runtime diagnostics: Telemetry capture/analysis, event recording/playback, debug overlays, and property inspection are part of the framework.
- Advanced routed runtime faculties: Policy, effects, pipelines, durable queues, capability contracts, projections, workflows, recompute, QoS, health, replay, and hot-swap are declaratively attachable through `RoutedRuntimeSpec`.

For theory and full API coverage of each system, use [MANUAL.md](MANUAL.md).

## Use Cases

gui_do supports a wide range of application classes without changing programming model:

- Developer tools and internal utilities: Build inspectors, dashboards, and operational consoles with strong runtime diagnostics and persistence.
- Game interfaces and HUDs: Combine controls, overlays, scene graphs, particles, tile maps, and audio cues in one runtime.
- Interactive simulations: Implement parameter explorers and visual experiments with reactive controls plus deterministic update cadence.
- Data visualization tools: Pair collection views, grids, validation pipelines, and dirty-region graphics for high-information interfaces.
- Multi-window workbench apps: Use window/task-panel presentation specs to manage dense tool surfaces and discoverable command routes.
- Rapid layout prototyping: Move quickly with constraint, flex, grid, flow, and adaptive layout systems while preserving lifecycle rigor.

For implementation walkthroughs, start in [TUTORIAL.md](TUTORIAL.md). For deeper architecture and contracts, use [MANUAL.md](MANUAL.md).

## Quick Look

```python
from pygame import Rect
from gui_do import (
    ActionSpec,
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
        self.count_value = ObservableValue(0)
        self.count_label = None
        self.count_subscription = None

    def build(self, host) -> None:
        root = host.app.add(PanelControl("main_root", Rect(0, 0, host.screen_rect.width, host.screen_rect.height)), scene_name="main")
        self.count_label = root.add(LabelControl("count_label", Rect(24, 24, 260, 32), "Count: 0"))

    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(lambda value: setattr(self.count_label, "text", f"Count: {value}"))

class DemoHost:
    pass

config = build_host_application_config(HostApplicationBindingSpec(
    display_size=(960, 540), window_title="Quick Look", fonts={"default": "arial"}, initial_scene_name="main",
    scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
    feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    action_entries=(ActionSpec(action_id="exit", label="Exit", kind="exit"),),
))
host = DemoHost()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=config.target_fps)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial — start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

[TUTORIAL.md](TUTORIAL.md) teaches the framework by building a complete project from scratch and explains both how and why at each stage. [MANUAL.md](MANUAL.md) is the comprehensive reference organized by system chapter, with API-oriented detail, integration patterns, and contract-aligned explanations.

## Installation

Install from repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies: `pygame` and `numpy`.

## Project Structure

- `gui_do/`: Core library package and public API surface.
- `demo_features/`: Runnable feature/scene package patterns that model recommended organization.
- `tests/`: Contract and behavioral tests for runtime guarantees.
- `docs/`: Architecture and operating contract documents.
- `TUTORIAL.md`: Guided learning path with end-to-end examples.
- `MANUAL.md`: Full reference and system-level documentation.

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features)
- [docs/](docs)
- [gui_do/__init__.py](gui_do/__init__.py)
