import unittest

from gui_do.features.feature_lifecycle import create_anchored_feature_window


class _DummyLayout:
    def anchored(self, size, *, anchor, margin, use_rect):
        return (size, anchor, margin, use_rect)


class _DummyApp:
    def __init__(self):
        self.layout = _DummyLayout()


class _DummyRoot:
    def add(self, control):
        return control


class _DummyHost:
    def __init__(self):
        self.app = _DummyApp()
        self.root = _DummyRoot()


class _CaptureWindowControl:
    def __init__(self, control_id, rect, title, **kwargs):
        self.control_id = control_id
        self.rect = rect
        self.title = title
        self.kwargs = kwargs


class TestFeatureWindowTitleFontRole(unittest.TestCase):
    def test_default_title_role_is_not_overridden_when_unspecified(self):
        host = _DummyHost()

        window = create_anchored_feature_window(
            host,
            window_control_cls=_CaptureWindowControl,
            control_id="w",
            title="Window",
            size=(320, 200),
            anchor="center",
            margin=(10, 10),
        )

        self.assertNotIn("title_font_role", window.kwargs)
        self.assertTrue(window.kwargs["use_frame_backdrop"])

    def test_explicit_title_role_is_forwarded(self):
        host = _DummyHost()

        window = create_anchored_feature_window(
            host,
            window_control_cls=_CaptureWindowControl,
            control_id="w",
            title="Window",
            size=(320, 200),
            anchor="center",
            margin=(10, 10),
            title_font_role="title",
            use_frame_backdrop=False,
        )

        self.assertEqual("title", window.kwargs["title_font_role"])
        self.assertFalse(window.kwargs["use_frame_backdrop"])

    def test_titlebar_controls_are_forwarded(self):
        host = _DummyHost()

        window = create_anchored_feature_window(
            host,
            window_control_cls=_CaptureWindowControl,
            control_id="w",
            title="Window",
            size=(320, 200),
            anchor="center",
            margin=(10, 10),
            titlebar_controls={"include_window_hide_image_button": False},
        )

        self.assertEqual(
            {
                "include_window_lower_button": True,
                "include_window_hide_image_button": False,
                "menus_enabled": True,
            },
            window.kwargs["titlebar_controls"],
        )


if __name__ == "__main__":
    unittest.main()
