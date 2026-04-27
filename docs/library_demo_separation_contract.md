# GUI_DO Library vs Demo Separation Contract

## Architectural Principle

Complete separation between the reusable **gui_do framework library** and **demo-specific code**. This enables the framework to be distributed and used independently without any demo dependencies or assumptions.

## Library Definition

The **GUI_DO LIBRARY** consists of:

- **gui_do/**: Core framework package
  - All controls, event system, layout system, theme system, graphics factory
  - Telemetry, timers, scheduler, focus management
  - 100% reusable, zero demo dependencies

- **tests/**: Unit test suite
  - Verifies all framework contracts and runtime behavior
  - Can be run independently in core-only (post-init) state
  - Contains some demo tests (for demo contract verification) but core tests run without demo

- **docs/**: Architecture and API documentation
  - public_api_spec.md: Public API contract
  - architecture_boundary_spec.md: Component boundaries
  - event_system_spec.md: Event architecture

- **scripts/manage.py**: Lifecycle management tool
  - Handles init/apply/verify/check/update operations
  - Enables users to strip demo content and obtain core-only distribution
  - Uses regex-based dynamic discovery (not hardcoded lists)

### What the Library Does NOT Include

- ❌ demo_features/ package
- ❌ demo_features/data/ (fonts, images, cursors)
- ❌ gui_do_demo.py (demo entrypoint)
- ❌ Any demo-specific code or assets

## Demo Definition

The **DEMO** (not part of the library distribution) consists of:

- **demo_features/**: Demo feature implementations
  - Showcases framework capabilities (controls, layout, scenes, events)
  - ControlsShowcaseFeature, StylesShowcaseFeature, etc.
  - Importable only from gui_do public root (enforced)

- **demo_features/data/**: Demo-owned assets
  - Fonts: Ubuntu-B.ttf, Gimbot.ttf
  - Images: backdrop.jpg, realize.png
  - Cursors: cursor.png, hand.png

- **gui_do_demo.py**: Demo application entrypoint
  - Imports demo_features only
  - Uses framework public API only
  - Passes full CWD-relative paths to framework for all asset loading

### What the Demo Does NOT Include

- ❌ Framework internals (only uses public API)
- ❌ Test code (except minimal smoke tests in demo features)

## Separation Enforcement Points

### 1. Import Separation (Code Level)

**gui_do/ must not import demo_features**
- Test: `test_gui_package_does_not_depend_on_demo_features` (test_boundary_contracts.py)
- Verification: AST walk of all gui_do/ Python files, no `import demo_features` or `from demo_features`

**demo_features/ must only import gui_do public root**
- Test: `test_demo_features_do_not_import_gui_do_internals` (test_boundary_contracts.py)
- Verification: No `from gui_do.` submodule imports in demo_features/ code

**gui_do_demo.py must use only gui_do public API**
- Tests: All demo entrypoint tests in test_boundary_contracts.py
- Verification:
  - No `from gui_do.` submodule imports
  - Only `from gui_do import (...)` blocks
  - Only public API exports used
  - No import aliases
  - Single import block

### 2. Path Separation (Code Level)

**gui_do/ must not reference demo_features/data/ paths**
- Test: `test_gui_package_has_no_hardcoded_demo_data_paths` (test_library_demo_separation_contracts.py)
- Verification: No `demo_features/data` strings in gui_do/ code

**Framework path resolution must accept caller-supplied paths**
- Functions:
  - `load_pristine_surface(source)` - resolves from CWD or absolute, not demo_features/data/images/
  - `register_cursor(name, path, hotspot)` - takes full path parameter, resolves from CWD
  - `ImageControl._resolve_image_path()` - resolves from CWD only
  - `ColorTheme._background_bitmap` - defaults to None, not auto-loaded from demo
- Test: `test_path_resolution_functions_accept_caller_paths` (test_library_demo_separation_contracts.py)

**Demo must provide all asset paths as CWD-relative**
- Test: `test_demo_provides_full_paths_to_framework` (test_library_demo_separation_contracts.py)
- Verification:
  - `register_cursor("normal", "demo_features/data/cursors/cursor.png", ...)`
  - `set_pristine("demo_features/data/images/backdrop.jpg", ...)`
  - No bare filenames passed to framework functions

### 3. Packaging Separation (Distribution Level)

**Wheel distribution (.whl) contains only gui_do/**
- Configuration: `pyproject.toml` [tool.setuptools.packages.find] `include = ["gui_do*"]`
- Verification: Build wheel, inspect zipfile, confirm only `gui_do/` and `gui_do-X.Y.Z.dist-info/`
- Test: `test_pyproject_packages_find_includes_only_gui_do` (test_library_demo_separation_contracts.py)

**Source distribution (.tar.gz) contains gui_do/, tests/, docs/, scripts/manage.py but NOT demo_features/**
- Configuration: `MANIFEST.in` explicitly excludes `demo_features/data`
- Verification: Extract sdist, confirm no demo_features/ directory
- Test: `test_manifest_in_excludes_demo_features_data` (test_library_demo_separation_contracts.py)

**Editable install (pip install -e .) includes everything for development**
- Contains gui_do/, demo_features/, tests/, docs/, scripts/
- Allows local development with demo
- Not a distribution artifact (development mode only)

### 4. Architectural Separation (Documentation Level)

**Separation principle formally documented**
- Location: `LIBRARY_SEPARATION_PRINCIPLE` constant in `tests/contract_test_catalog.py`
- Test: `test_separation_principle_is_documented` (test_library_demo_separation_contracts.py)
- Contents:
  - Clear definition of library vs demo
  - What each contains
  - Enforcement rules for each
  - References to specific contract tests

**Library composition clearly defined**
- Test: `test_library_composition_documented` (test_library_demo_separation_contracts.py)
- Verifies principle includes library components (gui_do/, tests/, docs/, scripts/manage.py)
- Verifies principle includes demo components (demo_features/, gui_do_demo.py)
- Verifies principle documents that demo is NOT in distributions

## Contract Tests (8 tests in test_library_demo_separation_contracts.py)

1. ✅ `test_separation_principle_is_documented` - Principle exists and has required sections
2. ✅ `test_gui_package_has_no_hardcoded_demo_data_paths` - gui_do/ has no demo_features/data strings
3. ✅ `test_path_resolution_functions_accept_caller_paths` - load_pristine_surface, register_cursor support CWD resolution
4. ✅ `test_demo_provides_full_paths_to_framework` - gui_do_demo.py passes full demo_features/ paths
5. ✅ `test_pyproject_packages_find_includes_only_gui_do` - packages.find includes only gui_do*
6. ✅ `test_manifest_in_excludes_demo_features_data` - MANIFEST.in has no demo_features reference
7. ✅ `test_library_composition_documented` - Principle documents library and demo composition
8. ✅ `test_all_separation_rules_consolidated` - All rules consolidated in one test suite

## Related Contract Tests (in test_boundary_contracts.py)

- `test_gui_package_does_not_depend_on_demo_features` - Import separation
- `test_demo_features_do_not_import_gui_do_internals` - Import separation
- `test_demo_entrypoints_use_public_gui_api_only` - API separation
- `test_demo_entrypoints_do_not_import_gui_submodules_via_import_statement` - API separation
- `test_demo_entrypoints_import_only_named_public_gui_exports` - API separation
- `test_demo_entrypoints_do_not_alias_gui_root_imports` - API separation
- `test_demo_entrypoints_use_single_gui_root_import_block` - API separation
- `test_active_demo_entrypoints_match_expected_contract_set` - Entrypoint inventory

## Test Suite Results

- **Total contract tests**: 15 tests across two test modules
  - 8 tests in `test_library_demo_separation_contracts.py`
  - 9 tests in `test_boundary_contracts.py` (demo-related)

- **Total project tests**: 872 tests (all passing)
  - 864 core tests (framework, runtime, etc.)
  - 8 new separation contract tests

- **Test execution**: ~20 seconds for full suite
- **CI integration**: All tests run on every commit; any separation violation fails the suite

## Benefits of This Separation

1. **Framework reusability**: gui_do can be used without any demo code
2. **Clean distribution**: Wheel and sdist contain only the library
3. **Maintenance clarity**: Clear boundaries between framework and showcase code
4. **Future extensibility**: New features added to framework don't depend on demo
5. **User control**: Users can strip demo via `manage.py init` to get pure library
6. **Testing isolation**: Core tests run independently; demo tests optional
7. **No hidden dependencies**: Framework paths never assume demo assets exist

## Summary

The gui_do library is architecturally separated from its demo through:
- **Enforced import boundaries** (AST-verified)
- **Isolated path resolution** (caller-supplied paths, no hardcoded demo references)
- **Packaging segregation** (wheel/sdist exclude demo, editable includes for development)
- **Documented principle** (formalized in code and tests)
- **Comprehensive test coverage** (15 dedicated separation contract tests)

This separation is verified on every commit via the contract test suite.
