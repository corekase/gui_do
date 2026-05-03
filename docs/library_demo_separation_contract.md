# GUI_DO Library vs Demo Separation Contract

## Principle

`gui_do` is the reusable framework package. Demo code is consumer code and stays outside the package boundary.

## Repository Roles

- `gui_do/`: framework runtime, controls, events, layout, state, persistence, telemetry, and bootstrap APIs.
- `demo_features/`: demo feature implementations and demo-owned assets.
- `gui_do_demo.py`: demo entrypoint that consumes public `gui_do` exports.
- `tests/`: framework and contract tests.
- `docs/`: architecture, API, and runtime contract documentation.

## Import Boundary

- Framework code under `gui_do/` must not import from `demo_features`.
- Consumer entrypoints should import from `gui_do` root exports instead of internal `gui_do.*` modules.

Current enforcement:

- `tests/test_boundary_contracts.py::test_gui_package_does_not_import_demo_features`
- `tests/test_boundary_contracts.py::test_demo_entrypoint_uses_gui_root_import`

## Packaging Boundary

- Wheel packaging targets `gui_do*` packages.
- Demo code remains in repository source for development/demo runs.
- Public consumer API is the `gui_do` root import contract documented in `docs/public_api_spec.md`.

## Operational Guidance

- Treat demo code as a consumer integration layer.
- Keep framework APIs demo-agnostic.
- Add new demo-only schemas/events under `demo_features/` unless they are intended as reusable framework primitives.

## Related Docs

- `docs/architecture_boundary_spec.md`
- `docs/public_api_spec.md`
- `docs/package_contracts.md`
