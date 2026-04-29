"""AssetRegistry — shared surface and font cache with reference counting.

All controls that load images or font surfaces use :class:`AssetRegistry`
rather than loading privately.  Duplicate loads are detected by
``(path, size)`` / ``(path, size, flags)`` keys so the same bitmap is never
decoded twice per process.

Portable hot-reload is supported via :meth:`check_hot_reload`: the registry
compares each asset's file ``mtime`` against the cached value.  If the file
has changed the asset is evicted from cache so the next access reloads it.
This uses only ``os.stat`` — no OS-specific file-watching APIs.

Usage::

    from gui_do import AssetRegistry

    registry = AssetRegistry(base_path="assets/data")

    # Load a surface (cached on subsequent calls with same key):
    surf = registry.get_surface("icons/play.png", size=(32, 32))

    # Load scaled to a different size — separate cache slot:
    surf2 = registry.get_surface("icons/play.png", size=(16, 16))

    # Release a reference (auto-evicts when count reaches 0):
    registry.release_surface("icons/play.png", size=(32, 32))

    # Per-frame hot-reload check (dev mode):
    if dev_mode:
        reloaded = registry.check_hot_reload()
        if reloaded:
            all_controls_invalidate()

    # Diagnostics:
    info = registry.stats()
    print(info)  # {"surfaces": 4, "fonts": 2, "total_bytes": 102400}
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


# Key types
_SurfaceKey = Tuple[str, Optional[Tuple[int, int]]]  # (path, size_or_None)
_FontKey = Tuple[str, int, int]                        # (path, size_px, flags)


class _SurfaceEntry:
    __slots__ = ("surface", "refs", "mtime", "path")

    def __init__(self, surface: "pygame.Surface", path: str, mtime: float) -> None:
        self.surface = surface
        self.refs: int = 1
        self.mtime: float = mtime
        self.path: str = path


class _FontEntry:
    __slots__ = ("font", "refs", "mtime", "path")

    def __init__(self, font: object, path: str, mtime: float) -> None:
        self.font = font
        self.refs: int = 1
        self.mtime: float = mtime
        self.path: str = path


class AssetRegistry:
    """Shared surface and font cache with reference counting and optional hot-reload.

    Parameters
    ----------
    base_path:
        Root directory for relative asset paths.  ``None`` means paths are
        resolved relative to the current working directory.
    enable_hot_reload:
        When ``True``, :meth:`check_hot_reload` compares file mtimes and
        evicts stale cache entries automatically.
    """

    def __init__(
        self,
        base_path: "Optional[str | Path]" = None,
        *,
        enable_hot_reload: bool = False,
    ) -> None:
        self._base: Optional[Path] = Path(base_path) if base_path is not None else None
        self._hot_reload: bool = enable_hot_reload
        self._surfaces: Dict[_SurfaceKey, _SurfaceEntry] = {}
        self._fonts: Dict[_FontKey, _FontEntry] = {}

    # ------------------------------------------------------------------
    # Path resolution
    # ------------------------------------------------------------------

    def _resolve(self, rel_path: str) -> Path:
        p = Path(rel_path)
        if p.is_absolute():
            return p
        if self._base is not None:
            return self._base / p
        return Path(rel_path)

    def _mtime(self, path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    # ------------------------------------------------------------------
    # Surface cache
    # ------------------------------------------------------------------

    def get_surface(
        self,
        path: str,
        *,
        size: Optional[Tuple[int, int]] = None,
        convert_alpha: bool = True,
    ) -> "pygame.Surface":
        """Return a (possibly cached) ``pygame.Surface`` loaded from *path*.

        Parameters
        ----------
        path:
            Asset path (relative to ``base_path`` or absolute).
        size:
            If given, scale the loaded surface to ``(width, height)``.
            Each ``(path, size)`` combination is a separate cache slot.
        convert_alpha:
            Use ``convert_alpha()`` for per-pixel alpha blending (default).
        """
        import pygame

        key: _SurfaceKey = (str(path), size)
        entry = self._surfaces.get(key)
        if entry is not None:
            entry.refs += 1
            return entry.surface

        full_path = self._resolve(str(path))
        mtime = self._mtime(full_path)
        surf: pygame.Surface = pygame.image.load(str(full_path))
        if convert_alpha:
            try:
                surf = surf.convert_alpha()
            except Exception:
                pass
        if size is not None:
            surf = pygame.transform.smoothscale(surf, size)

        self._surfaces[key] = _SurfaceEntry(surf, str(full_path), mtime)
        return surf

    def release_surface(self, path: str, *, size: Optional[Tuple[int, int]] = None) -> None:
        """Decrement the reference count for a surface; evict when it reaches 0."""
        key: _SurfaceKey = (str(path), size)
        entry = self._surfaces.get(key)
        if entry is None:
            return
        entry.refs -= 1
        if entry.refs <= 0:
            del self._surfaces[key]

    def has_surface(self, path: str, *, size: Optional[Tuple[int, int]] = None) -> bool:
        """True if a surface is currently cached for this key."""
        return (str(path), size) in self._surfaces

    # ------------------------------------------------------------------
    # Font cache
    # ------------------------------------------------------------------

    def get_font(
        self,
        path: str,
        size_px: int,
        *,
        bold: bool = False,
        italic: bool = False,
    ) -> "pygame.font.Font":
        """Return a (possibly cached) ``pygame.font.Font`` for *path* at *size_px*."""
        import pygame

        flags = (int(bold) << 1) | int(italic)
        key: _FontKey = (str(path), int(size_px), flags)
        entry = self._fonts.get(key)
        if entry is not None:
            entry.refs += 1
            return entry.font  # type: ignore[return-value]

        full_path = self._resolve(str(path))
        mtime = self._mtime(full_path)
        font = pygame.font.Font(str(full_path), int(size_px))
        if bold:
            font.set_bold(True)
        if italic:
            font.set_italic(True)

        self._fonts[key] = _FontEntry(font, str(full_path), mtime)
        return font

    def release_font(self, path: str, size_px: int, *, bold: bool = False, italic: bool = False) -> None:
        """Decrement font reference count; evict when it reaches 0."""
        flags = (int(bold) << 1) | int(italic)
        key: _FontKey = (str(path), int(size_px), flags)
        entry = self._fonts.get(key)
        if entry is None:
            return
        entry.refs -= 1
        if entry.refs <= 0:
            del self._fonts[key]

    # ------------------------------------------------------------------
    # Hot-reload
    # ------------------------------------------------------------------

    def check_hot_reload(self) -> bool:
        """Check all cached assets for file mtime changes.

        Evicts any asset whose source file has been modified since it was
        loaded.  Returns ``True`` if any asset was evicted (caller should
        trigger a full scene invalidation).
        """
        if not self._hot_reload:
            return False

        evicted = False

        stale_surf_keys: List[_SurfaceKey] = []
        for key, entry in self._surfaces.items():
            current_mtime = self._mtime(Path(entry.path))
            if current_mtime and current_mtime != entry.mtime:
                stale_surf_keys.append(key)
        for key in stale_surf_keys:
            del self._surfaces[key]
            evicted = True

        stale_font_keys: List[_FontKey] = []
        for key, entry in self._fonts.items():
            current_mtime = self._mtime(Path(entry.path))
            if current_mtime and current_mtime != entry.mtime:
                stale_font_keys.append(key)
        for key in stale_font_keys:
            del self._fonts[key]
            evicted = True

        return evicted

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return a dict with cache sizes and approximate memory usage."""
        total_bytes = 0
        for entry in self._surfaces.values():
            try:
                total_bytes += entry.surface.get_bytesize() * entry.surface.get_width() * entry.surface.get_height()
            except Exception:
                pass
        return {
            "surfaces": len(self._surfaces),
            "fonts": len(self._fonts),
            "total_bytes": total_bytes,
        }

    def clear(self) -> None:
        """Evict all cached assets (regardless of reference counts)."""
        self._surfaces.clear()
        self._fonts.clear()
