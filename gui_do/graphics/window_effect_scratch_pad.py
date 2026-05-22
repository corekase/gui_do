from __future__ import annotations

import math
from typing import Optional

import pygame


class WindowEffectScratchPad:
    """Shared promoted scratch surfaces for window visual effects."""

    _surfaces: dict[str, pygame.Surface] = {}
    _sizes: dict[str, tuple[int, int]] = {}
    _refcount: int = 0

    @classmethod
    def acquire(cls) -> None:
        cls._refcount += 1

    @classmethod
    def release(cls, *, force: bool = False) -> None:
        if cls._refcount > 0:
            cls._refcount -= 1
        if not force and cls._refcount > 0:
            return
        cls.dispose_all()

    @classmethod
    def dispose_all(cls) -> None:
        old_surfaces = list(cls._surfaces.values())
        cls._surfaces = {}
        cls._sizes = {}
        cls._refcount = 0
        for surface in old_surfaces:
            del surface

    @classmethod
    def get_surface(cls, slot: str) -> Optional[pygame.Surface]:
        return cls._surfaces.get(str(slot))

    @classmethod
    def set_surface(cls, slot: str, surface: Optional[pygame.Surface]) -> None:
        key = str(slot)
        old_surface = cls._surfaces.get(key)
        if surface is None:
            cls._surfaces.pop(key, None)
            cls._sizes[key] = (0, 0)
            if old_surface is not None:
                del old_surface
            return
        cls._surfaces[key] = surface
        cls._sizes[key] = tuple(map(int, surface.get_size()))
        if old_surface is not None and old_surface is not surface:
            del old_surface

    @classmethod
    def get_size(cls, slot: str) -> tuple[int, int]:
        return cls._sizes.get(str(slot), (0, 0))

    @staticmethod
    def _surface_can_fit(capacity: tuple[int, int], needed: tuple[int, int]) -> bool:
        return capacity[0] >= needed[0] and capacity[1] >= needed[1]

    @staticmethod
    def _expanded_surface_size(needed: tuple[int, int], growth_factor: float) -> tuple[int, int]:
        growth = max(1.0, float(growth_factor))
        width = max(1, int(math.ceil(float(needed[0]) * growth)))
        height = max(1, int(math.ceil(float(needed[1]) * growth)))
        return width, height

    @classmethod
    def ensure_capacity(
        cls,
        slot: str,
        needed: tuple[int, int],
        *,
        growth_factor: float = 1.5,
    ) -> pygame.Surface:
        key = str(slot)
        required = (max(1, int(needed[0])), max(1, int(needed[1])))
        current = cls.get_surface(key)
        current_size = cls.get_size(key)
        if current is not None and cls._surface_can_fit(current_size, required):
            return current

        allocated = cls._expanded_surface_size(required, growth_factor)
        next_surface = pygame.Surface(allocated, pygame.SRCALPHA)
        old_surface = current
        cls._surfaces[key] = next_surface
        cls._sizes[key] = allocated
        if old_surface is not None:
            del old_surface
        return next_surface
