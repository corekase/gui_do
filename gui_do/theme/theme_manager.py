"""ThemeManager — named themes with design token resolution."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..core.presentation_model import ObservableValue

# Design token map: semantic name -> sRGB tuple (r, g, b) each 0-255.
TokenMap = Dict[str, Tuple[int, int, int]]

# ---------------------------------------------------------------------------
# Built-in token sets
# ---------------------------------------------------------------------------

_DARK_TOKENS: TokenMap = {
    "surface": (45, 45, 55),
    "surface-variant": (65, 65, 78),
    "primary": (90, 140, 210),
    "on-primary": (255, 255, 255),
    "secondary": (110, 175, 135),
    "on-secondary": (15, 20, 30),
    "error": (200, 65, 65),
    "on-error": (255, 255, 255),
    "outline": (110, 110, 135),
    "text": (215, 215, 230),
    "text-muted": (140, 140, 165),
    "accent": (130, 180, 240),
}

_LIGHT_TOKENS: TokenMap = {
    "surface": (240, 240, 248),
    "surface-variant": (220, 220, 232),
    "primary": (55, 105, 185),
    "on-primary": (255, 255, 255),
    "secondary": (60, 140, 95),
    "on-secondary": (255, 255, 255),
    "error": (185, 35, 35),
    "on-error": (255, 255, 255),
    "outline": (145, 145, 165),
    "text": (25, 25, 40),
    "text-muted": (95, 95, 120),
    "accent": (70, 130, 200),
}

_BUILT_IN_THEMES: Dict[str, TokenMap] = {
    "dark": _DARK_TOKENS,
    "light": _LIGHT_TOKENS,
}


class DesignTokens:
    """A named set of semantic color tokens for a theme.

    Each token is a human-readable name (``"primary"``, ``"surface"``, etc.)
    mapped to an sRGB 3-tuple ``(r, g, b)`` with components in ``0..255``.

    Usage::

        tokens = DesignTokens("dark", {"primary": (90, 140, 210)})
        color = tokens.get("primary")            # (90, 140, 210)
        color = tokens.get("missing", (0, 0, 0)) # fallback
    """

    def __init__(self, name: str, tokens: TokenMap) -> None:
        self.name = str(name)
        self._tokens: TokenMap = {str(k): tuple(v) for k, v in tokens.items()}  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Token access
    # ------------------------------------------------------------------

    def get(
        self,
        token: str,
        fallback: Tuple[int, int, int] = (128, 128, 128),
    ) -> Tuple[int, int, int]:
        """Resolve *token* to an sRGB tuple, returning *fallback* if unknown."""
        result = self._tokens.get(str(token))
        return result if result is not None else fallback

    def set(self, token: str, color: Tuple[int, int, int]) -> None:
        """Override or add a token value on this :class:`DesignTokens` object."""
        self._tokens[str(token)] = (int(color[0]), int(color[1]), int(color[2]))

    def token_names(self) -> List[str]:
        """Sorted list of all declared token names."""
        return sorted(self._tokens.keys())

    def to_dict(self) -> TokenMap:
        """Return a copy of the underlying token map."""
        return dict(self._tokens)

    def copy(self, new_name: str) -> "DesignTokens":
        """Return a new :class:`DesignTokens` instance with the same tokens."""
        return DesignTokens(str(new_name), dict(self._tokens))

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "DesignTokens":
        """Construct from a plain dict mapping token names to RGB sequences."""
        tokens: TokenMap = {}
        for k, v in data.items():
            try:
                r, g, b = int(v[0]), int(v[1]), int(v[2])
                tokens[str(k)] = (r, g, b)
            except (TypeError, IndexError, ValueError):
                pass
        return cls(str(name), tokens)

    def __repr__(self) -> str:  # pragma: no cover
        return f"DesignTokens(name={self.name!r}, tokens={len(self._tokens)})"


class ThemeManager:
    """Manages named themes and exposes the active :class:`DesignTokens` set.

    Both ``active_theme`` (the current theme name) and ``active_tokens`` (the
    resolved :class:`DesignTokens`) are :class:`ObservableValue` instances; any
    subscriber can react to theme switches immediately.

    Two built-in themes are always available: ``"dark"`` and ``"light"``.

    Usage::

        mgr = ThemeManager()
        mgr.active_tokens.subscribe(lambda _: my_canvas.invalidate())

        mgr.register_theme("contrast", {"primary": (255, 220, 0), ...})
        mgr.switch("contrast")

        color = mgr.token("primary")   # (255, 220, 0)
    """

    def __init__(self) -> None:
        self._themes: Dict[str, DesignTokens] = {}
        for name, tokens in _BUILT_IN_THEMES.items():
            self._themes[name] = DesignTokens(name, tokens)

        self.active_theme: ObservableValue[str] = ObservableValue("dark")
        self.active_tokens: ObservableValue[DesignTokens] = ObservableValue(
            self._themes["dark"]
        )

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_theme(
        self,
        name: str,
        tokens: "TokenMap | DesignTokens",
    ) -> None:
        """Register (or replace) a named theme.

        *tokens* may be either a plain ``dict`` or an existing
        :class:`DesignTokens` instance.
        """
        name = str(name).strip()
        if not name:
            raise ValueError("theme name must be a non-empty string")
        if isinstance(tokens, DesignTokens):
            self._themes[name] = tokens
        else:
            self._themes[name] = DesignTokens(name, dict(tokens))

    # ------------------------------------------------------------------
    # Activation
    # ------------------------------------------------------------------

    def switch(self, theme_name: str) -> bool:
        """Activate a registered theme by name.

        Returns ``True`` if the theme was found and activated, ``False``
        otherwise (theme not registered).  Subscribers of ``active_theme``
        and ``active_tokens`` are fired even when the same theme is re-applied.
        """
        name = str(theme_name).strip()
        tokens = self._themes.get(name)
        if tokens is None:
            return False
        self.active_theme.value = name
        self.active_tokens.value = tokens
        return True

    # ------------------------------------------------------------------
    # Token resolution
    # ------------------------------------------------------------------

    def token(
        self,
        name: str,
        fallback: Tuple[int, int, int] = (128, 128, 128),
    ) -> Tuple[int, int, int]:
        """Resolve a design token from the currently active theme."""
        return self.active_tokens.value.get(str(name), fallback)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def theme_names(self) -> List[str]:
        """Sorted list of all registered theme names (including built-ins)."""
        return sorted(self._themes.keys())

    def get_theme(self, name: str) -> Optional[DesignTokens]:
        """Return the :class:`DesignTokens` for *name*, or *None*."""
        return self._themes.get(str(name))

    def has_theme(self, name: str) -> bool:
        """Return True if a theme with the given name is registered."""
        return str(name) in self._themes
