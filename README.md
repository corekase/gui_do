[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=OVj54_BhDO4"><img src="https://img.youtube.com/vi/OVj54_BhDO4/0.jpg" alt="Demo Video"></img></a>

---

gui_do is a Python GUI framework built on pygame for building structured desktop applications with a predictable runtime model. It combines declarative application specs with feature lifecycle classes so you describe structure once and let bootstrap handle wiring. It also gives you reactive state primitives so UI updates happen from data changes rather than manual polling loops. The runtime automates high-friction plumbing such as event routing, overlay dispatch, focus management, scene transitions, and lifecycle sequencing. It is designed for Python developers building internal tools, game UI layers, simulations, and interactive application workflows.

## Strengths

- Declarative runtime wiring: specs declare what the app should contain, and bootstrap wires how systems are connected.
- Feature lifecycle isolation: each feature owns build, bind, update, draw, and teardown boundaries to keep code cohesive.
- Reactive state: `ObservableValue`, `ObservableList`, and `ObservableDict` propagate changes without polling.
- Composable overlays: dialogs, toasts, tooltips, command surfaces, and context menus share consistent routing and focus behavior.
- Tiered API surface: a single root API spans 32 tiers from high-level bootstrap to lower-level graphics, state, and runtime systems.
- Scene management: multi-scene applications support transitions and scene-scoped routing with deterministic behavior.
- Persistence and migration: workspace capture/restore flows support snapshot migration and structured restore reporting.
- Accessibility and focus: semantic accessibility trees, focus rings, and live announcement channels are first-class runtime features.
- Built-in diagnostics: telemetry spans, introspection utilities, and runtime diagnostics improve confidence during development.
- Extensible by lifecycle composition: new behavior is added by implementing feature lifecycle methods and specs, not by editing framework internals.

For guided onboarding, continue in [TUTORIAL.md](TUTORIAL.md). For full reference depth, use [MANUAL.md](MANUAL.md).

## Use Cases

gui_do is suited for a wide range of Python GUI workloads. It works well for developer tools and internal utilities such as inspectors, dashboards, and data explorers where structured state and action routing matter. It also fits game interfaces and HUD workflows that benefit from scene transitions, overlays, 2D rendering support, and audio cues. For interactive simulations and parameter exploration tools, reactive state and lifecycle partitioning keep updates predictable. Data-oriented tools can combine list/grid controls with dirty-region rendering patterns for responsive interfaces. Multi-window workbench layouts, tabbed panels, and rapid layout prototyping are supported through window, scene, and layout systems.

The fastest way to learn these patterns end-to-end is [TUTORIAL.md](TUTORIAL.md), then [MANUAL.md](MANUAL.md) for system-level detail.

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


class HelloFeature(Feature):
    def __init__(self) -> None:
        super().__init__("hello_feature", scene_name="main")
        self.counter = ObservableValue(0)

    def build(self, host) -> None:
        self.label = host.app.add(LabelControl("hello_label", Rect(24, 24, 320, 40), "Count: 0"), scene_name="main")

    def bind_runtime(self, host) -> None:
        self._sub = self.counter.subscribe(lambda v: setattr(self.label, "text", f"Count: {v}"))


class QuickStartApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(800, 480),
                window_title="gui_do Quick Look",
                fonts={"default": "arial"},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(FeatureSpec("hello_feature", HelloFeature),),
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    host = QuickStartApp()
    host.app.run_entrypoint(target_fps=60)
```

Build the complete project tutorial next in [TUTORIAL.md](TUTORIAL.md), then use [MANUAL.md](MANUAL.md) as your detailed systems reference.

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial - start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

[TUTORIAL.md](TUTORIAL.md) teaches gui_do by building a complete project from scratch, explaining both how and why in each stage. [MANUAL.md](MANUAL.md) is the comprehensive reference organized by system with API tables, usage patterns, integration recipes, and appendices.

## Installation

From the repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies: `pygame` and `numpy`.

## Project Structure

- `gui_do/`: framework library code and authoritative root API exports.
- `demo_features/`: runnable feature packages that model the folder-per-feature and package-root-public-surface pattern.
- `tests/`: contract and behavioral tests for runtime, API, and documentation alignment.
- `docs/`: architecture boundaries, runtime contracts, and supporting specification docs.
- `TUTORIAL.md`: full project tutorial.
- `MANUAL.md`: full system reference.

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features)
- [docs/](docs)
- [gui_do/__init__.py](gui_do/__init__.py)
