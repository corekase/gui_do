"""Tests for CommandHistory, CommandTransaction, Command from state.command_history."""
import unittest

from gui_do.state.command_history import CommandHistory, CommandTransaction


class _SimpleCommand:
    """A simple reversible command for testing."""
    def __init__(self, name, log):
        self._name = name
        self._log = log

    @property
    def description(self):
        return self._name

    def execute(self):
        self._log.append(f"+{self._name}")

    def undo(self):
        self._log.append(f"-{self._name}")


# ===========================================================================
# CommandTransaction
# ===========================================================================


class TestCommandTransaction(unittest.TestCase):
    def test_description_stored(self):
        tx = CommandTransaction("Batch")
        self.assertEqual("Batch", tx.description)

    def test_description_settable(self):
        tx = CommandTransaction("old")
        tx.description = "new"
        self.assertEqual("new", tx.description)

    def test_len_empty(self):
        tx = CommandTransaction()
        self.assertEqual(0, len(tx))

    def test_add_and_len(self):
        log = []
        tx = CommandTransaction()
        tx.add(_SimpleCommand("a", log))
        tx.add(_SimpleCommand("b", log))
        self.assertEqual(2, len(tx))

    def test_execute_runs_all(self):
        log = []
        tx = CommandTransaction("T")
        tx.add(_SimpleCommand("a", log))
        tx.add(_SimpleCommand("b", log))
        tx.execute()
        self.assertEqual(["+a", "+b"], log)

    def test_undo_runs_in_reverse(self):
        log = []
        tx = CommandTransaction("T")
        tx.add(_SimpleCommand("a", log))
        tx.add(_SimpleCommand("b", log))
        tx.execute()
        log.clear()
        tx.undo()
        self.assertEqual(["-b", "-a"], log)


# ===========================================================================
# CommandHistory — initial state
# ===========================================================================


class TestCommandHistoryInitial(unittest.TestCase):
    def test_can_undo_false(self):
        h = CommandHistory()
        self.assertFalse(h.can_undo)

    def test_can_redo_false(self):
        h = CommandHistory()
        self.assertFalse(h.can_redo)

    def test_undo_description_none(self):
        h = CommandHistory()
        self.assertIsNone(h.undo_description)

    def test_redo_description_none(self):
        h = CommandHistory()
        self.assertIsNone(h.redo_description)

    def test_undo_stack_size_zero(self):
        h = CommandHistory()
        self.assertEqual(0, h.undo_stack_size)


# ===========================================================================
# CommandHistory.push
# ===========================================================================


class TestCommandHistoryPush(unittest.TestCase):
    def test_push_executes_command(self):
        log = []
        h = CommandHistory()
        h.push(_SimpleCommand("a", log))
        self.assertEqual(["+a"], log)

    def test_push_enables_undo(self):
        h = CommandHistory()
        h.push(_SimpleCommand("a", []))
        self.assertTrue(h.can_undo)

    def test_push_sets_undo_description(self):
        h = CommandHistory()
        h.push(_SimpleCommand("my cmd", []))
        self.assertEqual("my cmd", h.undo_description)

    def test_push_clears_redo(self):
        log = []
        h = CommandHistory()
        h.push(_SimpleCommand("a", log))
        h.undo()
        h.push(_SimpleCommand("b", log))
        self.assertFalse(h.can_redo)

    def test_push_no_execute(self):
        log = []
        h = CommandHistory()
        h.push(_SimpleCommand("a", log), execute=False)
        self.assertEqual([], log)
        self.assertTrue(h.can_undo)


# ===========================================================================
# CommandHistory.undo / redo
# ===========================================================================


class TestCommandHistoryUndoRedo(unittest.TestCase):
    def test_undo_returns_true(self):
        h = CommandHistory()
        h.push(_SimpleCommand("a", []))
        self.assertTrue(h.undo())

    def test_undo_empty_returns_false(self):
        h = CommandHistory()
        self.assertFalse(h.undo())

    def test_undo_calls_command_undo(self):
        log = []
        h = CommandHistory()
        h.push(_SimpleCommand("a", log))
        log.clear()
        h.undo()
        self.assertEqual(["-a"], log)

    def test_undo_enables_redo(self):
        h = CommandHistory()
        h.push(_SimpleCommand("a", []))
        h.undo()
        self.assertTrue(h.can_redo)

    def test_redo_returns_true(self):
        h = CommandHistory()
        h.push(_SimpleCommand("a", []))
        h.undo()
        self.assertTrue(h.redo())

    def test_redo_empty_returns_false(self):
        h = CommandHistory()
        self.assertFalse(h.redo())

    def test_redo_calls_execute_again(self):
        log = []
        h = CommandHistory()
        h.push(_SimpleCommand("a", log))
        h.undo()
        log.clear()
        h.redo()
        self.assertEqual(["+a"], log)


# ===========================================================================
# CommandHistory transactions
# ===========================================================================


class TestCommandHistoryTransaction(unittest.TestCase):
    def test_transaction_context_manager(self):
        log = []
        h = CommandHistory()
        with h.transaction("Batch") as tx:
            tx.add(_SimpleCommand("a", log))
            tx.add(_SimpleCommand("b", log))
        # after context, transaction should be committed
        self.assertTrue(h.can_undo)

    def test_nested_transaction_raises(self):
        h = CommandHistory()
        h.begin_transaction("T1")
        with self.assertRaises(RuntimeError):
            h.begin_transaction("T2")
        h.end_transaction()

    def test_transaction_undo_reverses_all(self):
        log = []
        h = CommandHistory()
        with h.transaction("Batch") as tx:
            tx.add(_SimpleCommand("a", log))
            tx.add(_SimpleCommand("b", log))
        log.clear()
        h.undo()
        self.assertIn("-b", log)
        self.assertIn("-a", log)


if __name__ == "__main__":
    unittest.main()
