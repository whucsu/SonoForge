"""Application use-case orchestration."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QThreadPool, Signal

from echo_personal_tool.application.workers.dicom_loader_worker import DicomLoaderWorker
from echo_personal_tool.application.workers.scan_worker import ScanWorker
from echo_personal_tool.domain.models import InstanceMetadata, StudyMetadata
from echo_personal_tool.infrastructure.dicom_reader import DicomReaderImpl


class AppController(QObject):
    """Coordinates scanning and frame loading between UI and infrastructure."""

    studies_loaded = Signal(list)
    scan_failed = Signal(str)
    frame_loaded = Signal(np.ndarray)
    frame_load_failed = Signal(str)
    status_message = Signal(str)

    def __init__(self, thread_pool: QThreadPool | None = None) -> None:
        super().__init__()
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._reader = DicomReaderImpl()
        self._studies: list[StudyMetadata] = []
        self._current_instance: InstanceMetadata | None = None

    @property
    def studies(self) -> list[StudyMetadata]:
        return self._studies

    def open_folder(self, root: Path, error_log_path: Path | None = None) -> None:
        self.status_message.emit(f"Scanning {root}…")
        worker = ScanWorker(root, error_log_path=error_log_path)
        worker.signals.finished.connect(self._on_studies_scanned)
        worker.signals.failed.connect(self._on_scan_failed)
        self._thread_pool.start(worker)

    def _on_studies_scanned(self, studies: object) -> None:
        self._studies = list(studies)  # type: ignore[arg-type]
        count = len(self._studies)
        self.status_message.emit(f"Loaded {count} studies")
        self.studies_loaded.emit(self._studies)

    def _on_scan_failed(self, message: str) -> None:
        self.status_message.emit(f"Scan failed: {message}")
        self.scan_failed.emit(message)

    def load_instance(self, instance: InstanceMetadata, frame_index: int = 0) -> None:
        if instance.path is None:
            self.frame_load_failed.emit("Instance has no file path")
            return
        self._current_instance = instance
        self.status_message.emit(f"Loading {instance.path.name}…")
        worker = DicomLoaderWorker(instance.path, frame_index=frame_index)
        worker.signals.finished.connect(self._on_frame_loaded)
        worker.signals.failed.connect(self._on_frame_load_failed)
        self._thread_pool.start(worker)

    def load_first_instance_of_series(self, study: StudyMetadata, series_uid: str) -> None:
        for series in study.series:
            if series.series_uid != series_uid:
                continue
            if not series.instances:
                self.frame_load_failed.emit("Series has no instances")
                return
            self.load_instance(series.instances[0])
            return
        self.frame_load_failed.emit("Series not found in study")

    def _on_frame_loaded(self, pixels: np.ndarray) -> None:
        self.status_message.emit("Frame ready")
        self.frame_loaded.emit(pixels)

    def _on_frame_load_failed(self, message: str) -> None:
        self.status_message.emit(f"Load failed: {message}")
        self.frame_load_failed.emit(message)
