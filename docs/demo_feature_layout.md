# Demo Feature Layout Standard

This document defines the required default organization for code in demo_features/.

## Required Default

- Put each feature or scene in its own folder package.
- Add an __init__.py file to each feature folder to establish the namespace boundary and expose the canonical imports.
- Keep __init__.py as a clean public export surface (for example via __all__) with no compatibility shims.
- Include at least one *_feature.py module and at least one *_specs.py module per feature/scene package.
- Keep feature-specific classes, specs, helpers, presenters, and small support objects inside that folder.
- Use underscore filename suffixes to clarify purpose, such as *_specs.py, *_feature.py, *_presenter.py, or other descriptive variants.
- Keep the root of demo_features/ limited to bootstrap-facing files and shared static assets needed by gui_do_demo.py.

## Runtime Contract

- Bootstrapping remains explicit and spec-driven through demo_config.py.
- Runtime startup does not scan package folders or consume FEATURE_PACKAGE_INFO metadata.
- FEATURE_PACKAGE_INFO can be used as optional documentation/tooling metadata, but it is not required for feature or scene registration.

## Root Contents

The demo_features/ root should generally contain only:

- __init__.py
- demo_config.py
- data/
- feature and scene folders

## Encapsulation Goal

This folder-based organization improves feature encapsulation while still allowing each feature to grow into as many internal modules, classes, and helpers as needed.
