import unittest
from pathlib import Path

from contract_test_catalog import ARCHITECTURE_DOC_PATHS
from contract_test_catalog import BOUNDARY_ASSET_PATHS
from contract_test_catalog import BOUNDARY_COMMAND_SEQUENCE
from contract_test_catalog import BOUNDARY_ENFORCEMENT_TEST_IDS
from contract_test_catalog import BOUNDARY_PYTEST_COMMAND
from contract_test_catalog import BOUNDARY_RELATED_DOC_PATHS
from contract_test_catalog import CONTRACT_PYTEST_COMMAND
from contract_test_catalog import CONTRACT_TEST_FILE_PATHS
from contract_test_catalog import CONTRACT_TEST_MODULES
from contract_test_catalog import CONTRACT_UNITTEST_COMMAND
from contract_test_catalog import DEMO_PARTS_EXPORT_ORDER


class ContractCatalogConsistencyTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_file_paths_match_module_list_derivation(self) -> None:
        expected_paths = tuple(module.replace(".", "/") + ".py" for module in CONTRACT_TEST_MODULES)
        self.assertEqual(CONTRACT_TEST_FILE_PATHS, expected_paths)

    def test_all_cataloged_test_files_exist(self) -> None:
        root = self._repo_root()
        for relative_path in CONTRACT_TEST_FILE_PATHS:
            self.assertTrue((root / relative_path).exists(), f"cataloged contract test file missing: {relative_path}")

    def test_cataloged_modules_and_paths_have_no_duplicates(self) -> None:
        self.assertEqual(len(CONTRACT_TEST_MODULES), len(set(CONTRACT_TEST_MODULES)))
        self.assertEqual(len(CONTRACT_TEST_FILE_PATHS), len(set(CONTRACT_TEST_FILE_PATHS)))

    def test_unittest_command_matches_cataloged_modules(self) -> None:
        expected = "python -m unittest " + " ".join(CONTRACT_TEST_MODULES) + " -v"
        self.assertEqual(CONTRACT_UNITTEST_COMMAND, expected)

    def test_pytest_command_matches_cataloged_paths(self) -> None:
        expected = "python -m pytest -q " + " ".join(CONTRACT_TEST_FILE_PATHS)
        self.assertEqual(CONTRACT_PYTEST_COMMAND, expected)

    def test_boundary_constants_are_non_empty_and_well_formed(self) -> None:
        self.assertTrue(BOUNDARY_ENFORCEMENT_TEST_IDS)
        self.assertTrue(BOUNDARY_RELATED_DOC_PATHS)
        self.assertTrue(BOUNDARY_ASSET_PATHS)
        self.assertEqual(BOUNDARY_PYTEST_COMMAND, "python -m pytest -q tests/test_boundary_contracts.py")
        self.assertEqual(len(BOUNDARY_ENFORCEMENT_TEST_IDS), len(set(BOUNDARY_ENFORCEMENT_TEST_IDS)))
        self.assertEqual(len(BOUNDARY_ASSET_PATHS), len(set(BOUNDARY_ASSET_PATHS)))

        for test_id in BOUNDARY_ENFORCEMENT_TEST_IDS:
            self.assertIn("::", test_id)

        for doc_path in BOUNDARY_RELATED_DOC_PATHS:
            self.assertTrue(doc_path.endswith(".md"))

        for asset_path in BOUNDARY_ASSET_PATHS:
            self.assertTrue(asset_path.endswith(".py"))

    def test_boundary_command_sequence_matches_canonical_commands(self) -> None:
        self.assertEqual(
            BOUNDARY_COMMAND_SEQUENCE,
            (CONTRACT_UNITTEST_COMMAND, BOUNDARY_PYTEST_COMMAND, CONTRACT_PYTEST_COMMAND),
        )
        self.assertEqual(len(BOUNDARY_COMMAND_SEQUENCE), len(set(BOUNDARY_COMMAND_SEQUENCE)))

    def test_boundary_related_docs_are_ordered_subset_of_architecture_docs(self) -> None:
        self.assertTrue(set(BOUNDARY_RELATED_DOC_PATHS).issubset(set(ARCHITECTURE_DOC_PATHS)))

        expected_ordered_subset = tuple(
            doc_path
            for doc_path in ARCHITECTURE_DOC_PATHS
            if doc_path in set(BOUNDARY_RELATED_DOC_PATHS)
        )
        self.assertEqual(BOUNDARY_RELATED_DOC_PATHS, expected_ordered_subset)

    def test_demo_parts_export_order_constant_is_well_formed(self) -> None:
        self.assertTrue(DEMO_PARTS_EXPORT_ORDER)
        self.assertEqual(len(DEMO_PARTS_EXPORT_ORDER), len(set(DEMO_PARTS_EXPORT_ORDER)))
        self.assertEqual(DEMO_PARTS_EXPORT_ORDER[-1], "MandelStatusEvent")

        for entry in DEMO_PARTS_EXPORT_ORDER[:-1]:
            self.assertTrue(entry.startswith("MANDEL_"))


if __name__ == "__main__":
    unittest.main()
