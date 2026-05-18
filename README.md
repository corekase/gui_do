[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=v1HKccjVcOw"><img src="https://img.youtube.com/vi/v1HKccjVcOw/0.jpg" alt="Demo Video"></img></a>

---

## Overview

gui_do is a Python GUI framework built on pygame for data-driven desktop and interactive applications. You describe application structure with declarative specs, then implement feature behavior with lifecycle methods that stay local and testable. The runtime automates event routing, overlay dispatch, focus management, scene transitions, and lifecycle sequencing so application code can focus on product behavior. The result is a practical architecture for Python developers building internal tools, game UIs, simulations, and other interactive apps. For deep system details, see MANUAL.md, and for a build-from-scratch walkthrough, see TUTORIAL.md.

## Strengths

- Declarative runtime wiring: specs describe intent, and bootstrap builds and wires runtime systems consistently.
- Feature lifecycle isolation: each feature owns build, bind, event handling, update, draw, and teardown.
- Reactive state: ObservableValue, ObservableList, and ObservableDict update UI without polling loops.
- Composable overlays: dialogs, toasts, tooltips, command surfaces, and shortcut help route through shared managers.
- Tiered API surface: the root package exposes 32 tiers from bootstrap APIs through rendering and persistence.
- Scene management: scene bundles, transition management, and scene-scoped routing support multi-scene workflows.
- Persistence and migration: workspace snapshots and migration APIs support long-lived application state.
- Accessibility and focus: accessibility tree, live regions, and focus systems are built into runtime composition.
- Built-in diagnostics: telemetry, event recording/playback, and introspection APIs support debugging and profiling.
- Extensible composition: new behavior is added with feature implementations and specs, not framework rewrites.

For architecture depth and system contracts, see MANUAL.md and docs/runtime_operating_contracts.md. For a practical end-to-end build, see TUTORIAL.md.

## Use Cases

gui_do is well suited for internal developer tools such as inspectors, diagnostics dashboards, and data explorers where deterministic runtime behavior and fast iteration matter. It also supports game-facing UI and HUD workflows through scene management, controls, graphics, and audio integration points. For simulation and exploratory tools, reactive state plus scheduling and layout systems keep interfaces responsive while logic evolves. The same model works for data visualization utilities, multi-window workbench-style apps, and rapid layout prototyping using constraint, grid, and flex systems. See TUTORIAL.md for a concrete project path, then use MANUAL.md for subsystem-level reference.

## Quick Look

```python
from gui_do import Feature, FeatureSpec, HostApplicationBindingSpec, LabelControl, ObservableValue, PanelControl, SceneBundleBindingSpec, build_host_application_config, bootstrap_host_application


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)

    def build(self, host) -> None:
        self._root = PanelControl("counter_root", host.screen_rect, draw_background=True)
        self._label = LabelControl("count_label", (24, 24, 260, 36), f"Count: {self._count.value}")
        self._root.add(self._label)
        host.app.add(self._root, scene_name="main")

    def bind_runtime(self, host) -> None:
        self._sub = self._count.subscribe(lambda value: setattr(self._label, "text", f"Count: {value}"))


class QuickLookHost:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(900, 540),
                window_title="gui_do quick look",
                fonts={"default": {"size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
            )
        )
        bootstrap_host_application(self, config)


QuickLookHost().app.run_entrypoint(target_fps=60)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial - start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

TUTORIAL.md teaches the framework by building a complete project from scratch and explaining both how and why at each step. MANUAL.md is the full systems reference with theory, API-oriented guidance, integration patterns, and appendices.

## Installation

Install locally from repository root:

```bash
python -m pip install -e . --no-deps
```

Runtime dependencies: pygame and numpy.

## Project Structure

- gui_do/: library source and public root API surface.
- demo_features/: runnable reference feature packages following folder-per-feature conventions.
- tests/: behavioral and contract tests for runtime, APIs, and architecture boundaries.
- docs/: architecture and runtime contract specifications.
- TUTORIAL.md: end-to-end learning path.
- MANUAL.md: complete system and API reference.

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features/)
- [docs/](docs/)
- [gui_do/__init__.py](gui_do/__init__.py)
