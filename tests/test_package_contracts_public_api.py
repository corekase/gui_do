import unittest
from pathlib import Path

import gui_do


def _read_package_contracts() -> str:
    path = Path(__file__).resolve().parents[1] / "docs" / "package_contracts.md"
    return path.read_text(encoding="utf-8")


def _extract_documented_gui_import_symbols(content: str) -> list[str]:
    start_marker = "from gui_do import ("
    start = content.find(start_marker)
    if start == -1:
        return []

    lines = content[start + len(start_marker):].splitlines()
    names: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith(")"):
            break
        if line.startswith("#"):
            continue
        name = line.rstrip(",").strip()
        if name:
            names.append(name)
    return names


class TestPackageContractsPublicAPI(unittest.TestCase):
    def test_package_contracts_contains_public_import_block(self):
        content = _read_package_contracts()

        self.assertIn("from gui_do import (", content)
        self.assertIn("from demo_features.mandelbrot_demo_feature import MandelStatusEvent", content)

    def test_all_documented_gui_root_symbols_resolve(self):
        content = _read_package_contracts()
        symbols = _extract_documented_gui_import_symbols(content)

        self.assertTrue(symbols, msg="No symbols parsed from package contracts gui_do import block")

        missing = [name for name in symbols if not hasattr(gui_do, name)]
        self.assertEqual([], missing, msg=f"Documented symbols missing from gui_do: {missing}")

    def test_documented_gui_import_block_has_no_duplicates(self):
        content = _read_package_contracts()
        symbols = _extract_documented_gui_import_symbols(content)

        seen = set()
        duplicates = []
        for name in symbols:
            if name in seen:
                duplicates.append(name)
            seen.add(name)
        self.assertEqual([], duplicates, msg=f"Duplicate symbols in package contracts import list: {duplicates}")
