# Architecture Boundary Specification

## Purpose

This document defines hard package boundaries between reusable framework code and demo-specific code.

It complements the public API and event-system specs by keeping framework contracts reusable and demo schemas isolated.

## Boundary Rule

- `gui/` is framework/runtime package code and must not depend on `demo_features/`.
- `demo_features/` contains demo-specific contracts and must remain independent from `gui/` imports.
- Active demo entrypoints (`*_demo.py`) should consume `gui` via public root exports (`from gui import ...`) rather than internal submodule imports, keep named imports without aliases, and use a single `from gui import (...)` block.

Boundary intent:

- Keep `gui/` independently reusable in non-demo applications.
- Allow demo schema evolution inside `demo_features/` without leaking symbols into `gui.__all__`.
- Keep demo entrypoints readable and enforceable via one canonical gui-root import block.

Rebase status:

- Rebase migration is complete. The repository now documents and enforces only the current gui package contracts with no previous-track baggage.

## Current Demo Boundary Assets

- `demo_features/mandelbrot_demo_feature.py`: Mandelbrot status topic, kind constants, and payload dataclass.

## Current Active Demo Entrypoints

- `gui_do_demo.py`

## Enforcement

Automated tests enforce both directions:

- `tests/test_boundary_contracts.py::test_gui_package_does_not_depend_on_demo_features`
- `tests/test_boundary_contracts.py::test_demo_features_does_not_depend_on_gui`
- `tests/test_boundary_contracts.py::test_demo_entrypoints_use_public_gui_api_only`
- `tests/test_boundary_contracts.py::test_demo_entrypoints_do_not_import_gui_submodules_via_import_statement`
- `tests/test_boundary_contracts.py::test_demo_entrypoints_import_only_named_public_gui_exports`
- `tests/test_boundary_contracts.py::test_demo_entrypoints_gui_root_import_names_follow_canonical_order`
- `tests/test_boundary_contracts.py::test_demo_entrypoints_do_not_alias_gui_root_imports`
- `tests/test_boundary_contracts.py::test_demo_entrypoints_use_single_gui_root_import_block`
- `tests/test_boundary_contracts.py::test_active_demo_entrypoints_match_expected_contract_set`

The boundary test uses AST-based import inspection, so only real imports are flagged (not comments or strings).

Run command:

```bash
python -m pytest -q tests/test_boundary_contracts.py
```

## Notes

This separation prevents demo implementation details from leaking into the reusable framework API and allows future demos to define their own contracts without modifying `gui` internals.

Operationally, boundary tests are treated as release gates for import hygiene and docs parity.

Related documents:

- `docs/public_api_spec.md`
- `docs/event_system_spec.md`
