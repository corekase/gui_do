import os
import unittest

from gui.utility.bitmapfactory import WidgetGraphicsFactory
from gui.utility.constants import GuiError
from gui.utility.resource_error import DataResourceErrorHandler


class ResourcePathHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = WidgetGraphicsFactory()

    def test_file_resource_requires_at_least_one_component(self) -> None:
        with self.assertRaises(GuiError):
            self.factory.file_resource()

    def test_file_resource_rejects_empty_or_non_string_components(self) -> None:
        with self.assertRaises(GuiError):
            self.factory.file_resource("")
        with self.assertRaises(GuiError):
            self.factory.file_resource("images", None)  # type: ignore[arg-type]

    def test_file_resource_rejects_absolute_components(self) -> None:
        absolute_component = os.path.abspath("somewhere")
        with self.assertRaises(GuiError):
            self.factory.file_resource(absolute_component)

    def test_file_resource_rejects_data_root_escape(self) -> None:
        with self.assertRaises(GuiError):
            self.factory.file_resource("..", "secrets.txt")

    def test_file_resource_resolves_under_data_root(self) -> None:
        resolved = self.factory.file_resource("images", "backdrop.jpg")
        normalized = os.path.normpath(resolved)

        self.assertTrue(normalized.endswith(os.path.normpath(os.path.join("data", "images", "backdrop.jpg"))))

    def test_data_display_path_returns_data_suffix_when_present(self) -> None:
        full_path = os.path.abspath(os.path.join("data", "images", "backdrop.jpg"))

        display = DataResourceErrorHandler.data_display_path(full_path)

        expected_suffix = os.path.normpath(os.path.join(os.sep, "data", "images", "backdrop.jpg"))
        self.assertEqual(os.path.normpath(display), expected_suffix)

    def test_raise_load_error_wraps_path_with_guierror(self) -> None:
        full_path = os.path.abspath(os.path.join("data", "fonts", "missing.ttf"))

        with self.assertRaises(GuiError) as ctx:
            DataResourceErrorHandler.raise_load_error("failed to load", full_path, RuntimeError("boom"))

        message = str(ctx.exception)
        self.assertIn("failed to load", message)
        self.assertIn("data", message.lower())


if __name__ == "__main__":
    unittest.main()
