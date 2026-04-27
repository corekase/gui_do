"""Thin pygame.scrap wrapper for clipboard operations."""
from __future__ import annotations


class ClipboardManager:
    """Wraps pygame.scrap with empty-string fallbacks for unavailable clipboard."""

    @staticmethod
    def copy(text: str) -> bool:
        """Copy text to clipboard. Returns False if unavailable."""
        try:
            import pygame
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8") + b"\x00")
            return True
        except Exception:
            return False

    @staticmethod
    def paste() -> str:
        """Paste text from clipboard. Returns "" if unavailable or empty."""
        try:
            import pygame
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            data = pygame.scrap.get(pygame.SCRAP_TEXT)
            if data is None:
                return ""
            # Strip null terminators that some platforms add
            text = data.decode("utf-8", errors="replace").rstrip("\x00")
            return text
        except Exception:
            return ""
