"""Background study tree scanner."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from echo_personal_tool.domain.models import StudyMetadata
from echo_personal_tool.infrastructure.local_scanner import LocalDicomDirectoryScanner


class ScanSignals(QObject):
    finished = Signal(list)
    failed = Signal(str)


class ScanWorker(QRunnable):
    """Scan a directory for DICOM studies without blocking the UI."""

    def __init__(self, root: Path, error_log_path: Path | None = None) -> None:
        super().__init__()
        self._root = root
        self._error_log_path = error_log_path
        self.signals = ScanSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            scanner = LocalDicomDirectoryScanner(error_log_path=self._error_log_path)
            studies: list[StudyMetadata] = scanner.scan(self._root)
            self.signals.finished.emit(studies)
        except Exception as exc:  # noqa: BLE001
            self.signals.failed.emit(str(exc))
