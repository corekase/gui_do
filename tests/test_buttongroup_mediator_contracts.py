import unittest

from gui.utility.intermediates.buttongroup_mediator import ButtonGroupMediator
from gui.utility.events import InteractiveState


class ButtonStub:
    def __init__(self, name: str) -> None:
        self.name = name
        self.state = InteractiveState.Idle


class ButtonGroupMediatorContractsBatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registered = set()
        self.mediator = ButtonGroupMediator(lambda button: button in self.registered)

    def test_get_selection_returns_none_for_unknown_group(self) -> None:
        self.assertIsNone(self.mediator.get_selection("missing"))

    def test_clear_resets_groups_and_selections(self) -> None:
        button = ButtonStub("a")
        self.registered.add(button)
        self.mediator.register("g", button)

        self.mediator.clear()

        self.assertEqual(self.mediator._groups, {})
        self.assertEqual(self.mediator._selections, {})

    def test_prune_drops_group_when_all_buttons_unregistered(self) -> None:
        button = ButtonStub("a")
        self.registered.add(button)
        self.mediator.register("g", button)

        self.registered.clear()
        selection = self.mediator.get_selection("g")

        self.assertIsNone(selection)
        self.assertNotIn("g", self.mediator._groups)
        self.assertNotIn("g", self.mediator._selections)

    def test_get_selection_arms_selected_and_unarms_others(self) -> None:
        a = ButtonStub("a")
        b = ButtonStub("b")
        self.registered.update([a, b])

        self.mediator.register("g", a)
        self.mediator.register("g", b)
        self.mediator.select("g", b)
        a.state = InteractiveState.Armed

        selection = self.mediator.get_selection("g")

        self.assertIs(selection, b)
        self.assertEqual(b.state, InteractiveState.Armed)
        self.assertEqual(a.state, InteractiveState.Idle)

    def test_register_preserves_existing_selection(self) -> None:
        a = ButtonStub("a")
        b = ButtonStub("b")
        c = ButtonStub("c")
        self.registered.update([a, b, c])

        self.mediator.register("g", a)
        self.mediator.register("g", b)
        self.mediator.select("g", b)
        self.mediator.register("g", c)

        selection = self.mediator.get_selection("g")

        self.assertIs(selection, b)


if __name__ == "__main__":
    unittest.main()
