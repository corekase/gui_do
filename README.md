[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=m_zNl7tcQlQ"><img src="https://img.youtube.com/vi/m_zNl7tcQlQ/0.jpg" alt="Demo Video"></img></a>

---

## Overview

`gui_do` is an architecture-first GUI framework built on pygame, designed for teams that care about deterministic runtime behavior, clear ownership, and testable composition.

The project favors declarative setup and explicit runtime wiring over hidden side effects. The public root API is intentionally broad so application code can stay on stable imports while internals evolve.

If you are evaluating where to start:

- Start with [TUTORIAL.md](TUTORIAL.md) for a complete, build-it-yourself path.
- Use [MANUAL.md](MANUAL.md) for deep system contracts and full reference detail.

## Strengths

- Declarative host bootstrap via `HostApplicationBindingSpec`, `build_host_application_config`, and `bootstrap_host_application`.
- Feature lifecycle model with clear hooks for registration, runtime binding, update, draw, and teardown.
- Multiple feature styles (`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`) so you can separate rendering, orchestration, and domain logic.
- Built-in facilities for actions, keyboard mappings, state, overlays, scheduling, persistence, telemetry, accessibility, and theme management.
- Runtime contracts documented in [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md), including determinism and bounded scheduler policies.

## Use Cases

`gui_do` is a strong fit when you need:

- A desktop-like, multi-scene pygame application with explicit window/panel behavior.
- Feature package boundaries with predictable runtime ownership and teardown.
- Data-driven bootstrapping for demos, internal tools, simulations, or operator consoles.
- A framework that scales from a single feature to many feature packages without abandoning root-level API imports.

Representative in-repo usage:

- `gui_do_demo.py` bootstraps from `demo_features/demo_config.py`.
- `demo_features/` packages show feature-per-folder organization and package-root export surfaces.

## Quick Look

The minimal in-repo launch pattern is:

```python
from gui_do import bootstrap_host_application
from demo_features.demo_config import DEMO_BOOTSTRAP_CONFIG


class GuiDoDemo:
    def __init__(self) -> None:
        bootstrap_host_application(self, DEMO_BOOTSTRAP_CONFIG)


if __name__ == "__main__":
    GuiDoDemo().app.run_entrypoint(target_fps=DEMO_BOOTSTRAP_CONFIG.target_fps)
```

Why this pattern is useful:

- You can keep app entrypoints tiny.
- Bootstrap remains declarative and centrally editable in one config object.
- Runtime facilities are created only when declared in specs.

For the full step-by-step build path, continue to [TUTORIAL.md](TUTORIAL.md).

## Documentation

Use this navigation table to choose the right depth quickly.

| Document | Purpose | When to use it |
| --- | --- | --- |
| [TUTORIAL.md](TUTORIAL.md) | End-to-end guided build | First-time adoption, team onboarding, implementation walkthrough |
| [MANUAL.md](MANUAL.md) | Authoritative systems and API reference | Deep runtime details, lifecycle contracts, advanced integration |
| [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md) | Behavioral guarantees and safety rails | Determinism checks, cross-system behavior expectations |
| [docs/demo_feature_layout.md](docs/demo_feature_layout.md) | Demo package organization contract | Structuring feature folders and package-root exports |
| [docs/public_api_spec.md](docs/public_api_spec.md) | Public API policy and import guidance | Root API stability and import discipline |

## Installation

`gui_do` currently targets Python 3.11+.

Use editable install without dependency resolution:

```bash
python -m pip install -e . --no-deps
```

Because `--no-deps` skips all dependency installation, install required packages manually.

Runtime dependencies (from `pyproject.toml`):

- `pygame>=2.0`
- `numpy>=1.24`

Typical manual install command:

```bash
python -m pip install "pygame>=2.0" "numpy>=1.24"
```

Optional test/CI tools discovered in repository dependency files:

- `coverage`
- `pytest`

Optional install command:

```bash
python -m pip install coverage pytest
```

Manual dependency installation is intentional here because building binary dependencies can be problematic on Windows; explicitly controlling package installs usually gives clearer failure modes and easier recovery.

## Project Structure

Top-level structure follows a framework/runtime plus consumer-demo split:

- `gui_do/`: framework runtime and public API surface (root exports and tiered systems).
- `demo_features/`: consumer-side feature packages and demo bootstrap config.
- `docs/`: architecture, contracts, and system/reference specifications.
- `tests/`: behavior contracts, API parity checks, and runtime regression coverage.
- `gui_do_demo.py`: demo application entrypoint.

`demo_features/` conventions in this repository:

- One folder per feature package (for example: `life/`, `mandelbrot/`, `moving_shapes/`, `showcase/`, `systems/`).
- Package-root `__init__.py` acts as the public import surface for each feature package.
- Root `demo_features/` stays focused on bootstrap and shared assets (`demo_config.py`, `data/`).

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/library_demo_separation_contract.md](docs/library_demo_separation_contract.md)
