"""Tests for CommandHistory — undo/redo with transactions."""
import unittest

from gui_do.core.command_history import CommandHistory, Command, CommandTransaction


class _AddCmd:
    """Simple test command that appends to a log."""

    def __init__(self, log: list, value: str) -> None:
        self._log = log
        self._value = value

    @property
    def description(self) -> str:
        return f"Add {self._value}"

    def execute(self) -> None:
        self._log.append(self._value)

    def undo(self) -> None:
        if self._value in self._log:
            self._log.remove(self._value)


class _FailCmd:
    """Command whose execute() raises."""

    @property
    def description(self) -> str:
        return "Fail"

    def execute(self) -> None:
        raise RuntimeError("Boom")

    def undo(self) -> None:
        pass


class TestCommandProtocol(unittest.TestCase):
    def test_concrete_class_satisfies_protocol(self) -> None:
        log: list = []
        cmd = _AddCmd(log, "x")
        self.assertIsInstance(cmd, Command)

    def test_execute_runs_action(self) -> None:
        log: list = []
        cmd = _AddCmd(log, "x")
        cmd.execute()
        self.assertIn("x", log)

    def test_undo_reverses_action(self) -> None:
        log = ["x"]
        cmd = _AddCmd(log, "x")
        cmd.undo()
        self.assertNotIn("x", log)


class TestCommandHistoryPush(unittest.TestCase):
    def test_push_executes_command(self) -> None:
        log: list = []
        h = CommandHistory()
        h.push(_AddCmd(log, "a"))
        self.assertIn("a", log)

    def test_push_without_execute(self) -> None:
        log: list = []
        h = CommandHistory()
        cmd = _AddCmd(log, "a")
        h.push(cmd, execute=False)
        self.assertNotIn("a", log)
        self.assertTrue(h.can_undo)

    def test_push_failed_execute_not_added_to_stack(self) -> None:
        h = CommandHistory()
        h.push(_FailCmd())
        self.assertFalse(h.can_undo)

    def test_push_clears_redo_stack(self) -> None:
        log: list = []
        h = CommandHistory()
        h.push(_AddCmd(log, "a"))
        h.undo()
        self.assertTrue(h.can_redo)
        h.push(_AddCmd(log, "b"))
        self.assertFalse(h.can_redo)


class TestCommandHistoryUndoRedo(unittest.TestCase):
    def test_undo_reverses_last(self) -> None:
        log: list = []
        h = CommandHistory()
        h.push(_AddCmd(log, "a"))
        h.undo()
        self.assertNotIn("a", log)

    def test_undo_returns_true_on_success(self) -> None:
        log: list = []
        h = CommandHistory()
        h.push(_AddCmd(log, "a"))
        self.assertTrue(h.undo())

    def test_undo_returns_false_when_empty(self) -> None:
        h = CommandHistory()
        self.assertFalse(h.undo())

    def test_redo_reapplies_undone(self) -> None:
        log: list = []
        h = CommandHistory()
        h.push(_AddCmd(log, "a"))
        h.undo()
        h.redo()
        self.assertIn("a", log)

    def test_redo_returns_true_on_success(self) -> None:
        log: list = []
        h = CommandHistory()
        h.push(_AddCmd(log, "a"))
        h.undo()
        self.assertTrue(h.redo())

    def test_redo_returns_false_when_empty(self) -> None:
        h = CommandHistory()
        self.assertFalse(h.redo())

    def test_multiple_undo_redo_cycle(self) -> None:
        log: list = []
        h = CommandHistory()
        h.push(_AddCmd(log, "a"))
        h.push(_AddCmd(log, "b"))
        h.undo()
        h.undo()
        self.assertEqual(log, [])
        h.redo()
        h.redo()
        self.assertIn("a", log)
        self.assertIn("b", log)


class TestCommandHistoryDescriptions(unittest.TestCase):
    def test_undo_description(self) -> None:
        log: list = []
        h = CommandHistory()
        h.push(_AddCmd(log, "x"))
        self.assertEqual(h.undo_description, "Add x")

    def test_redo_description_after_undo(self) -> None:
        log: list = []
        h = CommandHistory()
        h.push(_AddCmd(log, "x"))
        h.undo()
        self.assertEqual(h.redo_description, "Add x")

    def test_none_descriptions_when_stacks_empty(self) -> None:
        h = CommandHistory()
        self.assertIsNone(h.undo_description)
        self.assertIsNone(h.redo_description)


class TestCommandHistoryMaxSize(unittest.TestCase):
    def test_max_size_trims_oldest(self) -> None:
        log: list = []
        h = CommandHistory(max_size=2)
        h.push(_AddCmd(log, "a"))
        h.push(_AddCmd(log, "b"))
        h.push(_AddCmd(log, "c"))
        self.assertEqual(h.undo_stack_size, 2)


class TestCommandHistoryClear(unittest.TestCase):
    def test_clear_empties_undo_and_redo(self) -> None:
        log: list = []
        h = CommandHistory()
        h.push(_AddCmd(log, "a"))
        h.undo()
        h.clear()
        self.assertFalse(h.can_undo)
        self.assertFalse(h.can_redo)


class TestCommandTransaction(unittest.TestCase):
    def test_transaction_executes_all_commands(self) -> None:
        log: list = []
        tx = CommandTransaction("batch")
        tx.add(_AddCmd(log, "a"))
        tx.add(_AddCmd(log, "b"))
        tx.execute()
        self.assertIn("a", log)
        self.assertIn("b", log)

    def test_transaction_undo_reverses_all(self) -> None:
        log = ["a", "b"]
        tx = CommandTransaction("batch")
        tx.add(_AddCmd(log, "a"))
        tx.add(_AddCmd(log, "b"))
        tx.undo()
        self.assertNotIn("a", log)
        self.assertNotIn("b", log)

    def test_transaction_undo_in_reverse_order(self) -> None:
        order: list = []
        class _TrackCmd:
            def __init__(self, label):
                self._label = label
            @property
            def description(self): return self._label
            def execute(self): order.append(f"do:{self._label}")
            def undo(self): order.append(f"undo:{self._label}")

        tx = CommandTransaction("ordered")
        tx.add(_TrackCmd("x"))
        tx.add(_TrackCmd("y"))
        tx.undo()
        self.assertEqual(order, ["undo:y", "undo:x"])

    def test_transaction_length(self) -> None:
        tx = CommandTransaction()
        log: list = []
        tx.add(_AddCmd(log, "a"))
        tx.add(_AddCmd(log, "b"))
        self.assertEqual(len(tx), 2)

    def test_empty_transaction_not_pushed_to_history(self) -> None:
        h = CommandHistory()
        with h.transaction("empty"):
            pass  # nothing added
        self.assertFalse(h.can_undo)


class TestCommandHistoryBeginEndTransaction(unittest.TestCase):
    def test_begin_end_transaction_commits(self) -> None:
        log: list = []
        h = CommandHistory()
        h.begin_transaction("T")
        h.push(_AddCmd(log, "a"))
        h.push(_AddCmd(log, "b"))
        h.end_transaction()
        self.assertTrue(h.can_undo)
        self.assertEqual(h.undo_description, "T")

    def test_abort_transaction_discards(self) -> None:
        log: list = []
        h = CommandHistory()
        h.begin_transaction("T")
        h.push(_AddCmd(log, "a"))
        h.abort_transaction()
        self.assertFalse(h.can_undo)

    def test_begin_while_open_raises(self) -> None:
        h = CommandHistory()
        h.begin_transaction("T1")
        with self.assertRaises(RuntimeError):
            h.begin_transaction("T2")
        h.abort_transaction()

    def test_end_without_begin_raises(self) -> None:
        h = CommandHistory()
        with self.assertRaises(RuntimeError):
            h.end_transaction()


class TestCommandHistoryContextManager(unittest.TestCase):
    def test_context_manager_commits_on_success(self) -> None:
        log: list = []
        h = CommandHistory()
        with h.transaction("C") as tx:
            tx.add(_AddCmd(log, "a"))
        self.assertTrue(h.can_undo)

    def test_context_manager_aborts_on_exception(self) -> None:
        log: list = []
        h = CommandHistory()
        try:
            with h.transaction("C") as tx:
                tx.add(_AddCmd(log, "a"))
                raise ValueError("test error")
        except ValueError:
            pass
        self.assertFalse(h.can_undo)

    def test_transaction_undo_reverses_entire_group(self) -> None:
        log: list = []
        h = CommandHistory()
        with h.transaction("Group") as tx:
            tx.add(_AddCmd(log, "a"))
            tx.add(_AddCmd(log, "b"))
        h.undo()
        self.assertNotIn("a", log)
        self.assertNotIn("b", log)


if __name__ == "__main__":
    unittest.main()
