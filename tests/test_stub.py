import unittest

import gui_do_demo


class TestStub(unittest.TestCase):
    def test_demo_entrypoint_exports_main_and_app_class(self):
        self.assertTrue(hasattr(gui_do_demo, "GuiDoDemo"))
        self.assertTrue(hasattr(gui_do_demo, "main"))
        self.assertTrue(callable(gui_do_demo.main))

if __name__ == "__main__":
    unittest.main()
