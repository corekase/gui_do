"""FontRoleRegistry — define font roles once, apply them to any scene.

A :class:`FontRoleRegistry` collects font role definitions (name, size,
typeface, weight) during application startup and registers them with the
:class:`~gui_do.GuiApplication` for any scene on demand.

Usage pattern
-------------
1. **Configure once** — typically in ``__init__`` before scene construction::

    from gui_do import FontRoleRegistry

    registry = FontRoleRegistry()
    registry.define("body",    size=16, file_path="fonts/Ubuntu-B.ttf")
    registry.define("title",   size=14, file_path="fonts/Ubuntu-B.ttf", bold=True)
    registry.define("display", size=72, file_path="fonts/Gimbot.ttf")

2. **Apply to a scene** — one call registers all roles for that scene::

    registry.apply(app, scene_name="main")
    registry.apply(app, scene_name="settings")

3. **Reference by name** — controls use the role name string directly::

    button = ButtonControl("ok", rect, "OK", font_role=registry["body"])
    # or equivalently:
    button = ButtonControl("ok", rect, "OK", font_role=registry.role("body"))

Features and scenes that receive a host with a ``font_roles`` attribute follow
the same pattern — call ``host.font_roles.apply(app, scene_name=...)`` in
``build()`` and then pass ``host.font_roles["body"]`` wherever a ``font_role``
parameter is expected.

:class:`FontRoleRegistry` is chainable: ``define()`` returns ``self``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


@dataclass(frozen=True)
class FontRoleDef:
    """Immutable definition of a single font role."""

    role_name: str
    size: int
    file_path: Optional[str] = None
    system_name: Optional[str] = None
    bold: bool = False
    italic: bool = False


class FontRoleRegistry:
    """Cross-scene font role registry.

    Define all font roles during application startup, then apply them to any
    scene with a single :meth:`apply` call.  Role names can be retrieved via
    :meth:`role` or ``__getitem__`` for use as ``font_role=`` arguments.
    """

    def __init__(self) -> None:
        self._defs: Dict[str, FontRoleDef] = {}
        self._order: List[str] = []

    # ------------------------------------------------------------------
    # Configuration API
    # ------------------------------------------------------------------

    def define(
        self,
        role_name: str,
        *,
        size: int,
        file_path: Optional[str] = None,
        system_name: Optional[str] = None,
        bold: bool = False,
        italic: bool = False,
    ) -> "FontRoleRegistry":
        """Add or replace a font role definition.

        Returns *self* so calls can be chained::

            registry.define("body", size=16).define("title", size=14, bold=True)

        Parameters
        ----------
        role_name:
            The role name string passed to controls as ``font_role=``.
        size:
            Point size.
        file_path:
            Path to a ``.ttf`` / ``.otf`` font file, relative to the process
            working directory or absolute.  Takes priority over *system_name*.
        system_name:
            Pygame system font name (fallback when *file_path* is ``None``).
        bold:
            Request bold weight from a system font.
        italic:
            Request italic style from a system font.
        """
        name = str(role_name).strip()
        if not name:
            raise ValueError("role_name must be a non-empty string")
        defn = FontRoleDef(
            role_name=name,
            size=max(1, int(size)),
            file_path=file_path,
            system_name=system_name,
            bold=bool(bold),
            italic=bool(italic),
        )
        if name not in self._defs:
            self._order.append(name)
        self._defs[name] = defn
        return self

    # ------------------------------------------------------------------
    # Application API
    # ------------------------------------------------------------------

    def apply(
        self,
        app,
        *,
        scene_name: Optional[str] = None,
        names: Optional[Sequence[str]] = None,
    ) -> None:
        """Register all defined roles (or a named subset) with *app*.

        Parameters
        ----------
        app:
            A :class:`~gui_do.GuiApplication` instance.
        scene_name:
            Scene to register the roles in.  ``None`` targets the currently
            active scene (same semantics as ``app.register_font_role``).
        names:
            If given, only these role names are applied.  Useful when a scene
            needs only a subset of the registry.
        """
        target_names: Sequence[str]
        if names is None:
            target_names = self._order
        else:
            target_names = list(names)

        for name in target_names:
            defn = self._defs.get(name)
            if defn is None:
                raise KeyError(f"FontRoleRegistry: unknown role {name!r}")
            app.register_font_role(
                defn.role_name,
                size=defn.size,
                file_path=defn.file_path,
                system_name=defn.system_name,
                bold=defn.bold,
                italic=defn.italic,
                scene_name=scene_name,
            )

    # ------------------------------------------------------------------
    # Lookup API
    # ------------------------------------------------------------------

    def role(self, role_name: str) -> str:
        """Return *role_name* after confirming it has been defined.

        Raises :class:`KeyError` for unknown names so typos fail fast at
        build time rather than silently falling back to the default font.
        """
        name = str(role_name)
        if name not in self._defs:
            raise KeyError(f"FontRoleRegistry: unknown role {name!r}")
        return self._defs[name].role_name

    def __getitem__(self, role_name: str) -> str:
        """Shorthand for :meth:`role`; enables ``registry["body"]``."""
        return self.role(role_name)

    def defined_names(self) -> tuple[str, ...]:
        """Return all defined role names in definition order."""
        return tuple(self._order)

    def __contains__(self, role_name: object) -> bool:
        return str(role_name) in self._defs

    def __len__(self) -> int:
        return len(self._defs)
