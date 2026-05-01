import unittest

from gui_do_demo import GuiDoDemo


class _StubControl:
    def __init__(self, name: str):
        self.name = str(name)
        self.tab_indices = []
        self.accessibility_calls = []

    def set_tab_index(self, index: int):
        self.tab_indices.append(int(index))

    def set_accessibility(self, *, role: str, label: str):
        self.accessibility_calls.append((str(role), str(label)))


class _StubBinding:
    def __init__(
        self,
        *,
        key: str,
        toggle_attr: str | None,
        accessibility_label: str | None,
        action_label: str | None,
        task_panel_slot_index: int | None,
        tab_before_showcase: bool,
    ):
        self.key = str(key)
        self.toggle_attr = toggle_attr
        self.accessibility_label = accessibility_label
        self.action_label = action_label
        self.task_panel_slot_index = task_panel_slot_index
        self.tab_before_showcase = bool(tab_before_showcase)


class _StubWindowPresentation:
    def __init__(self, bindings):
        self._bindings = list(bindings)

    def bindings(self):
        return tuple(self._bindings)


class TestDemoAccessibilitySpecs(unittest.TestCase):
    def _make_demo(self):
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.exit_button = _StubControl("exit")
        demo.showcase_button = _StubControl("showcase")
        demo.systems_toggle_window = _StubControl("systems")
        demo.life_toggle_window = _StubControl("life")
        demo.mandel_toggle_window = _StubControl("mandel")
        demo.window_presentation = _StubWindowPresentation(
            [
                _StubBinding(
                    key="systems",
                    toggle_attr="systems_toggle_window",
                    accessibility_label="Show Systems window",
                    action_label="Show Systems Window",
                    task_panel_slot_index=1,
                    tab_before_showcase=True,
                ),
                _StubBinding(
                    key="life",
                    toggle_attr="life_toggle_window",
                    accessibility_label="Show Life window",
                    action_label="Show Life Window",
                    task_panel_slot_index=3,
                    tab_before_showcase=False,
                ),
                _StubBinding(
                    key="mandel",
                    toggle_attr="mandel_toggle_window",
                    accessibility_label="Show Mandelbrot window",
                    action_label="Show Mandelbrot Window",
                    task_panel_slot_index=4,
                    tab_before_showcase=False,
                ),
            ]
        )
        return demo

    def test_tab_order_places_showcase_after_first_toggle(self):
        demo = self._make_demo()

        toggles = demo._collect_window_toggle_controls()
        self.assertEqual(
            ["systems", "life", "mandel"],
            [binding.key for binding, _control in toggles],
        )
        ordered = demo._build_main_tab_order_controls(toggles)

        self.assertEqual(
            [demo.exit_button, demo.systems_toggle_window, demo.showcase_button, demo.life_toggle_window, demo.mandel_toggle_window],
            ordered,
        )
        self.assertEqual([0], demo.exit_button.tab_indices)
        self.assertEqual([1], demo.systems_toggle_window.tab_indices)
        self.assertEqual([2], demo.showcase_button.tab_indices)
        self.assertEqual([3], demo.life_toggle_window.tab_indices)
        self.assertEqual([4], demo.mandel_toggle_window.tab_indices)

    def test_accessibility_applies_static_and_toggle_labels(self):
        demo = self._make_demo()
        ordered = [demo.exit_button, demo.systems_toggle_window, demo.showcase_button]

        demo._apply_main_accessibility(ordered)

        self.assertEqual([("button", "Exit")], demo.exit_button.accessibility_calls)
        self.assertEqual([("button", "Showcase")], demo.showcase_button.accessibility_calls)
        self.assertEqual([("toggle", "Show Systems window")], demo.systems_toggle_window.accessibility_calls)
        self.assertEqual([("toggle", "Show Life window")], demo.life_toggle_window.accessibility_calls)
        self.assertEqual([("toggle", "Show Mandelbrot window")], demo.mandel_toggle_window.accessibility_calls)


if __name__ == "__main__":
    unittest.main()
