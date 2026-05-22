import unittest

import pygame

from demo_features.life.life_specs import _LIFE_WINDOW_SIZE
from demo_features.main.main_build_helpers import _add_opt_out_test_window
from demo_features.mandelbrot.mandelbrot_specs import _WINDOW_SIZE as _MANDEL_WINDOW_SIZE


class _RootStub:
    def __init__(self):
        self.added = []

    def add(self, control):
        self.added.append(control)
        return control


class _WindowPresentationStub:
    def __init__(self):
        self.calls = []

    def register_feature_window(self, key, *, feature_attribute_name):
        self.calls.append((key, feature_attribute_name))


class _HostStub:
    def __init__(self):
        self.app = type("_App", (), {"theme": None})()
        self.root = _RootStub()
        self.window_presentation = _WindowPresentationStub()


class TestDemoWindowContentSizeSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_life_window_size_is_content_body_only(self):
        expected_width = 10 + 600 + 10
        expected_height = 10 + 600 + 8 + 28 + 10
        self.assertEqual((expected_width, expected_height), _LIFE_WINDOW_SIZE)

    def test_mandelbrot_window_size_is_content_body_only(self):
        btn_w, btn_h, btn_gap = 120, 30, 8
        row_pad = 12
        num_btns = 5
        pad = 10
        canvas_h = 560
        status_h = 20
        canvas_w = num_btns * btn_w + (num_btns - 1) * btn_gap + 2 * row_pad
        expected = (
            pad + canvas_w + pad,
            pad + canvas_h + 8 + btn_h + 6 + status_h + pad,
        )
        self.assertEqual(expected, _MANDEL_WINDOW_SIZE)

    def test_opt_out_test_window_uses_content_size_for_text_body(self):
        host = _HostStub()

        _add_opt_out_test_window(host)

        window = host.opt_out_test_window
        content = window.content_rect()
        label = window.children[0].children[0]

        content_pad = 8
        self.assertEqual(label.rect.width + (content_pad * 2), content.width)
        self.assertEqual(label.rect.height + (content_pad * 2), content.height)
        self.assertEqual(content.left + content_pad, label.rect.left)
        self.assertEqual(content.top + content_pad, label.rect.top)


if __name__ == "__main__":
    unittest.main()
