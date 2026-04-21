import unittest

from pygame import Rect

from gui.controls.scrollbar_control import ScrollbarControl
from gui.controls.slider_control import SliderControl
from gui.layout.layout_axis import LayoutAxis


class ValueControlInvariantsTests(unittest.TestCase):
    def test_slider_normalizes_inverted_range_and_clamps_value(self) -> None:
        slider = SliderControl("s", Rect(0, 0, 120, 24), LayoutAxis.HORIZONTAL, 100.0, 0.0, 150.0)

        self.assertEqual(slider.minimum, 0.0)
        self.assertEqual(slider.maximum, 100.0)
        self.assertEqual(slider.value, 100.0)

    def test_scrollbar_handle_does_not_exceed_track_when_viewport_exceeds_content(self) -> None:
        bar = ScrollbarControl(
            "sb",
            Rect(0, 0, 120, 24),
            LayoutAxis.HORIZONTAL,
            content_size=100,
            viewport_size=500,
            offset=0,
            step=10,
        )

        track = bar._track_rect()
        handle = bar.handle_rect()

        self.assertLessEqual(handle.width, track.width)
        self.assertEqual(bar._max_offset(), 0)

    def test_scrollbar_reclamps_offset_after_external_size_mutation(self) -> None:
        bar = ScrollbarControl(
            "sb",
            Rect(0, 0, 120, 24),
            LayoutAxis.HORIZONTAL,
            content_size=1000,
            viewport_size=200,
            offset=700,
            step=10,
        )

        bar.content_size = 300
        bar.viewport_size = 250
        bar.offset = 999

        _ = bar.handle_rect()

        self.assertEqual(bar.offset, bar._max_offset())


if __name__ == "__main__":
    unittest.main()
