"""Top system bar: study context, global actions."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class SystemBar(QWidget):
    """EchoPac-style header above the main splitter."""

    open_folder_requested = Signal()
    reset_session_requested = Signal()
    caliper_requested = Signal()
    calibration_requested = Signal()
    doppler_calibration_requested = Signal()
    settings_requested = Signal()
    references_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("systemBar")

        self._study_label = QLabel("No study loaded")
        self._study_label.setMinimumWidth(120)
        self._study_label.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred,
        )

        self._status_label = QLabel("Ready")
        self._status_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        btn_open = QPushButton("Open folder…")
        btn_open.clicked.connect(self.open_folder_requested.emit)

        self._btn_settings = QPushButton("Настройки")
        self._btn_settings.setToolTip("Параметры измерений и отображения")
        self._btn_settings.clicked.connect(self.settings_requested.emit)

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

        self._btn_references = QPushButton("Нормативы")
        self._btn_references.setToolTip("Справочник нормативных значений ASE")
        self._btn_references.clicked.connect(self.references_requested.emit)

        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self.reset_session_requested.emit)

        left = QWidget()
        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 12, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(btn_open)
        left_layout.addWidget(self._study_label)
        left_layout.addWidget(self._status_label, 1)

        self._actions_widget = QWidget()
        self._actions_widget.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred,
        )
        actions_layout = QHBoxLayout(self._actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        for button in (
            self._btn_settings,
            btn_caliper,
            btn_calibration,
            btn_doppler_calibration,
            self._btn_references,
            btn_reset,
        ):
            actions_layout.addWidget(button)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(0)
        layout.addWidget(left, 1)
        layout.addWidget(self._actions_widget, 0)

    def set_study_context(self, label: str, modality: str = "") -> None:
        del modality
        self._study_label.setText(label)
        self._study_label.setToolTip(label)

    def clear_study_context(self) -> None:
        self._study_label.setText("No study loaded")
        self._study_label.setToolTip("")

    def set_status_message(self, message: str) -> None:
        self._status_label.setText(message[:200])
