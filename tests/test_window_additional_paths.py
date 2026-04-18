import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pygame import Rect

from gui.utility.events import GuiError, InteractiveState
from gui.widgets.window import Window


class _FakeSurface:
    def __init__(self, size):
        self._size = size
        self.blit_calls = []

    def convert(self):
        return self

    def get_rect(self):
        return Rect(0, 0, self._size[0], self._size[1])

    def blit(self, bitmap, pos):
        self.blit_calls.append((bitmap, pos))


class _CopySurface:
    def convert(self):
        return self


class WindowAdditionalPathTests(unittest.TestCase):
    def test_constructor_validates_title_position_and_size(self) -> None:
        gui = SimpleNamespace(graphics_factory=SimpleNamespace(get_titlebar_height=lambda: 10))

        with self.assertRaises(GuiError):
            Window(gui, "", (0, 0), (10, 10))
        with self.assertRaises(GuiError):
            Window(gui, "w", "bad", (10, 10))  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            Window(gui, "w", (0, 0), "bad")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            Window(gui, "w", (0, 0), (0, 10))

    def test_constructor_without_backdrop_draws_frame_and_initializes_bitmaps(self) -> None:
        frame_calls = []

        class FakeFrame:
            def __init__(self, _gui, _id, _rect):
                self.state = None
                self.surface = None

            def draw(self):
                frame_calls.append("draw")

        surface_obj = _FakeSurface((40, 20))
        title_active = _FakeSurface((40, 10))
        title_inactive = _FakeSurface((40, 10))
        lower = _FakeSurface((8, 8))

        gui = SimpleNamespace()
        gui.graphics_factory = SimpleNamespace(
            get_titlebar_height=lambda: 12,
            build_window_chrome_visuals=lambda *_args: SimpleNamespace(
                title_bar_inactive=title_inactive,
                title_bar_active=title_active,
                lower_widget=lower,
            ),
        )
        gui.copy_graphic_area = lambda *_args, **_kwargs: _CopySurface()
        gui.set_pristine = lambda *_args, **_kwargs: None

        with patch("gui.widgets.window.pygame.surface.Surface", return_value=surface_obj), patch("gui.widgets.window.Frame", FakeFrame):
            window = Window(gui, "title", (5, 30), (40, 20), backdrop=None)

        self.assertEqual(frame_calls, ["draw"])
        self.assertEqual(window.position, (5, 30))
        self.assertTrue(window.visible)
        self.assertEqual(window.titlebar_size, 12)
        self.assertIs(window.surface, surface_obj)
        self.assertIs(window.title_bar_inactive_bitmap, title_inactive)
        self.assertIs(window.title_bar_active_bitmap, title_active)

    def test_constructor_with_backdrop_uses_set_pristine(self) -> None:
        set_pristine_calls = []
        surface_obj = _FakeSurface((50, 25))

        gui = SimpleNamespace()
        gui.graphics_factory = SimpleNamespace(
            get_titlebar_height=lambda: 10,
            build_window_chrome_visuals=lambda *_args: SimpleNamespace(
                title_bar_inactive=_FakeSurface((50, 10)),
                title_bar_active=_FakeSurface((50, 10)),
                lower_widget=_FakeSurface((8, 8)),
            ),
        )
        gui.copy_graphic_area = lambda *_args, **_kwargs: _CopySurface()
        gui.set_pristine = lambda backdrop, target: set_pristine_calls.append((backdrop, target))

        with patch("gui.widgets.window.pygame.surface.Surface", return_value=surface_obj):
            window = Window(gui, "title", (1, 2), (50, 25), backdrop="bg.png")

        self.assertEqual(len(set_pristine_calls), 1)
        self.assertEqual(set_pristine_calls[0][0], "bg.png")
        self.assertIs(set_pristine_calls[0][1], window)

    def test_constructor_normalizes_non_callable_lifecycle_handlers(self) -> None:
        surface_obj = _FakeSurface((30, 20))
        gui = SimpleNamespace()
        gui.graphics_factory = SimpleNamespace(
            get_titlebar_height=lambda: 10,
            build_frame_visuals=lambda _rect: SimpleNamespace(
                idle=_FakeSurface((30, 20)),
                hover=_FakeSurface((30, 20)),
                armed=_FakeSurface((30, 20)),
                hit_rect=Rect(0, 0, 30, 20),
            ),
            build_window_chrome_visuals=lambda *_args: SimpleNamespace(
                title_bar_inactive=_FakeSurface((30, 10)),
                title_bar_active=_FakeSurface((30, 10)),
                lower_widget=_FakeSurface((8, 8)),
            ),
        )
        gui.copy_graphic_area = lambda *_args, **_kwargs: _CopySurface()
        gui.set_pristine = lambda *_args, **_kwargs: None

        with patch("gui.widgets.window.pygame.surface.Surface", return_value=surface_obj):
            window = Window(
                gui,
                "title",
                (0, 20),
                (30, 20),
                preamble="nope",  # type: ignore[arg-type]
                event_handler=1,  # type: ignore[arg-type]
                postamble={},  # type: ignore[arg-type]
            )

        # These should be harmless no-ops, not errors.
        window.run_preamble()
        window.handle_event(SimpleNamespace())
        window.run_postamble()

    def test_draw_title_bar_and_window_delegate_to_gui_surface(self) -> None:
        window = Window.__new__(Window)
        window.x = 10
        window.y = 30
        window.width = 40
        window.height = 20
        window.titlebar_size = 10
        window.window_widget_lower_bitmap = _FakeSurface((8, 8))
        window.title_bar_active_bitmap = _FakeSurface((40, 10))
        window.title_bar_inactive_bitmap = _FakeSurface((40, 10))
        window.surface = _FakeSurface((40, 20))
        blit_calls = []
        restore_calls = []
        window.gui = SimpleNamespace(
            surface=SimpleNamespace(blit=lambda bitmap, pos: blit_calls.append((bitmap, pos))),
            restore_pristine=lambda rect, target: restore_calls.append((rect, target)),
        )

        Window.draw_title_bar_active(window)
        Window.draw_title_bar_inactive(window)
        Window.draw_window(window)

        self.assertEqual(len(blit_calls), 4)
        self.assertIs(blit_calls[0][0], window.title_bar_active_bitmap)
        self.assertIs(blit_calls[2][0], window.title_bar_inactive_bitmap)
        self.assertEqual(restore_calls, [(window.surface.get_rect(), window)])

    def test_window_save_pristine_uses_copy_graphic_area(self) -> None:
        window = Window.__new__(Window)
        window.surface = _FakeSurface((10, 12))
        copied = _CopySurface()
        window.gui = SimpleNamespace(copy_graphic_area=lambda surface, rect: copied)

        Window._window_save_pristine(window)

        self.assertIs(window.pristine, copied)


if __name__ == "__main__":
    unittest.main()
