"""ListDiffCalculator — minimal-edit list reconciliation (Myers algorithm).

Computes the minimal sequence of insert, remove, and move operations needed
to transform one list into another.  Useful for animating list view updates
and for reactive data binding.

Usage::

    from gui_do import ListDiffCalculator, ListDiff, DiffInsert, DiffRemove, DiffMove

    old = ["a", "b", "c", "d"]
    new = ["b", "c", "e", "d"]

    diff = ListDiffCalculator.diff(old, new)
    # diff.removes → [DiffRemove(index=0, item="a")]
    # diff.inserts → [DiffInsert(index=2, item="e")]
    # diff.moves   → []

    # With a key function (for object lists):
    diff = ListDiffCalculator.diff(old_items, new_items, key_fn=lambda x: x.id)

    # Apply a diff to a mutable list:
    ListDiffCalculator.apply_to_list(target, diff)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Optional


# ---------------------------------------------------------------------------
# Diff result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiffInsert:
    """A new item inserted at *index* in the new list."""
    index: int
    item: Any


@dataclass(frozen=True)
class DiffRemove:
    """An item removed from *index* in the old list."""
    index: int
    item: Any


@dataclass(frozen=True)
class DiffMove:
    """An item moved from *from_index* to *to_index*."""
    from_index: int
    to_index: int
    item: Any


@dataclass
class ListDiff:
    """The result of a :func:`ListDiffCalculator.diff` computation.

    Attributes
    ----------
    inserts:
        Items inserted (not present in old list).
    removes:
        Items removed (not present in new list).
    moves:
        Items that exist in both lists but at different positions.
    """
    inserts: List[DiffInsert]
    removes: List[DiffRemove]
    moves: List[DiffMove]

    @property
    def is_empty(self) -> bool:
        """``True`` when the two lists are identical (no ops)."""
        return not self.inserts and not self.removes and not self.moves


# ---------------------------------------------------------------------------
# ListDiffCalculator
# ---------------------------------------------------------------------------


class ListDiffCalculator:
    """Computes minimal-edit diffs between two lists.

    All methods are static/class methods — no instance is needed.
    """

    @staticmethod
    def diff(
        old_list: List,
        new_list: List,
        *,
        key_fn: Optional[Callable[[Any], Any]] = None,
    ) -> ListDiff:
        """Compute the diff between *old_list* and *new_list*.

        Parameters
        ----------
        old_list:
            The original list.
        new_list:
            The target list.
        key_fn:
            Optional function to extract a comparable key from each item.
            Defaults to the item itself (requires items to be hashable/comparable).

        Returns
        -------
        ListDiff
            Minimal set of insert, remove, and move operations.
        """
        if key_fn is None:
            key_fn = lambda x: x  # noqa: E731

        old_keys = [key_fn(x) for x in old_list]
        new_keys = [key_fn(x) for x in new_list]

        # Compute LCS (Longest Common Subsequence) of keys
        lcs = _lcs(old_keys, new_keys)

        # Build sets for fast lookup
        lcs_set_old = set(lcs)   # keys in LCS

        inserts: List[DiffInsert] = []
        removes: List[DiffRemove] = []
        moves: List[DiffMove] = []

        # Items removed from old (not in new at all)
        new_key_set = set(new_keys)
        for i, item in enumerate(old_list):
            k = old_keys[i]
            if k not in new_key_set:
                removes.append(DiffRemove(index=i, item=item))

        # Items inserted into new (not in old at all)
        old_key_set = set(old_keys)
        for j, item in enumerate(new_list):
            k = new_keys[j]
            if k not in old_key_set:
                inserts.append(DiffInsert(index=j, item=item))

        # Items that exist in both but moved
        old_index_map = {k: i for i, k in enumerate(old_keys)}
        for j, item in enumerate(new_list):
            k = new_keys[j]
            if k in old_index_map:
                old_i = old_index_map[k]
                if k not in lcs_set_old and old_i != j:
                    moves.append(DiffMove(from_index=old_i, to_index=j, item=item))

        return ListDiff(inserts=inserts, removes=removes, moves=moves)

    @staticmethod
    def apply_to_list(target: List, diff: ListDiff) -> None:
        """Apply *diff* to *target* in-place to make it match the new list.

        The operations are applied in a stable order:
        1. Removes (highest index first to preserve indices).
        2. Inserts (lowest index first).
        3. Moves.

        Parameters
        ----------
        target:
            The mutable list to transform.
        diff:
            The diff to apply.
        """
        # Removes — apply in reverse index order
        for rem in sorted(diff.removes, key=lambda r: -r.index):
            if 0 <= rem.index < len(target):
                target.pop(rem.index)

        # Inserts — apply in index order
        for ins in sorted(diff.inserts, key=lambda i: i.index):
            idx = min(ins.index, len(target))
            target.insert(idx, ins.item)

        # Moves
        for mv in diff.moves:
            from_i = mv.from_index
            to_i = mv.to_index
            if 0 <= from_i < len(target):
                item = target.pop(from_i)
                to_i = min(to_i, len(target))
                target.insert(to_i, item)


# ---------------------------------------------------------------------------
# LCS helper (hunt-szymanski style via DP for clarity)
# ---------------------------------------------------------------------------


def _lcs(a: List, b: List) -> List:
    """Return the Longest Common Subsequence of keys *a* and *b*."""
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return []

    # Build DP table
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la - 1, -1, -1):
        for j in range(lb - 1, -1, -1):
            if a[i] == b[j]:
                dp[i][j] = dp[i + 1][j + 1] + 1
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])

    # Traceback
    result = []
    i, j = 0, 0
    while i < la and j < lb:
        if a[i] == b[j]:
            result.append(a[i])
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    return result
