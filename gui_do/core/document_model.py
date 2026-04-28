"""Document model — tracked content, revision, and persistence lifecycle."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .command_history import CommandHistory


DocumentLoader = Callable[[Path], Any]
DocumentSaver = Callable[[Path, Any], None]


@dataclass(slots=True)
class DocumentModel:
    """Generic document state container for editor-style applications."""

    document_id: str
    content: Any = None
    path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    revision: int = 0
    saved_revision: int = 0

    @property
    def is_dirty(self) -> bool:
        return self.revision != self.saved_revision

    def set_content(self, content: Any) -> None:
        self.content = content
        self.revision += 1

    def update_metadata(self, **kwargs: Any) -> None:
        self.metadata.update(kwargs)

    def mark_saved(self, path: str | Path | None = None) -> None:
        if path is not None:
            self.path = Path(path)
        self.saved_revision = self.revision

    def save(self, path: str | Path | None = None, *, saver: Optional[DocumentSaver] = None) -> Path:
        target = self.path if path is None else Path(path)
        if target is None:
            raise ValueError("Document save requires a path")
        if saver is None:
            Path(target).write_text(str(self.content), encoding="utf-8")
        else:
            saver(Path(target), self.content)
        self.path = Path(target)
        self.saved_revision = self.revision
        return self.path

    def load(self, path: str | Path, *, loader: Optional[DocumentLoader] = None) -> Any:
        target = Path(path)
        if loader is None:
            loaded = target.read_text(encoding="utf-8")
        else:
            loaded = loader(target)
        self.content = loaded
        self.path = target
        self.revision += 1
        self.saved_revision = self.revision
        return loaded

    def snapshot(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "content": self.content,
            "path": None if self.path is None else str(self.path),
            "metadata": dict(self.metadata),
            "revision": self.revision,
            "saved_revision": self.saved_revision,
        }

    def restore(self, snapshot: Dict[str, Any]) -> None:
        self.document_id = str(snapshot.get("document_id", self.document_id))
        self.content = snapshot.get("content")
        path_value = snapshot.get("path")
        self.path = None if path_value is None else Path(path_value)
        self.metadata = dict(snapshot.get("metadata", {}))
        self.revision = int(snapshot.get("revision", 0))
        self.saved_revision = int(snapshot.get("saved_revision", self.revision))

    # ------------------------------------------------------------------
    # History binding
    # ------------------------------------------------------------------

    def bind_history(self, history: "CommandHistory") -> "Callable[[], None]":
        """Subscribe to *history* so that commands auto-mark this document dirty.

        - Any ``'push'`` event increments the document revision (marks dirty).
        - Any ``'undo'`` or ``'redo'`` event re-evaluates whether the document
          is back at the last-saved revision and adjusts accordingly.

        Returns an unsubscribe callable to detach from the history.
        """
        baseline_revision = self.revision  # revision at bind time = clean point

        def _on_history_change(event: str) -> None:
            nonlocal baseline_revision
            if event == "push":
                self.revision += 1
            elif event in ("undo", "redo"):
                # Recalculate: undo stack depth relative to binding point maps
                # to current document revision above saved_revision.
                # We use history undo_stack_size to estimate position.
                depth = history.undo_stack_size
                self.revision = baseline_revision + depth
                # Refresh saved_revision anchor only when clean
                if not self.is_dirty:
                    baseline_revision = self.revision

        return history.subscribe(_on_history_change)
