"""CommandHistory — undo/redo stack with optional transaction grouping."""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable


@runtime_checkable
class Command(Protocol):
    """Protocol that all undoable commands must satisfy."""

    @property
    def description(self) -> str:
        """Human-readable description of this command."""
        ...

    def execute(self) -> None:
        """Perform the command."""
        ...

    def undo(self) -> None:
        """Reverse the effects of :meth:`execute`."""
        ...


class CommandTransaction:
    """Groups multiple :class:`Command` objects into a single atomic unit.

    All constituent commands are executed and undone as one operation.
    """

    def __init__(self, description: str = "Transaction") -> None:
        self._description: str = description
        self._commands: List[Command] = []

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value

    def add(self, command: Command) -> None:
        """Append a command to this transaction."""
        self._commands.append(command)

    def execute(self) -> None:
        """Execute all commands in insertion order."""
        for cmd in self._commands:
            cmd.execute()

    def undo(self) -> None:
        """Undo all commands in reverse insertion order."""
        for cmd in reversed(self._commands):
            cmd.undo()

    def __len__(self) -> int:
        return len(self._commands)


class CommandHistory:
    """Bounded undo/redo stack for :class:`Command` objects.

    Typical usage::

        history = CommandHistory(max_size=100)

        # Simple command
        history.push(my_command)

        # Transaction
        with history.transaction("Bulk edit") as tx:
            tx.add(cmd_a)
            tx.add(cmd_b)

        history.undo()
        history.redo()
    """

    def __init__(self, max_size: int = 100) -> None:
        self._max_size: int = max(1, int(max_size))
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._open_transaction: Optional[CommandTransaction] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        """True when there is at least one operation to undo."""
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        """True when there is at least one operation to redo."""
        return bool(self._redo_stack)

    @property
    def undo_description(self) -> Optional[str]:
        """Description of the next undo operation, or None."""
        return self._undo_stack[-1].description if self._undo_stack else None

    @property
    def redo_description(self) -> Optional[str]:
        """Description of the next redo operation, or None."""
        return self._redo_stack[-1].description if self._redo_stack else None

    @property
    def undo_stack_size(self) -> int:
        return len(self._undo_stack)

    @property
    def redo_stack_size(self) -> int:
        return len(self._redo_stack)

    # ------------------------------------------------------------------
    # Command push
    # ------------------------------------------------------------------

    def push(self, command: Command, *, execute: bool = True) -> None:
        """Add *command* to the history, optionally executing it first.

        If a transaction is open the command is added to the transaction
        instead and will *not* be executed immediately (the transaction
        executes everything at commit time).

        Any pending redo history is discarded.
        """
        if self._open_transaction is not None:
            self._open_transaction.add(command)
            if execute:
                try:
                    command.execute()
                except Exception:
                    pass
            return

        if execute:
            try:
                command.execute()
            except Exception:
                return

        self._redo_stack.clear()
        self._undo_stack.append(command)
        if len(self._undo_stack) > self._max_size:
            self._undo_stack.pop(0)

    # ------------------------------------------------------------------
    # Undo / redo
    # ------------------------------------------------------------------

    def undo(self) -> bool:
        """Undo the most recent operation.  Returns True on success."""
        if not self._undo_stack:
            return False
        command = self._undo_stack.pop()
        try:
            command.undo()
        except Exception:
            return False
        self._redo_stack.append(command)
        return True

    def redo(self) -> bool:
        """Redo the most recently undone operation.  Returns True on success."""
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        try:
            command.execute()
        except Exception:
            return False
        self._undo_stack.append(command)
        return True

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    def begin_transaction(self, description: str = "Transaction") -> CommandTransaction:
        """Start a new transaction.  Commands pushed while open go into it.

        Call :meth:`end_transaction` (or use the context manager) to commit.
        """
        if self._open_transaction is not None:
            raise RuntimeError("A transaction is already open.")
        self._open_transaction = CommandTransaction(description)
        return self._open_transaction

    def end_transaction(self) -> None:
        """Commit the open transaction onto the undo stack."""
        if self._open_transaction is None:
            raise RuntimeError("No transaction is open.")
        tx = self._open_transaction
        self._open_transaction = None
        # Only record non-empty transactions
        if len(tx) > 0:
            self._redo_stack.clear()
            self._undo_stack.append(tx)
            if len(self._undo_stack) > self._max_size:
                self._undo_stack.pop(0)

    def abort_transaction(self) -> None:
        """Discard the open transaction without recording it."""
        if self._open_transaction is None:
            raise RuntimeError("No transaction is open.")
        self._open_transaction = None

    class _TransactionContext:
        def __init__(self, history: "CommandHistory", description: str) -> None:
            self._history = history
            self._tx = history.begin_transaction(description)
            self._committed = False

        @property
        def transaction(self) -> CommandTransaction:
            return self._tx

        def __enter__(self) -> CommandTransaction:
            return self._tx

        def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
            if exc_type is None:
                self._history.end_transaction()
            else:
                self._history.abort_transaction()
            return False

    def transaction(self, description: str = "Transaction") -> "_TransactionContext":
        """Context manager that wraps :meth:`begin_transaction` / :meth:`end_transaction`.

        Example::

            with history.transaction("Rename") as tx:
                tx.add(some_cmd)
        """
        return self._TransactionContext(self, description)

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Discard all undo and redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._open_transaction = None
