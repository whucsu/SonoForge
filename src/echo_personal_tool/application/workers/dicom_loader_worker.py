"""Background workers for DICOM I/O."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from echo_personal_tool.infrastructure.dicom_reader import DicomReaderImpl


class DicomLoaderSignals(QObject):
    finished = Signal(np.ndarray)
    failed = Signal(str)


class DicomLoaderWorker(QRunnable):
    """Load a single DICOM frame on a thread pool thread."""

    def __init__(self, path: Path, frame_index: int = 0) -> None:
        super().__init__()
        self._path = path
        self._frame_index = frame_index
        self.signals = DicomLoaderSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            reader = DicomReaderImpl()
            pixels = reader.read_pixels(self._path, frame_index=self._frame_index)
            self.signals.finished.emit(pixels)
        except Exception as exc:  # noqa: BLE001 — surface to UI
            self.signals.failed.emit(str(exc))
