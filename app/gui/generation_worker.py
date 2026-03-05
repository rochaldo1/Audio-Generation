"""Worker thread for running generation tasks without freezing the UI."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QThread, Signal


class GenerationKind(Enum):
    INSTRUMENTAL = "instrumental"
    VOCAL = "vocal"
    SFX = "sfx"
    VARIATION = "variation"


@dataclass
class GenerationResult:
    kind: GenerationKind
    success: bool
    track: Any = None
    error: Optional[str] = None


class GenerationWorker(QObject):
    """Runs a generation callable in a background thread."""
    finished = Signal(object)  # GenerationResult

    def __init__(
        self,
        task: Callable[[], GenerationResult],
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._task = task

    def run(self) -> None:
        try:
            result = self._task()
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(
                GenerationResult(
                    kind=GenerationKind.INSTRUMENTAL,  # placeholder
                    success=False,
                    error=str(e),
                )
            )
