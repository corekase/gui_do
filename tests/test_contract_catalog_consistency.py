import unittest
from pathlib import Path

from contract_test_catalog import BOUNDARY_ENFORCEMENT_TEST_IDS
from contract_test_catalog import BOUNDARY_PYTEST_COMMAND
from contract_test_catalog import BOUNDARY_RELATED_DOC_PATHS
from contract_test_catalog import CONTRACT_PYTEST_COMMAND
from contract_test_catalog import CONTRACT_TEST_FILE_PATHS
from contract_test_catalog import CONTRACT_TEST_MODULES
from contract_test_catalog import CONTRACT_UNITTEST_COMMAND


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

    def test_unittest_command_matches_cataloged_modules(self) -> None:
        expected = "python -m unittest " + " ".join(CONTRACT_TEST_MODULES) + " -v"
        self.assertEqual(CONTRACT_UNITTEST_COMMAND, expected)

    def test_pytest_command_matches_cataloged_paths(self) -> None:
        expected = "python -m pytest -q " + " ".join(CONTRACT_TEST_FILE_PATHS)
        self.assertEqual(CONTRACT_PYTEST_COMMAND, expected)

    def test_boundary_constants_are_non_empty_and_well_formed(self) -> None:
        self.assertTrue(BOUNDARY_ENFORCEMENT_TEST_IDS)
        self.assertTrue(BOUNDARY_RELATED_DOC_PATHS)
        self.assertEqual(BOUNDARY_PYTEST_COMMAND, "python -m pytest -q tests/test_boundary_contracts.py")

        for test_id in BOUNDARY_ENFORCEMENT_TEST_IDS:
            self.assertIn("::", test_id)

        for doc_path in BOUNDARY_RELATED_DOC_PATHS:
            self.assertTrue(doc_path.endswith(".md"))


if __name__ == "__main__":
    unittest.main()
