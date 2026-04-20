import unittest

from pygame import Rect

from gui.utility.intermediates.buttongroup_mediator import ButtonGroupMediator
from gui.utility.events import InteractiveState
from gui.utility.layout_manager import LayoutManager


class ButtonStub:
    def __init__(self, name: str) -> None:
        self.name = name
        self.state = InteractiveState.Idle


class LayoutManagerTests(unittest.TestCase):
    def test_get_cell_returns_rect_with_expected_geometry(self) -> None:
        layout = LayoutManager()
        layout.grid.set_properties(anchor=(10, 20), width=30, height=40, spacing=5, use_rect=True)

        cell = layout.grid.get_cell(2, 3)

        self.assertEqual(cell, Rect(80, 155, 30, 40))

    def test_get_cell_returns_point_when_use_rect_is_false(self) -> None:
        layout = LayoutManager()
        layout.grid.set_properties(anchor=(3, 4), width=10, height=8, spacing=2, use_rect=False)

        cell = layout.grid.get_cell(1, 2)

        self.assertEqual(cell, (15, 24))

    def test_set_properties_rejects_invalid_values(self) -> None:
        layout = LayoutManager()

        with self.assertRaises(ValueError):
            layout.grid.set_properties(anchor=(0, 0), width=0, height=10, spacing=1)
        with self.assertRaises(ValueError):
            layout.grid.set_properties(anchor=(0, 0), width=10, height=-1, spacing=1)
        with self.assertRaises(ValueError):
            layout.grid.set_properties(anchor=(0, 0), width=10, height=10, spacing=-1)
        with self.assertRaises(ValueError):
            layout.grid.set_properties(anchor=(0,), width=10, height=10, spacing=0)


class ButtonGroupMediatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registered = set()
        self.mediator = ButtonGroupMediator(lambda button: button in self.registered)

    def test_get_selection_prunes_unregistered_buttons(self) -> None:
        a = ButtonStub("a")
        b = ButtonStub("b")

        self.registered.update([a, b])
        self.mediator.register("g", a)
        self.mediator.register("g", b)
        self.mediator.select("g", b)

        self.registered.remove(b)
        selection = self.mediator.get_selection("g")

        self.assertIs(selection, a)
        self.assertEqual(a.state, InteractiveState.Armed)

    def test_select_sets_previous_selection_idle(self) -> None:
        a = ButtonStub("a")
        b = ButtonStub("b")

        self.registered.update([a, b])
        self.mediator.register("g", a)
        self.mediator.register("g", b)
        self.mediator.select("g", a)

        self.assertEqual(a.state, InteractiveState.Armed)

        self.mediator.select("g", b)

        self.assertEqual(a.state, InteractiveState.Idle)
        self.assertEqual(b.state, InteractiveState.Idle)

        selected = self.mediator.get_selection("g")

        self.assertIs(selected, b)
        self.assertEqual(b.state, InteractiveState.Armed)

    def test_select_ignores_unregistered_button(self) -> None:
        a = ButtonStub("a")
        b = ButtonStub("b")

        self.registered.add(a)
        self.mediator.register("g", a)

        self.mediator.select("g", b)

        self.assertIs(self.mediator.get_selection("g"), a)
        self.assertEqual(a.state, InteractiveState.Armed)

    def test_register_deduplicates_same_button(self) -> None:
        a = ButtonStub("a")
        self.registered.add(a)

        self.mediator.register("g", a)
        self.mediator.register("g", a)
        self.mediator.get_selection("g")

        self.assertEqual(len(self.mediator._groups["g"]), 1)


if __name__ == "__main__":
    unittest.main()
