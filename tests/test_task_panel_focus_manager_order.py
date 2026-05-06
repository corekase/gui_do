import unittest

from gui_do.focus.task_panel_focus_manager import TaskPanelFocusManager


class _Node:
    def __init__(self, control_id: str, tab_index: int = -1):
        self.control_id = str(control_id)
        self.tab_index = int(tab_index)
        self.visible = True
        self.enabled = True
        self.parent = None

    def accepts_focus(self) -> bool:
        return True


class _Panel(_Node):
    def __init__(self, nodes):
        super().__init__("task_panel", tab_index=-1)
        self._nodes = list(nodes)
        for node in self._nodes:
            node.parent = self

    def find_descendants(self, predicate):
        return [node for node in self._nodes if predicate(node)]


class TestTaskPanelFocusManagerOrder(unittest.TestCase):
    def test_candidates_follow_explicit_tab_index_order(self):
        panel = _Panel(
            [
                _Node("exit", tab_index=0),
                _Node("showcase", tab_index=4),
                _Node("systems_toggle", tab_index=1),
                _Node("life_toggle", tab_index=2),
                _Node("mandel_toggle", tab_index=3),
            ]
        )

        manager = TaskPanelFocusManager()
        ordered = manager._candidate_controls(panel)

        self.assertEqual(
            ["exit", "systems_toggle", "life_toggle", "mandel_toggle", "showcase"],
            [node.control_id for node in ordered],
        )

    def test_unindexed_candidates_follow_indexed_candidates(self):
        panel = _Panel(
            [
                _Node("exit", tab_index=0),
                _Node("help", tab_index=-1),
                _Node("systems_toggle", tab_index=1),
            ]
        )

        manager = TaskPanelFocusManager()
        ordered = manager._candidate_controls(panel)

        self.assertEqual(
            ["exit", "systems_toggle", "help"],
            [node.control_id for node in ordered],
        )

    def test_excluded_controls_are_not_candidates(self):
        exit_button = _Node("exit", tab_index=0)
        help_button = _Node("help", tab_index=1)
        setattr(help_button, "task_panel_focus_excluded", True)
        systems_toggle = _Node("systems_toggle", tab_index=2)
        panel = _Panel([exit_button, help_button, systems_toggle])

        manager = TaskPanelFocusManager()
        ordered = manager._candidate_controls(panel)

        self.assertEqual(
            ["exit", "systems_toggle"],
            [node.control_id for node in ordered],
        )


if __name__ == "__main__":
    unittest.main()
