"""Top system bar: study context, global actions."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class SystemBar(QWidget):
    """EchoPac-style header above the main splitter."""

    open_folder_requested = Signal()
    reset_session_requested = Signal()
    caliper_requested = Signal()
    calibration_requested = Signal()
    doppler_calibration_requested = Signal()
    auto_segment_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("systemBar")

        self._study_label = QLabel("No study loaded")
        self._study_label.setMinimumWidth(280)

        self._status_label = QLabel("Ready")
        self._status_label.setMinimumWidth(160)

        btn_open = QPushButton("Open folder…")
        btn_open.clicked.connect(self.open_folder_requested.emit)

        btn_caliper = QPushButton("Caliper")
        btn_caliper.setToolTip("Linear distance (Dist1, Dist2, …)")
        btn_caliper.clicked.connect(self.caliper_requested.emit)

        btn_calibration = QPushButton("Calibration B-mode")
        btn_calibration.setToolTip("B-mode pixel spacing: depth scale line")
        btn_calibration.clicked.connect(self.calibration_requested.emit)

        btn_doppler_calibration = QPushButton("Calibration Doppler")
        btn_doppler_calibration.setToolTip(
            "Doppler spectrogram: ROI → baseline → velocity scale"
        )
        btn_doppler_calibration.clicked.connect(self.doppler_calibration_requested.emit)

        self._btn_auto = QPushButton("Auto Segment")
        self._btn_auto.setToolTip("ONNX auto-segment (I)")
        self._btn_auto.clicked.connect(self.auto_segment_requested.emit)

        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self.reset_session_requested.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.addWidget(btn_open)
        layout.addWidget(self._study_label)
        layout.addStretch(1)
        layout.addWidget(btn_caliper)
        layout.addWidget(btn_calibration)
        layout.addWidget(btn_doppler_calibration)
        layout.addWidget(self._btn_auto)
        layout.addWidget(btn_reset)
        layout.addWidget(self._status_label)

    def set_study_context(self, label: str, modality: str = "") -> None:
        del modality
        self._study_label.setText(label)
        self._study_label.setToolTip(label)

    def clear_study_context(self) -> None:
        self._study_label.setText("No study loaded")
        self._study_label.setToolTip("")

    def set_status_message(self, message: str) -> None:
        self._status_label.setText(message[:120])

    def set_auto_segment_enabled(self, enabled: bool) -> None:
        self._btn_auto.setEnabled(enabled)
