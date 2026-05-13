import unittest

from demo_features.demo_config import DEMO_BOOTSTRAP_CONFIG


class TestDemoWindowBundleOrder(unittest.TestCase):
    def test_main_scene_window_bundle_order_lists_systems_first(self):
        self.assertEqual(
            ["systems", "life", "mandel"],
            [spec.key for spec in DEMO_BOOTSTRAP_CONFIG.window_specs],
        )


if __name__ == "__main__":
    unittest.main()
