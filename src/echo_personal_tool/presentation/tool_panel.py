"""Right-side tool panel with Measures / Controls tabs."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from echo_personal_tool.presentation.ge_labeled_slider import GeLabeledSlider
from echo_personal_tool.presentation.measures_menu import MeasuresMenuWidget


class _PatientMetricsRow(QWidget):
    """Height / weight inputs (0 = empty)."""

    metrics_changed = Signal(object, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 4, 8, 8)
        row.addWidget(QLabel("Рост"))
        self._height_spin = QDoubleSpinBox()
        self._height_spin.setRange(0.0, 250.0)
        self._height_spin.setDecimals(1)
        self._height_spin.setSuffix(" cm")
        self._height_spin.setSpecialValueText("")
        self._height_spin.valueChanged.connect(self._emit_metrics)
        row.addWidget(self._height_spin)
        row.addWidget(QLabel("Вес"))
        self._weight_spin = QDoubleSpinBox()
        self._weight_spin.setRange(0.0, 300.0)
        self._weight_spin.setDecimals(1)
        self._weight_spin.setSuffix(" kg")
        self._weight_spin.setSpecialValueText("")
        self._weight_spin.valueChanged.connect(self._emit_metrics)
        row.addWidget(self._weight_spin)
        row.addStretch(1)

    def _emit_metrics(self) -> None:
        height = self._height_spin.value()
        weight = self._weight_spin.value()
        self.metrics_changed.emit(
            height if height > 0.0 else None,
            weight if weight > 0.0 else None,
        )

    def set_metrics(self, height_cm: float | None, weight_kg: float | None) -> None:
        self._height_spin.blockSignals(True)
        self._weight_spin.blockSignals(True)
        self._height_spin.setValue(height_cm if height_cm else 0.0)
        self._weight_spin.setValue(weight_kg if weight_kg else 0.0)
        self._height_spin.blockSignals(False)
        self._weight_spin.blockSignals(False)


class ControlsTab(QWidget):
    """Window / Level / DR sliders (GE Controls)."""

    magnetic_snap_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.window_slider = GeLabeledSlider("Window", minimum=1, maximum=400, value=100)
        self.level_slider = GeLabeledSlider("Level", minimum=0, maximum=100, value=50)
        self.dr_slider = GeLabeledSlider("DR", minimum=0, maximum=100, value=50)
        self.dr_slider.slider().setToolTip(
            "Dynamic range: center = full range; left = clip dark (typical for US)"
        )
        self._magnetic_snap_check = QCheckBox("Магнит к стенке")
        self._magnetic_snap_check.setChecked(True)
        self._magnetic_snap_check.setToolTip(
            "При отпускании узла — мягкое прилипание к границе по градиенту"
        )
        self._magnetic_snap_check.toggled.connect(self.magnetic_snap_changed.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)
        layout.addWidget(self.window_slider)
        layout.addWidget(self.level_slider)
        layout.addWidget(self.dr_slider)
        layout.addWidget(self._magnetic_snap_check)
        layout.addStretch(1)


class MeasureTab(QWidget):
    """Measurement tools only (results shown on-image overlay)."""

    action_requested = Signal(object, str, str, str)
    patient_metrics_changed = Signal(object, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._menu = MeasuresMenuWidget()
        self._menu.action_requested.connect(self.action_requested.emit)
        self._patient_metrics = _PatientMetricsRow()
        self._patient_metrics.metrics_changed.connect(self.patient_metrics_changed.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._menu, stretch=1)
        layout.addWidget(self._patient_metrics)

    def set_patient_metrics(self, height_cm: float | None, weight_kg: float | None) -> None:
        self._patient_metrics.set_metrics(height_cm, weight_kg)

    def set_doppler_tool_availability(self, *, time_ok: bool) -> None:
        self._menu.set_doppler_tool_availability(time_ok=time_ok)


class ToolPanel(QWidget):
    """EchoPac-style right tool menu."""

    action_requested = Signal(object, str, str, str)
    patient_metrics_changed = Signal(object, object)
    magnetic_snap_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("toolPanel")
        self.setMinimumWidth(260)
        self.setMaximumWidth(360)

        self._tabs = QTabWidget()
        self.measure = MeasureTab()
        self.controls = ControlsTab()

        self._tabs.addTab(self.measure, "Measures")
        self._tabs.addTab(self.controls, "Controls")

        self.measure.action_requested.connect(self.action_requested.emit)
        self.measure.patient_metrics_changed.connect(self.patient_metrics_changed.emit)
        self.controls.magnetic_snap_changed.connect(self.magnetic_snap_changed.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)

    def set_patient_metrics(self, height_cm: float | None, weight_kg: float | None) -> None:
        self.measure.set_patient_metrics(height_cm, weight_kg)

    def set_doppler_tool_availability(self, *, time_ok: bool) -> None:
        self.measure.set_doppler_tool_availability(time_ok=time_ok)
