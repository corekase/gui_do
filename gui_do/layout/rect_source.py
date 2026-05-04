"""Composable rect-source helpers for nested layout composition.

Layout engines can accept either a concrete ``pygame.Rect`` or a dynamic rect
source (for example another layout manager's computed slot).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, Union, runtime_checkable

from pygame import Rect


@runtime_checkable
class SupportsLayoutRect(Protocol):
    """Protocol for objects that can resolve themselves to a rect."""

    def resolve_layout_rect(self) -> Rect:
        ...


RectSource = Union[Rect, SupportsLayoutRect, Callable[[], Rect], object]


def resolve_rect(source: RectSource) -> Rect:
    """Resolve *source* into a defensive copy of ``pygame.Rect``.

    Accepted forms:
    - ``Rect``
    - objects implementing ``resolve_layout_rect()``
    - zero-arg callables returning ``Rect``
    - objects exposing a ``rect`` attribute
    """
    if isinstance(source, Rect):
        return Rect(source)

    resolver = getattr(source, "resolve_layout_rect", None)
    if callable(resolver):
        return Rect(resolver())

    if callable(source):
        return Rect(source())

    rect_attr = getattr(source, "rect", None)
    if isinstance(rect_attr, Rect):
        return Rect(rect_attr)

    raise TypeError(
        "Rect source must be a Rect, callable returning Rect, object with "
        "resolve_layout_rect(), or object exposing .rect"
    )


@dataclass(frozen=True)
class LayoutRect:
    """Lazy rect provider for nested layout composition."""

    _resolver: Callable[[], Rect]

    @classmethod
    def from_source(cls, source: RectSource) -> "LayoutRect":
        return cls(lambda: resolve_rect(source))

    def resolve_layout_rect(self) -> Rect:
        return Rect(self._resolver())

    def inset(self, padding: int | tuple[int, int] | tuple[int, int, int, int]) -> "LayoutRect":
        left, top, right, bottom = _normalize_padding(padding)

        def _resolve() -> Rect:
            base = self.resolve_layout_rect()
            return Rect(
                base.left + left,
                base.top + top,
                max(1, base.width - left - right),
                max(1, base.height - top - bottom),
            )

        return LayoutRect(_resolve)


def _normalize_padding(
    padding: int | tuple[int, int] | tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    if isinstance(padding, int):
        p = max(0, int(padding))
        return p, p, p, p
    if len(padding) == 2:
        x = max(0, int(padding[0]))
        y = max(0, int(padding[1]))
        return x, y, x, y
    if len(padding) == 4:
        return tuple(max(0, int(part)) for part in padding)
    raise ValueError("padding must be int, (x,y), or (l,t,r,b)")
