import unittest
from pathlib import Path


class TestContractCatalogConsistency(unittest.TestCase):
    def test_required_contract_docs_exist(self):
        docs_dir = Path(__file__).resolve().parents[1] / "docs"
        required = [
            "public_api_spec.md",
            "event_system_spec.md",
            "architecture_boundary_spec.md",
            "package_contracts.md",
            "runtime_operating_contracts.md",
            "library_demo_separation_contract.md",
        ]

        missing = [name for name in required if not (docs_dir / name).exists()]
        self.assertEqual([], missing, msg=f"Missing docs: {missing}")
