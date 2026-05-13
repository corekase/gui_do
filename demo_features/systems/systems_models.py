"""Data models for the systems demo feature package."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class _BacklogItem:
    title: str
    status: str
    priority: int
    owner: str


@dataclass
class _VirtualCell:
    index: int = -1


__all__ = [
    "_BacklogItem",
    "_VirtualCell",
]
