"""FocusRing — composable modal focus trap with wrap-around and chaining.

A :class:`FocusRing` wraps a sequence of focusable node-ids and implements
Tab / Shift+Tab cycling within a bounded ring.  When ``trap=True`` the ring
never exits to an outer scope (modal dialog behaviour).  When ``wrap=True``
(default) Tab past the last node cycles back to the first; setting
``wrap=False`` lets Tab fall through to the parent ring.

Rings chain: each :class:`FocusRing` may have a ``parent`` ring.  When a
non-trapping ring reaches its boundary it delegates to the parent ring's
advance logic, enabling nested focus containment without coupling to the
global :class:`~gui_do.FocusManager` internals.

Usage::

    from gui_do import FocusRing

    # Modal dialog ring — Tab never leaves the dialog:
    dialog_ring = FocusRing(
        node_ids=["ok_button", "cancel_button", "text_input"],
        trap=True,
        wrap=True,
    )

    # Advance focus (Tab):
    next_id = dialog_ring.advance(current_id, forward=True)

    # Shift+Tab:
    prev_id = dialog_ring.advance(current_id, forward=False)

    # Open ring chained to a parent:
    panel_ring = FocusRing(["a", "b", "c"], wrap=False, parent=outer_ring)
    next_id = panel_ring.advance("c", forward=True)  # delegates to outer_ring

    # Check membership:
    dialog_ring.contains("ok_button")   # True

    # Dynamic updates (add/remove while open):
    dialog_ring.insert("new_field", after="text_input")
    dialog_ring.remove("cancel_button")
"""
from __future__ import annotations

from typing import Sequence


class FocusRing:
    """Bounded focus traversal ring with optional trap and chain semantics.

    Parameters
    ----------
    node_ids:
        Ordered sequence of focusable ``control_id`` strings.
    trap:
        When ``True`` Tab never escapes this ring (modal dialog).
    wrap:
        When ``True`` (default) cycling past the boundary wraps around.
        When ``False`` and no parent is set, boundary returns ``None``.
    parent:
        Optional parent :class:`FocusRing` to delegate boundary advances to.
    """

    def __init__(
        self,
        node_ids: Sequence[str],
        *,
        trap: bool = False,
        wrap: bool = True,
        parent: Optional["FocusRing"] = None,
    ) -> None:
        self._ids: List[str] = list(node_ids)
        self._index_by_id: dict[str, int] = {}
        self._rebuild_index()
        self.trap: bool = trap
        self.wrap: bool = wrap
        self.parent: Optional["FocusRing"] = parent

    def _rebuild_index(self) -> None:
        index: dict[str, int] = {}
        for i, node_id in enumerate(self._ids):
            # Match prior list.index behavior: first occurrence wins.
            index.setdefault(node_id, i)
        self._index_by_id = index

    # ------------------------------------------------------------------
    # Membership
    # ------------------------------------------------------------------

    def contains(self, node_id: str) -> bool:
        """Return True if *node_id* is in this ring."""
        return str(node_id) in self._index_by_id

    @property
    def node_ids(self) -> List[str]:
        """Current ordered list of node ids."""
        return list(self._ids)

    @property
    def size(self) -> int:
        return len(self._ids)

    def first(self) -> Optional[str]:
        """Return the first node id, or ``None`` if the ring is empty."""
        return self._ids[0] if self._ids else None

    def last(self) -> Optional[str]:
        """Return the last node id, or ``None`` if the ring is empty."""
        return self._ids[-1] if self._ids else None

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    def advance(self, current_id: Optional[str], *, forward: bool = True) -> Optional[str]:
        """Return the next node id in the traversal direction.

        Parameters
        ----------
        current_id:
            The currently focused node.  If ``None`` or not in this ring,
            returns the first (forward) or last (backward) node.
        forward:
            ``True`` for Tab (forward), ``False`` for Shift+Tab (backward).

        Returns ``None`` if the ring is empty or if traversal escapes a
        non-trapping, non-wrapping ring with no parent.
        """
        if not self._ids:
            return None

        if current_id is None:
            return self._ids[0] if forward else self._ids[-1]

        current_idx = self._index_by_id.get(str(current_id))
        if current_idx is None:
            return self._ids[0] if forward else self._ids[-1]

        n = len(self._ids)
        next_idx = current_idx + (1 if forward else -1)

        # At boundary
        if next_idx < 0 or next_idx >= n:
            if self.trap:
                # Wrap within this ring regardless of wrap flag
                return self._ids[0] if forward else self._ids[-1]
            if self.wrap:
                return self._ids[0] if forward else self._ids[-1]
            # Delegate to parent
            if self.parent is not None:
                return self.parent.advance(current_id, forward=forward)
            return None

        return self._ids[next_idx]

    def first_focusable(self) -> Optional[str]:
        """Return the first node id (entry point for initial focus)."""
        return self._ids[0] if self._ids else None

    # ------------------------------------------------------------------
    # Dynamic mutation
    # ------------------------------------------------------------------

    def append(self, node_id: str) -> None:
        """Append *node_id* to the end of the ring."""
        normalized = str(node_id)
        if normalized in self._index_by_id:
            return
        self._ids.append(normalized)
        self._index_by_id[normalized] = len(self._ids) - 1

    def insert(self, node_id: str, *, after: Optional[str] = None, before: Optional[str] = None) -> None:
        """Insert *node_id* relative to an existing id.

        If neither *after* nor *before* is given, appends to end.
        """
        node_id = str(node_id)
        if node_id in self._index_by_id:
            return
        after_key = None if after is None else str(after)
        before_key = None if before is None else str(before)
        if after_key is not None and after_key in self._index_by_id:
            idx = self._index_by_id[after_key]
            self._ids.insert(idx + 1, node_id)
        elif before_key is not None and before_key in self._index_by_id:
            idx = self._index_by_id[before_key]
            self._ids.insert(idx, node_id)
        else:
            self._ids.append(node_id)
        self._rebuild_index()

    def remove(self, node_id: str) -> bool:
        """Remove *node_id* from the ring.  Returns True if it was present."""
        normalized = str(node_id)
        idx = self._index_by_id.get(normalized)
        if idx is None:
            return False
        self._ids.pop(idx)
        self._rebuild_index()
        return True

    def clear(self) -> None:
        """Remove all node ids from the ring."""
        self._ids.clear()
        self._index_by_id.clear()

    def replace(self, node_ids: Sequence[str]) -> None:
        """Replace the entire ring contents with *node_ids*."""
        self._ids = list(node_ids)
        self._rebuild_index()
