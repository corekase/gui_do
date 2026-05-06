[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=OVj54_BhDO4"><img src="https://img.youtube.com/vi/OVj54_BhDO4/0.jpg" alt="Demo Video"></img></a>

---

gui_do is a Python GUI framework built on pygame for teams that want predictable runtime behavior without hand-wiring every subsystem. You describe scenes, features, actions, windows, and overlays with declarative specs, then bootstrap once and let the runtime connect lifecycle sequencing, routing, and presentation models. Reactive state primitives keep UI updates explicit and low-friction, while feature lifecycles keep responsibilities isolated and testable. The framework automates event routing, overlay dispatch, focus paths, scene transitions, and runtime startup/teardown plumbing. It is well suited to Python developers building desktop tools, game UIs, simulations, and other interactive applications.

## Strengths

- Declarative runtime wiring: You declare what the application contains with specs, and bootstrap builds the concrete runtime graph.
- Feature lifecycle isolation: Each feature owns build, runtime binding, update, draw, and shutdown responsibilities in one place.
- Reactive state: ObservableValue, ObservableList, and ObservableDict propagate changes directly to consumers without polling loops.
- Composable overlays: Dialogs, toasts, tooltips, command palette, and context menus share consistent routing expectations.
- Tiered public API surface: The root import is organized into 32 tiers from bootstrap helpers through graphics and persistence facilities.
- Scene management: Multi-scene applications support transitions, scene-scoped behavior, and clean navigation actions.
- Persistence and migration: Workspace state capture/restore and snapshot migration provide controlled upgrade paths.
- Accessibility and focus: Semantic accessibility structures and focus routing are first-class runtime concerns.
- Built-in diagnostics: Telemetry, event tools, and inspection utilities make runtime behavior easier to observe and debug.
- Extensible architecture: New behavior is added by composing features and specs rather than patching framework internals.

## Use Cases

gui_do works well for internal developer tools such as inspectors, dashboards, and utility workbenches where deterministic behavior and fast iteration matter. It also maps naturally to game-adjacent interfaces, including HUDs, scene overlays, and interactive simulation controls, because rendering, input, and scene orchestration live in one coherent runtime. For data-centric applications, the framework supports responsive controls, structured state, and predictable update loops that help keep larger UI surfaces maintainable. For rapid exploration, its layout and scene abstractions let you prototype application flows quickly while still using production-grade lifecycle boundaries.

## Quick Look

```python
from pygame import Rect

from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)

    def build(self, host) -> None:
        self.label = host.app.add(LabelControl("count_label", Rect(20, 20, 320, 40), "Count: 0"), scene_name="main")

    def bind_runtime(self, host) -> None:
        self.unsubscribe = self.count.subscribe(lambda value: setattr(self.label, "text", f"Count: {value}"))

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(800, 480),
        window_title="Quick Look",
        fonts={"default": {"system": "arial", "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)

host = type("Host", (), {})()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial - start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

TUTORIAL.md walks through building a complete application from scratch and explains both the mechanics and design rationale at each step. MANUAL.md is the deep reference organized by system, with API inventories, integration patterns, operational guidance, and appendices.

## Installation

Install from the repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies: pygame and numpy.

## Project Structure

- gui_do/: The library and public API surface.
- demo_features/: Runnable reference feature and scene package patterns.
- tests/: Contract and behavior coverage for runtime systems and boundaries.
- docs/: Architecture boundary and runtime operating contracts.
- TUTORIAL.md: End-to-end learning path.
- MANUAL.md: Full system reference.

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features)
- [docs/](docs)
- [gui_do/__init__.py](gui_do/__init__.py)
