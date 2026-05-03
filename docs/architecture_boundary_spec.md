# Architecture Boundary Specification

## Purpose

Define and document the import boundary between framework runtime code and demo consumer code.

## Boundary Rule

- `gui_do/` is framework/runtime package code and must not depend on `demo_features/`.
- `gui_do_demo.py` is a consumer entrypoint and should import from the `gui_do` root package, not internal `gui_do.*` submodules.

Boundary intent:

- Keep `gui_do/` reusable as a standalone package.
- Keep demo-specific evolution isolated to `demo_features/` and entrypoint code.
- Preserve a clear consumer pattern for imports from `gui_do`.

## Active Demo Entrypoint

- `gui_do_demo.py`

## Enforcement

Automated tests enforce the boundary using AST import inspection:

- `tests/test_boundary_contracts.py::test_gui_package_does_not_import_demo_features`
- `tests/test_boundary_contracts.py::test_demo_entrypoint_uses_gui_root_import`

Run command:

```bash
python -m pytest -q tests/test_boundary_contracts.py
```

## Related Documents

- `docs/public_api_spec.md`
- `docs/event_system_spec.md`
- `docs/package_contracts.md`
