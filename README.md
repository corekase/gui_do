[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=m_zNl7tcQlQ"><img src="https://img.youtube.com/vi/m_zNl7tcQlQ/0.jpg" alt="Demo Video"></img></a>

---

## Overview

gui_do is an architecture-first pygame GUI framework designed for deterministic behavior, scene isolation, and feature-level composition. It is built for teams that want explicit runtime contracts, stable public APIs, and a clear path from small prototypes to larger multi-scene applications.

This repository ships with a layered public API at the package root, a complete demo composed under demo_features, and contract-driven docs/tests that keep behavior and docs aligned.

## Strengths

- Data-driven bootstrap: declare scenes, features, actions, windows, and palette behavior with specs.
- Strong runtime contracts: deterministic event ordering, explicit optional facilities, and scheduler budget bounds.
- Clear lifecycle boundaries: features own runtime wiring and teardown.
- Broad systems coverage from one surface: controls, overlays, layout, animation, persistence, telemetry, forms, and dataflow.
- Practical reference assets: MANUAL.md, architecture docs, and a full demo package layout.

## Use Cases

- Desktop control surfaces where predictable input routing and scene switching matter.
- Tooling dashboards that combine windows, command palettes, and task-panel workflows.
- Data-heavy editors that benefit from explicit state, observables, and runtime policies.
- Learning projects that want a single framework covering controls, overlays, scheduling, and persistence.

## Quick Look

Minimal runnable bootstrap using verified root imports:

```python
from gui_do import (
    ActionBindingSpec,
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    RuntimeSceneSpec,
    SceneSetupSpec,
    bootstrap_host_application,
    build_host_application_config,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.ticks = 0

    def on_update(self, host) -> None:
        self.ticks += 1


class QuickStartHost:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1280, 720),
                window_title="gui_do quick look",
                fonts={"default": None},
                initial_scene_name="main",
                scene_entries=(
                    SceneSetupSpec(name="main", pretty_name="Main", make_initial=True),
                ),
                runtime_scene_entries=(
                    RuntimeSceneSpec(scene_name="main"),
                ),
                feature_entries=(
                    FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
                ),
                action_entries=(
                    ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
                ),
                target_fps=60,
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    QuickStartHost().app.run_entrypoint(target_fps=60)
```

For a complete build path, follow TUTORIAL.md and use MANUAL.md for deep system details.

## Documentation

Start here based on your goal:

| Goal | Document |
| --- | --- |
| Build your first complete app step by step | [TUTORIAL.md](TUTORIAL.md) |
| Deep reference for runtime systems, architecture, and specs | [MANUAL.md](MANUAL.md) |
| Runtime guarantees and operating contracts | [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md) |
| Architectural boundaries and package contracts | [docs/architecture.md](docs/architecture.md) |

Suggested path:

1. Read [TUTORIAL.md](TUTORIAL.md) end to end.
2. Jump into [MANUAL.md](MANUAL.md#main-systems-reference) when you need subsystem-level depth.
3. Validate runtime assumptions against [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md).

## Installation

This project uses editable installation with no dependency auto-install:

```bash
python -m pip install -e . --no-deps
```

Because --no-deps skips dependency installation, install runtime dependencies manually:

- pygame>=2.0
- numpy>=1.24

If you also want CI/test tooling locally, these are discovered in repository dependency files:

- coverage

Manual dependency installation is intentional here because building binary dependencies can be problematic on Windows, and explicit installation gives you tighter control over versions and wheel/source behavior.

## Project Structure

Top-level layout at a glance:

- gui_do/: framework source and public root exports.
- demo_features/: demo composition packages (main, life, mandelbrot, moving_shapes, showcase, systems) plus shared demo data/config.
- docs/: architecture, contracts, and specification references.
- tests/: contract and behavior coverage across runtime systems.
- gui_do_demo.py: demo entrypoint using declarative bootstrap config.

demo_features follows a package-per-feature convention with package-root __init__.py as each feature package's public surface, and internal concerns split across focused modules.

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [MANUAL.md: Main Systems Reference](MANUAL.md#main-systems-reference)
- [MANUAL.md: Feature Organization Conventions](MANUAL.md#feature-organization-conventions)
- [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md)
