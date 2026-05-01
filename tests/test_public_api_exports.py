import unittest
import gui_do


class TestPublicAPIExports(unittest.TestCase):
    def test_selected_runtime_symbols_exist(self):
        expected = [
            "GuiApplication",
            "EventManager",
            "EventBus",
            "WorkspacePersistenceManager",
            "FeatureSpec",
            "WindowSpec",
            "RuntimeSceneSpec",
            "ActionSpec",
            "TabLayoutContext",
            "bootstrap_host_application",
        ]
        for name in expected:
            self.assertTrue(hasattr(gui_do, name), msg=f"Missing public symbol: {name}")

    def test_selected_functional_exports_are_callable(self):
        expected_callables = [
            "bootstrap_host_application",
            "build_tab_builder_specs",
            "create_feature_presented_window",
        ]
        for name in expected_callables:
            self.assertTrue(callable(getattr(gui_do, name)), msg=f"Expected callable export: {name}")
