# Architecture Boundary Specification

## Purpose

This document defines hard package boundaries between reusable framework code and demo-specific code.

## Boundary Rule

- `gui/` is framework/runtime package code and must not depend on `demo_parts/`.
- `demo_parts/` contains demo-specific contracts and must remain independent from `gui/` imports.
- Active demo entrypoints (`*_demo.py`, excluding archived `_pre_rebase*_demo.py`) should consume `gui` via public root exports (`from gui import ...`) rather than internal submodule imports.

## Current Demo Boundary Assets

- `demo_parts/mandel_events.py`: Mandelbrot status topic, kind constants, and payload dataclass.

## Enforcement

Automated tests enforce both directions:

- `tests/test_boundary_contracts.py::test_gui_package_does_not_depend_on_demo_parts`
- `tests/test_boundary_contracts.py::test_demo_parts_does_not_depend_on_gui`
- `tests/test_boundary_contracts.py::test_demo_entrypoints_use_public_gui_api_only`

The boundary test uses AST-based import inspection, so only real imports are flagged (not comments or strings).

Run command:

```bash
python -m pytest -q tests/test_boundary_contracts.py
```

## Notes

This separation prevents demo implementation details from leaking into the reusable framework API and allows future demos to define their own contracts without modifying `gui` internals.

Related documents:

- `docs/public_api_spec.md`
- `docs/event_system_spec.md`
