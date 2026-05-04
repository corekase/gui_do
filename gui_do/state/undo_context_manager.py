"""UndoContextManager — named multi-stack undo/redo context routing.

Maintains a registry of named :class:`~gui_do.CommandHistory` stacks and
routes undo/redo operations to whichever stack is currently active.

This is the thin composition layer on top of the existing
:class:`~gui_do.CommandHistory` that makes multi-document, multi-panel, and
multi-modal applications correct: a global ``Ctrl+Z`` action routes to the
active document's history, not always the same stack.

Usage::

    from gui_do import UndoContextManager, CommandHistory

    canvas_history = CommandHistory(max_size=50)
    props_history  = CommandHistory(max_size=20)

    undo_mgr = UndoContextManager()
    undo_mgr.register("canvas", canvas_history)
    undo_mgr.register("props",  props_history)

    # Activate based on focus:
    undo_mgr.set_active("canvas")

    # Undo routes to canvas_history:
    undo_mgr.undo()   # equivalent to canvas_history.undo()
    undo_mgr.redo()

    # Switch to props context:
    undo_mgr.set_active("props")
    undo_mgr.undo()   # routes to props_history

    # Query the active stack:
    print(undo_mgr.can_undo)  # True/False
    print(undo_mgr.can_redo)

    # Observe context switches:
    unsub = undo_mgr.subscribe_context_change(
        lambda key: status_bar.set_undo_context(key)
    )

    # Unregister a context when its document is closed:
    undo_mgr.unregister("canvas")

    # Access any stack directly:
    history = undo_mgr.get("canvas")
    history.push(my_command)
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..state.command_history import CommandHistory


# ---------------------------------------------------------------------------
# UndoContextManager
# ---------------------------------------------------------------------------


class UndoContextManager:
    """Routes undo/redo to the active named :class:`~gui_do.CommandHistory`.

    Parameters
    ----------
    default_key:
        When set, :meth:`set_active` is automatically called with this key
        after the first :meth:`register` call for that key.
    """

    def __init__(self, *, default_key: Optional[str] = None) -> None:
        self._stacks: Dict[str, "CommandHistory"] = {}
        self._active_key: Optional[str] = None
        self._default_key = default_key
        self._subscribers: List[Callable[[Optional[str]], None]] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self, key: str, history: "CommandHistory", *, make_active: bool = False
    ) -> None:
        """Register *history* under *key*.

        Parameters
        ----------
        key:
            String identifier for this stack.
        history:
            The :class:`~gui_do.CommandHistory` to register.
        make_active:
            When ``True``, immediately activate this key.
        """
        self._stacks[str(key)] = history
        if make_active or (self._default_key == key and self._active_key is None):
            self.set_active(key)

    def unregister(self, key: str) -> bool:
        """Remove *key* from the registry.

        If *key* was active, the active context is set to ``None``.

        Returns ``True`` if the key existed.
        """
        key = str(key)
        existed = self._stacks.pop(key, None) is not None
        if existed and self._active_key == key:
            self._active_key = None
            self._notify()
        return existed

    # ------------------------------------------------------------------
    # Activation
    # ------------------------------------------------------------------

    def set_active(self, key: Optional[str]) -> None:
        """Activate the stack identified by *key*.

        Passing ``None`` deactivates all contexts (undo/redo becomes no-op).

        Raises :class:`KeyError` if *key* is not registered (and not ``None``).
        """
        if key is not None:
            key = str(key)
            if key not in self._stacks:
                raise KeyError(f"UndoContextManager: unknown context key {key!r}")
        if self._active_key != key:
            self._active_key = key
            self._notify()

    @property
    def active_key(self) -> Optional[str]:
        """The currently active context key, or ``None``."""
        return self._active_key

    @property
    def active(self) -> Optional["CommandHistory"]:
        """The currently active :class:`~gui_do.CommandHistory`, or ``None``."""
        if self._active_key is None:
            return None
        return self._stacks.get(self._active_key)

    # ------------------------------------------------------------------
    # Undo/redo
    # ------------------------------------------------------------------

    def undo(self) -> bool:
        """Undo the top command in the active stack.

        Returns ``True`` if an undo was performed.
        """
        stack = self.active
        if stack is None or not stack.can_undo:
            return False
        stack.undo()
        return True

    def redo(self) -> bool:
        """Redo the next command in the active stack.

        Returns ``True`` if a redo was performed.
        """
        stack = self.active
        if stack is None or not stack.can_redo:
            return False
        stack.redo()
        return True

    @property
    def can_undo(self) -> bool:
        """``True`` if the active stack has commands that can be undone."""
        stack = self.active
        return stack is not None and stack.can_undo

    @property
    def can_redo(self) -> bool:
        """``True`` if the active stack has commands that can be redone."""
        stack = self.active
        return stack is not None and stack.can_redo

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional["CommandHistory"]:
        """Return the :class:`~gui_do.CommandHistory` for *key*, or ``None``."""
        return self._stacks.get(str(key))

    def registered_keys(self) -> List[str]:
        """Sorted list of all registered context keys."""
        return sorted(self._stacks.keys())

    def __len__(self) -> int:
        return len(self._stacks)

    def __contains__(self, key: str) -> bool:
        return str(key) in self._stacks

    # ------------------------------------------------------------------
    # Observers
    # ------------------------------------------------------------------

    def subscribe_context_change(
        self, callback: Callable[[Optional[str]], None]
    ) -> Callable[[], None]:
        """Register *callback* to be notified when the active key changes.

        *callback* receives the new active key (or ``None`` if deactivated).
        Returns an unsubscribe callable.
        """
        self._subscribers.append(callback)

        def _unsub() -> None:
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass

        return _unsub

    def _notify(self) -> None:
        for cb in tuple(self._subscribers):
            try:
                cb(self._active_key)
            except Exception:
                pass
