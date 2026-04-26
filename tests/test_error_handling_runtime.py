import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do.controls.image_control import ImageControl
from gui_do.graphics import load_pristine_surface
from gui_do.core.telemetry_analyzer import load_telemetry_log_file
from gui_do import Feature, FeatureManager


class ErrorHandlingRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.display = pygame.display.set_mode((320, 200))

    def tearDown(self) -> None:
        pygame.quit()

    def test_feature_constructor_error_includes_logical_context(self) -> None:
        with self.assertRaises(ValueError) as exc_info:
            Feature("   ")

        text = str(exc_info.exception)
        self.assertIn("feature name must be a non-empty string", text)
        self.assertIn("kind=logical", text)
        self.assertIn("subsystem=feature_lifecycle", text)
        self.assertIn("operation=Feature.__init__", text)
        self.assertIn("source=", text)

    def test_load_pristine_surface_missing_file_includes_io_context(self) -> None:
        with self.assertRaises(ValueError) as exc_info:
            load_pristine_surface("this_file_should_not_exist_12345.png")

        text = str(exc_info.exception)
        self.assertIn("failed to load pristine surface", text)
        self.assertIn("kind=io", text)
        self.assertIn("operation=load_pristine_surface", text)
        self.assertIn("source=", text)
        self.assertIn("path=", text)

    def test_image_control_missing_file_includes_io_context(self) -> None:
        with self.assertRaises(ValueError) as exc_info:
            ImageControl("img", Rect(0, 0, 10, 10), "this_image_should_not_exist_98765.png")

        text = str(exc_info.exception)
        self.assertIn("failed to load image control bitmap", text)
        self.assertIn("kind=io", text)
        self.assertIn("operation=ImageControl._load_image", text)
        self.assertIn("source=", text)
        self.assertIn("path=", text)

    def test_duplicate_feature_registration_error_keeps_value_error_type_and_context(self) -> None:
        manager = FeatureManager(app=object())
        manager.register(Feature("same_name"))

        with self.assertRaises(ValueError) as exc_info:
            manager.register(Feature("same_name"))

        text = str(exc_info.exception)
        self.assertIn("feature already registered: same_name", text)
        self.assertIn("kind=logical", text)
        self.assertIn("operation=FeatureManager.register", text)

    def test_telemetry_load_invalid_json_line_reports_line_number(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as handle:
            path = handle.name
            handle.write('{"type": "sample", "system": "s", "point": "p", "elapsed_ms": 1, "metadata": {}}\n')
            handle.write("not-valid-json\n")

        try:
            with self.assertRaises(ValueError) as exc_info:
                load_telemetry_log_file(path)
            text = str(exc_info.exception)
            self.assertIn("failed to parse telemetry log line as JSON", text)
            self.assertIn("kind=io", text)
            self.assertIn("line_number", text)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
