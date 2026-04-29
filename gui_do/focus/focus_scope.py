"""FocusScopeManager — formal focus containment for modal UI subtrees.

A :class:`FocusScope` constrains Tab traversal to a declared subtree root.
While a scope is active, Tab cycles only among focusable descendants of that
root, preventing focus from escaping into background controls.

:class:`FocusScopeManager` manages a push/pop stack of scopes and
synchronises with the package :class:`~gui_do.FocusManager`'s internal
``_scope_stack`` so that existing focus traversal logic automatically
respects the active containment.

Typical usage is opening a modal overlay, dialog, or dropdown::

    scope_mgr = FocusScopeManager(app.focus_manager)

    # When opening a dialog:
    scope = scope_mgr.push(dialog_panel, scope_id="main-dialog")

    # When closing:
    scope_mgr.pop(scope)

    # Or pop the most recent scope:
    scope_mgr.pop_top()

Multiple scopes may be stacked.  The innermost (most-recently pushed) scope
is always the active one.
"""
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .focus_manager import FocusManager
    from ..controls.base.ui_node import UiNode


# ---------------------------------------------------------------------------
# FocusScope
# ---------------------------------------------------------------------------


class FocusScope:
    """A named focus-containment scope rooted at a :class:`~gui_do.UiNode`.

    Instances are created by :meth:`FocusScopeManager.push` and live until
    removed by :meth:`FocusScopeManager.pop`.

    Parameters
    ----------
    root:
        The :class:`~gui_do.UiNode` whose subtree constrains Tab traversal.
    scope_id:
        Human-readable identifier for debugging (default: auto-generated).
    """

    def __init__(self, root: "UiNode", scope_id: Optional[str] = None) -> None:
        self.root: "UiNode" = root
        self.scope_id: str = str(scope_id) if scope_id is not None else f"scope:{id(root):#x}"
        self._active: bool = False

    @property
    def active(self) -> bool:
        """True while this scope is registered in a :class:`FocusScopeManager`."""
        return self._active

    def __repr__(self) -> str:  # pragma: no cover
        return f"FocusScope(scope_id={self.scope_id!r}, active={self._active})"


# ---------------------------------------------------------------------------
# FocusScopeManager
# ---------------------------------------------------------------------------


class FocusScopeManager:
    """Stack-based manager for :class:`FocusScope` containment zones.

    When one or more scopes are active the innermost scope restricts Tab
    cycling to its subtree.  Popping the scope restores the previous
    containment level (or removes all constraints when the stack is empty).

    The manager synchronises with :class:`~gui_do.FocusManager` by mirroring
    the scope stack into ``FocusManager._scope_stack`` so that the existing
    Tab traversal loop automatically obeys the active containment without any
    changes to the FocusManager internals.

    Parameters
    ----------
    focus_manager:
        The application's :class:`~gui_do.FocusManager` instance.
    """

    def __init__(self, focus_manager: "FocusManager") -> None:
        self._fm = focus_manager
        self._stack: List[FocusScope] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def push(self, root: "UiNode", *, scope_id: Optional[str] = None) -> FocusScope:
        """Push a new scope rooted at *root* and return the handle.

        Parameters
        ----------
        root:
            Root node of the focus-containment subtree.
        scope_id:
            Optional human-readable label for debugging.

        Returns
        -------
        FocusScope
            Handle used with :meth:`pop` to remove the scope.
        """
        scope = FocusScope(root, scope_id=scope_id)
        scope._active = True
        self._stack.append(scope)
        self._sync()
        return scope

    def pop(self, scope: FocusScope) -> bool:
        """Remove *scope* from the stack (it need not be the topmost).

        Returns ``True`` if the scope was found and removed, ``False`` if it
        was not registered.
        """
        scope._active = False
        try:
            self._stack.remove(scope)
        except ValueError:
            return False
        self._sync()
        return True

    def pop_top(self) -> Optional[FocusScope]:
        """Pop and return the innermost (most recently pushed) scope.

        Returns ``None`` if the stack is empty.
        """
        if not self._stack:
            return None
        scope = self._stack.pop()
        scope._active = False
        self._sync()
        return scope

    def pop_all(self) -> None:
        """Remove all active scopes and restore unconstrained Tab traversal."""
        for scope in self._stack:
            scope._active = False
        self._stack.clear()
        self._sync()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    @property
    def active_scope(self) -> Optional[FocusScope]:
        """The innermost active scope, or ``None`` if no scopes are active."""
        return self._stack[-1] if self._stack else None

    @property
    def depth(self) -> int:
        """Number of scopes currently on the stack."""
        return len(self._stack)

    @property
    def is_constrained(self) -> bool:
        """True when at least one scope is active."""
        return bool(self._stack)

    # ------------------------------------------------------------------
    # FocusManager synchronisation
    # ------------------------------------------------------------------

    def _sync(self) -> None:
        """Mirror the scope-root stack into ``FocusManager._scope_stack``."""
        roots = [s.root for s in self._stack]
        fm_stack: list = self._fm._scope_stack
        fm_stack.clear()
        fm_stack.extend(roots)
