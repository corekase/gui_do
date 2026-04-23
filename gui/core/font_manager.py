from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pygame


@dataclass(frozen=True)
class _FontRole:
    name: str
    size: int
    file_path: Optional[str]
    system_name: Optional[str]
    bold: bool
    italic: bool


class FontManager:
    """Role-based font registry and cache.

    Roles map a named purpose (``"body"``, ``"title"``, ``"display"``) to a
    specific typeface and size.  Call :meth:`register_role` to create or update
    a role definition; the revision counter increments so that any control that
    caches rendered bitmaps can detect the change and rebuild.
    """

    def __init__(self, resource_root: Optional[Path] = None) -> None:
        self._resource_root = None if resource_root is None else Path(resource_root)
        self._roles: dict[str, _FontRole] = {}
        self._role_order: list[str] = []
        self._font_cache: dict[tuple[str, int], pygame.font.Font] = {}
        self._revision = 0

    @property
    def revision(self) -> int:
        return self._revision

    def role_names(self) -> tuple[str, ...]:
        return tuple(self._role_order)

    def has_role(self, role_name: str) -> bool:
        return str(role_name) in self._roles

    def register_role(
        self,
        role_name: str,
        *,
        size: int,
        file_path: Optional[str] = None,
        system_name: Optional[str] = None,
        bold: bool = False,
        italic: bool = False,
    ) -> None:
        """Create or update a font role definition.

        Calling this with an existing ``role_name`` reconfigures that role
        (e.g. to switch the typeface or size used for ``"body"`` text).  The
        font cache for that role is dropped and the revision counter increments.
        """
        normalized_name = str(role_name).strip()
        if not normalized_name:
            raise ValueError("role_name must be a non-empty string")

        normalized_size = max(1, int(size))
        resolved_path: Optional[str] = None
        if file_path is not None:
            candidate = Path(file_path)
            if not candidate.is_absolute() and self._resource_root is not None:
                candidate = self._resource_root / candidate
            resolved_path = str(candidate)

        role = _FontRole(
            name=normalized_name,
            size=normalized_size,
            file_path=resolved_path,
            system_name=None if system_name is None else str(system_name),
            bold=bool(bold),
            italic=bool(italic),
        )
        if normalized_name not in self._roles:
            self._role_order.append(normalized_name)
        self._roles[normalized_name] = role
        self._drop_role_cache(normalized_name)
        self._revision += 1

    def get_font(self, role_name: str, *, size: Optional[int] = None) -> pygame.font.Font:
        role = self._resolve_role(role_name)
        resolved_size = role.size if size is None else max(1, int(size))
        cache_key = (role.name, resolved_size)
        cached = self._font_cache.get(cache_key)
        if cached is not None:
            return cached

        if not pygame.font.get_init():
            pygame.font.init()

        loaded: Optional[pygame.font.Font] = None
        if role.file_path is not None:
            try:
                loaded = pygame.font.Font(role.file_path, resolved_size)
            except Exception:
                loaded = None
        if loaded is None and role.system_name is not None:
            try:
                loaded = pygame.font.SysFont(role.system_name, resolved_size, bold=role.bold, italic=role.italic)
            except Exception:
                loaded = None
        if loaded is None:
            loaded = pygame.font.Font(None, resolved_size)

        self._font_cache[cache_key] = loaded
        return loaded

    def render_text(self, text: str, color, *, role_name: str, size: Optional[int] = None) -> pygame.Surface:
        font = self.get_font(role_name, size=size)
        return font.render(str(text), True, color)

    def render_text_with_shadow(
        self,
        text: str,
        color,
        shadow_color,
        *,
        role_name: str,
        size: Optional[int] = None,
        shadow_offset: tuple[int, int] = (1, 1),
    ) -> pygame.Surface:
        font = self.get_font(role_name, size=size)
        text_bitmap = font.render(str(text), True, color)
        shadow_bitmap = font.render(str(text), True, shadow_color)
        offset_x = int(shadow_offset[0])
        offset_y = int(shadow_offset[1])
        out = pygame.Surface(
            (
                text_bitmap.get_width() + max(0, offset_x),
                text_bitmap.get_height() + max(0, offset_y),
            ),
            pygame.SRCALPHA,
        )
        out.blit(shadow_bitmap, (max(0, offset_x), max(0, offset_y)))
        out.blit(text_bitmap, (0, 0))
        return out

    def _resolve_role(self, role_name: str) -> _FontRole:
        role = self._roles.get(str(role_name))
        if role is None:
            raise ValueError(f"unknown font role: {role_name!r}")
        return role

    def _drop_role_cache(self, role_name: str) -> None:
        doomed = [key for key in self._font_cache.keys() if key[0] == role_name]
        for key in doomed:
            self._font_cache.pop(key, None)
