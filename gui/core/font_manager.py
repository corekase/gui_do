from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Optional

import pygame

from .first_frame_profiler import first_frame_profiler
from shared.error_handling import logical_error, report_nonfatal_error


@dataclass(frozen=True)
class _FontRole:
    name: str
    size: int
    file_path: Optional[str]
    system_name: Optional[str]
    bold: bool
    italic: bool


class _FontInstance:
    """Bound view over a resolved role/font size with measurement helpers."""

    def __init__(self, role: _FontRole, font: pygame.font.Font, size: int) -> None:
        self._role = role
        self._font = font
        self._size = int(size)

    @property
    def role_name(self) -> str:
        return self._role.name

    @property
    def point_size(self) -> int:
        return self._size

    @property
    def line_height(self) -> int:
        return int(self._font.get_height())

    def text_size(self, text: str) -> tuple[int, int]:
        return self._font.size(str(text))

    def text_surface_size(self, text: str, *, shadow: bool = False, shadow_offset: tuple[int, int] = (1, 1)) -> tuple[int, int]:
        width, height = self.text_size(text)
        if not shadow:
            return int(width), int(height)
        offset_x = max(0, int(shadow_offset[0]))
        offset_y = max(0, int(shadow_offset[1]))
        return int(width + offset_x), int(height + offset_y)


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
        self._reported_load_failures: set[tuple[str, int, str]] = set()
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
            raise logical_error(
                "role_name must be a non-empty string",
                subsystem="gui.fonts",
                operation="FontManager.register_role",
                exc_type=ValueError,
                details={"role_name": role_name},
                source_skip_frames=1,
            )

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

        load_start = perf_counter()
        loaded: Optional[pygame.font.Font] = None
        if role.file_path is not None:
            try:
                loaded = pygame.font.Font(role.file_path, resolved_size)
            except Exception as exc:
                self._report_load_failure_once(role.name, resolved_size, "file", exc, source=role.file_path)
                loaded = None
        if loaded is None and role.system_name is not None:
            try:
                loaded = pygame.font.SysFont(role.system_name, resolved_size, bold=role.bold, italic=role.italic)
            except Exception as exc:
                self._report_load_failure_once(role.name, resolved_size, "system", exc, source=role.system_name)
                loaded = None
        if loaded is None:
            loaded = pygame.font.Font(None, resolved_size)

        self._font_cache[cache_key] = loaded
        elapsed_ms = (perf_counter() - load_start) * 1000.0
        source = role.file_path or role.system_name or "pygame-default"
        first_frame_profiler().record_once(
            "font.load",
            f"{role.name}:{resolved_size}",
            elapsed_ms,
            detail=f"source={source}",
        )
        return loaded

    def font_instance(self, role_name: str, *, size: Optional[int] = None) -> _FontInstance:
        role = self._resolve_role(role_name)
        resolved_size = role.size if size is None else max(1, int(size))
        font = self.get_font(role.name, size=resolved_size)
        return _FontInstance(role=role, font=font, size=resolved_size)

    def render_text(self, text: str, color, *, role_name: str, size: Optional[int] = None) -> pygame.Surface:
        timer = first_frame_profiler().time_once(
            "text.render",
            f"{role_name}:{size if size is not None else 'default'}",
            detail=f"shadow=False chars={len(str(text))}",
        )
        font = self.get_font(role_name, size=size)
        rendered = font.render(str(text), True, color)
        timer()
        return rendered

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
        timer = first_frame_profiler().time_once(
            "text.render",
            f"{role_name}:{size if size is not None else 'default'}:shadow",
            detail=f"shadow=True chars={len(str(text))}",
        )
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
        timer()
        return out

    def _resolve_role(self, role_name: str) -> _FontRole:
        role = self._roles.get(str(role_name))
        if role is None:
            raise logical_error(
                f"unknown font role: {role_name!r}",
                subsystem="gui.fonts",
                operation="FontManager._resolve_role",
                exc_type=ValueError,
                details={"role_name": role_name},
                source_skip_frames=1,
            )
        return role

    def _report_load_failure_once(self, role_name: str, size: int, source_type: str, exc: BaseException, *, source: str) -> None:
        key = (str(role_name), int(size), str(source_type))
        if key in self._reported_load_failures:
            return
        self._reported_load_failures.add(key)
        report_nonfatal_error(
            "failed to load configured font; falling back to a default font",
            kind="io",
            subsystem="gui.fonts",
            operation="FontManager.get_font",
            cause=exc,
            path=source,
            details={"role": role_name, "size": int(size), "source_type": source_type},
            source_skip_frames=1,
        )

    def _drop_role_cache(self, role_name: str) -> None:
        doomed = [key for key in self._font_cache.keys() if key[0] == role_name]
        for key in doomed:
            self._font_cache.pop(key, None)
