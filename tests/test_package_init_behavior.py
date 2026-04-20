import ctypes
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import gui


class PackageInitBehaviorTests(unittest.TestCase):
    def test_package_exports_expected_public_symbols(self) -> None:
        self.assertTrue(hasattr(gui, "GuiManager"))
        self.assertTrue(hasattr(gui, "Engine"))
        self.assertTrue(hasattr(gui, "StateManager"))
        self.assertTrue(hasattr(gui, "Event"))
        self.assertTrue(hasattr(gui, "CanvasEvent"))
        self.assertTrue(hasattr(gui, "ButtonStyle"))
        self.assertTrue(hasattr(gui, "colours"))

    def test_windows_dpi_awareness_exceptions_propagate(self) -> None:
        exception_cases = [OSError("dpi fail"), AttributeError("missing api")]

        for exc in exception_cases:
            with self.subTest(exception_type=type(exc).__name__):
                set_dpi = SimpleNamespace(SetProcessDPIAware=lambda: (_ for _ in ()).throw(exc))
                fake_windll = SimpleNamespace(user32=set_dpi)
                with patch("os.name", "nt"), patch.object(ctypes, "windll", fake_windll, create=True):
                    with self.assertRaises(type(exc)):
                        gui._enable_windows_dpi_awareness()


if __name__ == "__main__":
    unittest.main()
