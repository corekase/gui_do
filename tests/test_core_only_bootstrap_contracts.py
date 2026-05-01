import unittest

import gui_do
from demo_features import feature_abstractions


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

    def test_demo_feature_abstractions_reexport_selected_core_symbols(self):
        expected = [
            "bootstrap_host_application",
            "FeatureSpec",
            "WindowSpec",
            "RuntimeSceneSpec",
            "ActionSpec",
            "TabBuilderSpec",
            "TabLayoutContext",
            "ActiveTabUpdateRouter",
        ]
        for name in expected:
            self.assertTrue(hasattr(feature_abstractions, name), msg=f"Shim missing symbol: {name}")
