"""Canonical contract-test catalog shared by docs/parity regression tests."""

CONTRACT_TEST_MODULES = (
    "tests.test_boundary_contracts",
    "tests.test_public_api_exports",
    "tests.test_mandel_event_schema_exports",
    "tests.test_public_api_docs_contracts",
    "tests.test_architecture_boundary_docs_contracts",
    "tests.test_contract_command_parity",
    "tests.test_readme_docs_contracts",
    "tests.test_contract_docs_helpers",
    "tests.test_contract_catalog_consistency",
)

CONTRACT_TEST_FILE_PATHS = tuple(module.replace(".", "/") + ".py" for module in CONTRACT_TEST_MODULES)

CONTRACT_UNITTEST_COMMAND = "python -m unittest " + " ".join(CONTRACT_TEST_MODULES) + " -v"
CONTRACT_PYTEST_COMMAND = "python -m pytest -q " + " ".join(CONTRACT_TEST_FILE_PATHS)

ARCHITECTURE_DOC_PATHS = (
    "docs/public_api_spec.md",
    "docs/event_system_spec.md",
    "docs/architecture_boundary_spec.md",
)

BOUNDARY_RELATED_DOC_PATHS = (
    "docs/public_api_spec.md",
    "docs/event_system_spec.md",
)

BOUNDARY_ENFORCEMENT_TEST_IDS = (
    "tests/test_boundary_contracts.py::test_gui_package_does_not_depend_on_demo_parts",
    "tests/test_boundary_contracts.py::test_demo_parts_does_not_depend_on_gui",
    "tests/test_boundary_contracts.py::test_demo_entrypoints_use_public_gui_api_only",
)

BOUNDARY_PYTEST_COMMAND = "python -m pytest -q tests/test_boundary_contracts.py"
