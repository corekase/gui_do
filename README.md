[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=m_zNl7tcQlQ"><img src="https://img.youtube.com/vi/m_zNl7tcQlQ/0.jpg" alt="Demo Video"></img></a>

---

## Overview

`gui_do` is an architecture-first GUI framework built around a tiered public API, declarative runtime assembly, and explicit lifecycle ownership. The repository combines the framework, a runnable demo application, contract docs, and tests that pin down the intended runtime behavior.

If you want the shortest path from “I want to see it run” to “I want to understand how it works,” start with [TUTORIAL.md](TUTORIAL.md) and keep [MANUAL.md](MANUAL.md) open for deeper runtime and API reference material.

## Strengths

The public surface is organized around the root package exports in [gui_do/__init__.py](gui_do/__init__.py), so application code can stay on the supported API instead of reaching into private internals. The runtime also emphasizes scene isolation, deterministic routing, and explicit teardown for subscriptions, tasks, and feature-owned state.

The demo layout mirrors the intended application structure: feature packages live under `demo_features/`, each package owns its own `__init__.py` boundary, and bootstrap wiring stays in `demo_features/demo_config.py` instead of being scattered across feature modules.

## Use Cases

Use `gui_do` when you want a GUI app that is assembled from feature bundles, scene bundles, action declarations, and runtime specs rather than from ad hoc widget wiring.

It fits applications that need scene navigation, window/task-panel chrome, reactive state, command palettes, feature communication, or a strong contract boundary around focus, teardown, and layout decisions.

## Quick Look

Run the repository demo entrypoint to see the framework in action:

```python
from gui_do import bootstrap_host_application

from demo_features.demo_config import DEMO_BOOTSTRAP_CONFIG


class GuiDoDemo:
    """Interactive demo app showcasing gui_do controls and scene workflows."""

    def __init__(self) -> None:
        bootstrap_host_application(self, DEMO_BOOTSTRAP_CONFIG)


if __name__ == "__main__":
    GuiDoDemo().app.run_entrypoint(target_fps=DEMO_BOOTSTRAP_CONFIG.target_fps)
```

Expected result: the host is bootstrapped from the demo config, then the app enters the configured runtime loop at the demo target frame rate.

## Documentation

The project docs are split by intent, not by file count:

| Document | Best for |
| --- | --- |
| [TUTORIAL.md](TUTORIAL.md) | A full learning path that builds up the demo project step by step. |
| [MANUAL.md](MANUAL.md) | Deep system reference, architecture notes, and API selection guidance. |
| [docs/public_api_spec.md](docs/public_api_spec.md) | The supported root import contract and public API rules. |
| [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md) | Runtime guarantees, safety rails, and deterministic behavior. |
| [docs/demo_feature_layout.md](docs/demo_feature_layout.md) | The feature-package organization convention used by the demo. |

Use the tutorial when you want a complete walkthrough, and use the manual when you need a subsystem-level explanation or a contract-backed API decision.

## Installation

Install the package in editable mode without dependency resolution:

```bash
python -m pip install -e . --no-deps
```

Then install the repository’s runtime and development dependencies manually. The discovered dependencies are:

- `pygame`
- `numpy`
- `coverage` for test and coverage workflows

Manual dependency installation is required because building binary dependencies can be problematic on Windows, and the repository intentionally keeps the editable install free of automatic dependency resolution.

## Project Structure

The repository is split into a framework package, a runnable demo, docs, and tests:

- `gui_do/` contains the tiered public API and internal subsystem packages.
- `demo_features/` contains the demo application’s feature packages and bootstrap config.
- `gui_do_demo.py` is the runnable demo entrypoint.
- `docs/` contains the runtime contracts and architectural reference material.
- `tests/` contains public API, contract, and behavior tests.

The `demo_features/` package is especially important because it shows the intended application-scale organization: one folder per feature package, public package roots in each feature directory, and shared bootstrap wiring in `demo_config.py`.

## See Also

- [MANUAL.md](MANUAL.md)
- [TUTORIAL.md](TUTORIAL.md)
- [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md)
- [docs/public_api_spec.md](docs/public_api_spec.md)
- [gui_do_demo.py](gui_do_demo.py)
