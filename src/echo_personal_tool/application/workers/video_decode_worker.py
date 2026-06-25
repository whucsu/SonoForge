"""Background worker that decodes all frames from an MP4 video file."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from echo_personal_tool.infrastructure.pixel_utils import to_bgr_uint8


class VideoDecodeSignals(QObject):
    finished = Signal(int, object, object)  # request_id, path, frames ndarray
    failed = Signal(int, str)


class VideoDecodeWorker(QRunnable):
    def __init__(
        self,
        path: Path,
        request_id: int,
        parent: QObject | None = None,
    ) -> None:
        super().__init__()
        self._path = Path(path)
        self._request_id = request_id
        self.signals = VideoDecodeSignals(parent)
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            import cv2

            cap = cv2.VideoCapture(str(self._path))
            if not cap.isOpened():
                raise OSError(f"Cannot open video: {self._path}")

            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total <= 0:
                cap.release()
                raise OSError(f"Cannot determine frame count: {self._path}")

            frames: list[np.ndarray] = []
            for _ in range(total):
                ok, bgr = cap.read()
                if not ok or bgr is None:
                    break
                frames.append(to_bgr_uint8(bgr))
            cap.release()

            if not frames:
                raise OSError(f"No frames decoded from: {self._path}")

            result = np.stack(frames, axis=0)
            self.signals.finished.emit(
                self._request_id,
                self._path,
                np.ascontiguousarray(result),
            )
        except Exception as exc:  # noqa: BLE001
            self.signals.failed.emit(self._request_id, str(exc))
