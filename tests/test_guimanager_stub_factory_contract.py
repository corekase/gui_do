import unittest

from gui_manager_test_factory import build_gui_manager_stub


class GuiManagerStubFactoryContractTests(unittest.TestCase):
    def test_builds_stub_with_required_collaborators(self) -> None:
        gui = build_gui_manager_stub()

        required_attrs = [
            "object_registry",
            "dispatch_bridge",
            "event_delivery",
            "event_input",
            "graphics",
            "layout",
            "lifecycle",
            "lock_flow",
            "pointer",
            "render_flow",
            "task_panel_config",
            "widget_state",
            "workspace",
        ]
        for attr in required_attrs:
            self.assertTrue(hasattr(gui, attr), f"missing collaborator: {attr}")

    def test_build_can_optionally_include_ui_factory(self) -> None:
        gui = build_gui_manager_stub(include_ui_factory=True)
        self.assertTrue(hasattr(gui, "ui_factory"))


if __name__ == "__main__":
    unittest.main()
