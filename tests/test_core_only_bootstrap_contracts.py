import unittest

import gui_do


class TestCoreOnlyBootstrapContracts(unittest.TestCase):
    def test_core_bootstrap_surface_exists_on_gui_root(self):
        expected = [
            "bootstrap_host_application",
            "FeatureSpec",
            "WindowSpec",
            "RuntimeSceneSpec",
            "ActionSpec",
            "TabBuilderSpec",
            "TabLayoutContext",
        ]
        for name in expected:
            self.assertTrue(hasattr(gui_do, name), msg=f"Missing core bootstrap symbol: {name}")
