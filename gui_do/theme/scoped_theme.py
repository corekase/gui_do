"""ScopedTheme — per-subtree design-token overrides for theme inheritance.

:class:`ScopedTheme` holds a set of token overrides that apply to a declared
UI subtree without changing the global theme.  :class:`ScopedThemeManager`
manages a push/pop stack so that controls rendering their children can
temporarily activate a different token context.

Usage::

    from gui_do import ScopedTheme, ScopedThemeManager

    # Create a "dark sidebar" scope:
    dark_sidebar = ScopedTheme(
        {"surface": (20, 20, 30), "text": (230, 230, 240)},
        name="dark-sidebar",
    )

    scope_mgr = ScopedThemeManager(app.theme.active_tokens)

    # During sidebar draw:
    with scope_mgr.scope(dark_sidebar):
        color = scope_mgr.resolve("surface")   # → (20, 20, 30)
        color = scope_mgr.resolve("primary")   # → falls through to global tokens

    # Or manual push/pop:
    scope_mgr.push(dark_sidebar)
    color = scope_mgr.resolve("text")
    scope_mgr.pop()

Scope chain
-----------
Token resolution climbs the scope chain:
    innermost scope → parent scope → … → global DesignTokens

Only explicitly overridden names differ from the outer layer.  All other
names pass through unchanged to the global theme.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..theme.theme_manager import DesignTokens


# ---------------------------------------------------------------------------
# ScopedTheme
# ---------------------------------------------------------------------------


class ScopedTheme:
    """A set of design-token overrides for a UI subtree.

    Parameters
    ----------
    overrides:
        Mapping of token name → ``(r, g, b)`` tuple (each 0-255).
    name:
        Human-readable label for debugging (default ``"scoped"``).
    """

    def __init__(
        self,
        overrides: Optional[Dict[str, Tuple[int, int, int]]] = None,
        *,
        name: str = "scoped",
    ) -> None:
        self._name: str = str(name)
        self._overrides: Dict[str, Tuple[int, int, int]] = {}
        if overrides:
            for k, v in overrides.items():
                self._overrides[str(k)] = (int(v[0]), int(v[1]), int(v[2]))
        # Set by ScopedThemeManager on push/pop.
        self._parent: Optional["ScopedTheme"] = None

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Human-readable scope label."""
        return self._name

    @property
    def parent(self) -> Optional["ScopedTheme"]:
        """Parent scope in the chain, or ``None`` for the root scope."""
        return self._parent

    # ------------------------------------------------------------------
    # Token access
    # ------------------------------------------------------------------

    def set(self, token: str, color: Tuple[int, int, int]) -> None:
        """Add or override a single token in this scope."""
        self._overrides[str(token)] = (int(color[0]), int(color[1]), int(color[2]))

    def remove(self, token: str) -> None:
        """Remove a token override, letting it fall through to the parent."""
        self._overrides.pop(str(token), None)

    def resolve(
        self,
        token: str,
        fallback: Optional[Tuple[int, int, int]] = None,
    ) -> Optional[Tuple[int, int, int]]:
        """Resolve *token* through the scope chain.

        Returns the override from the nearest scope that declares the token,
        or *fallback* if no scope in the chain declares it.
        """
        v = self._overrides.get(str(token))
        if v is not None:
            return v
        if self._parent is not None:
            return self._parent.resolve(token, fallback)
        return fallback

    def to_dict(self) -> Dict[str, Tuple[int, int, int]]:
        """Return a copy of this scope's override map (parent not included)."""
        return dict(self._overrides)

    def copy(self, *, name: str = "copy") -> "ScopedTheme":
        """Return a new :class:`ScopedTheme` with the same overrides."""
        return ScopedTheme(dict(self._overrides), name=name)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ScopedTheme(name={self._name!r}, overrides={len(self._overrides)})"


# ---------------------------------------------------------------------------
# ScopedThemeManager
# ---------------------------------------------------------------------------


class ScopedThemeManager:
    """Manages a push/pop stack of :class:`ScopedTheme` objects.

    Token resolution during a draw pass climbs the scope chain then falls
    through to the global :class:`~gui_do.DesignTokens` base.

    Parameters
    ----------
    base_tokens:
        The global :class:`~gui_do.DesignTokens` used as the final fallback.
    """

    def __init__(self, base_tokens: "DesignTokens") -> None:
        self._base = base_tokens
        self._stack: List[ScopedTheme] = []

    # ------------------------------------------------------------------
    # Stack API
    # ------------------------------------------------------------------

    def push(self, scoped: ScopedTheme) -> None:
        """Push *scoped* onto the scope stack.

        Sets *scoped*'s parent to the current top scope (or ``None`` if the
        stack is empty), so the chain resolves correctly.
        """
        scoped._parent = self._stack[-1] if self._stack else None
        self._stack.append(scoped)

    def pop(self) -> Optional[ScopedTheme]:
        """Pop and return the innermost scope.  Returns ``None`` if empty."""
        if not self._stack:
            return None
        scope = self._stack.pop()
        scope._parent = None
        return scope

    @property
    def active_scope(self) -> Optional[ScopedTheme]:
        """The innermost active scope, or ``None`` if none are pushed."""
        return self._stack[-1] if self._stack else None

    @property
    def depth(self) -> int:
        """Number of scopes currently on the stack."""
        return len(self._stack)

    # ------------------------------------------------------------------
    # Token resolution
    # ------------------------------------------------------------------

    def resolve(
        self,
        token: str,
        fallback: Tuple[int, int, int] = (128, 128, 128),
    ) -> Tuple[int, int, int]:
        """Resolve *token* through the scope chain then the global base tokens.

        Parameters
        ----------
        token:
            Semantic token name (e.g. ``"primary"``, ``"surface"``).
        fallback:
            Returned when the token is not found anywhere in the chain.
        """
        if self._stack:
            v = self._stack[-1].resolve(token, fallback=None)
            if v is not None:
                return v
        return self._base.get(token, fallback)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def scope(self, scoped: ScopedTheme) -> "_ScopeContext":
        """Return a context manager that pushes/pops *scoped*.

        Usage::

            with scope_mgr.scope(dark_tokens):
                draw_subtree(scope_mgr)
        """
        return _ScopeContext(self, scoped)


class _ScopeContext:
    """Context manager returned by :meth:`ScopedThemeManager.scope`."""

    def __init__(self, manager: ScopedThemeManager, scoped: ScopedTheme) -> None:
        self._mgr = manager
        self._scope = scoped

    def __enter__(self) -> ScopedTheme:
        self._mgr.push(self._scope)
        return self._scope

    def __exit__(self, *_: object) -> None:
        self._mgr.pop()
