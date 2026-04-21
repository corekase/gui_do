import unittest

from gui_do_demo import _MandelPresentationModel


class GuiDoDemoPresentationModelTests(unittest.TestCase):
    def test_status_text_updates_via_set_status(self) -> None:
        model = _MandelPresentationModel()

        model.set_status("Mandelbrot: running iterative")

        self.assertEqual(model.status_text.value, "Mandelbrot: running iterative")

    def test_observer_receives_status_updates_and_dispose_unsubscribes(self) -> None:
        model = _MandelPresentationModel()
        seen = []
        model.bind(model.status_text, lambda text: seen.append(text))

        model.set_status("Mandelbrot: running")
        model.dispose()
        model.set_status("Mandelbrot: complete")

        self.assertEqual(seen, ["Mandelbrot: running"])


if __name__ == "__main__":
    unittest.main()
