"""Background worker that decodes DICOM frames progressively."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from echo_personal_tool.infrastructure.dicom_session import get_thread_dicom_session


class DicomDecodeSignals(QObject):
    first_frame_ready = Signal(int, object, object)  # request_id, path, first_frame
    progress = Signal(int, int)  # current, total
    finished = Signal(int, object, object)  # request_id, path, all_frames
    failed = Signal(int, str)


class DicomDecodeWorker(QRunnable):
    """Decode DICOM progressively: first frame immediately, then all frames."""

    def __init__(
        self,
        path: Path,
        request_id: int,
        parent: QObject | None = None,
    ) -> None:
        super().__init__()
        self._path = Path(path)
        self._request_id = request_id
        self.signals = DicomDecodeSignals(parent)
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            session = get_thread_dicom_session()
            session.open(self._path)

            # Emit first frame immediately for fast display
            first_frame = session.decode_first_frame()
            self.signals.first_frame_ready.emit(
                self._request_id,
                self._path,
                first_frame,
            )
            self.signals.progress.emit(1, 1)

            # Decode remaining frames (reuses cached pixel_array)
            frames = session.decode_all_frames()
            self.signals.finished.emit(
                self._request_id,
                self._path,
                frames,
            )
        except Exception as exc:  # noqa: BLE001
            self.signals.failed.emit(self._request_id, str(exc))
