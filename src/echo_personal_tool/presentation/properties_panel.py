"""Properties panel for selected element (measurement, contour, instance)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class PropertiesPanel(QWidget):
    """Context-sensitive panel showing properties of the selected element."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._content = QWidget()
        self._form = QFormLayout(self._content)
        self._form.setSpacing(4)
        self._form.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._content)
        layout.addWidget(scroll)

        # Create groups once, hide when empty
        self._instance_group = QGroupBox("Instance")
        self._instance_form = QFormLayout(self._instance_group)
        self._instance_form.setSpacing(2)
        self._form.addRow(self._instance_group)

        self._measurement_group = QGroupBox("Measurement")
        self._measurement_form = QFormLayout(self._measurement_group)
        self._measurement_form.setSpacing(2)
        self._form.addRow(self._measurement_group)

        self._contour_group = QGroupBox("Contour")
        self._contour_form = QFormLayout(self._contour_group)
        self._contour_form.setSpacing(2)
        self._form.addRow(self._contour_group)

        self._instance_group.hide()
        self._measurement_group.hide()
        self._contour_group.hide()

    def update_instance_info(
        self,
        *,
        modality: str = "",
        series_desc: str = "",
        frame_rate: float | None = None,
        pixel_spacing: str = "",
        number_of_frames: int = 0,
        patient_height_m: float | None = None,
        patient_weight_kg: float | None = None,
        media_format: str = "",
        frame_time_ms: float | None = None,
    ) -> None:
        """Update the instance information section."""
        self._clear_form(self._instance_form)
        if not modality and not series_desc:
            self._instance_group.hide()
            return
        if modality:
            self._instance_form.addRow("Modality:", QLabel(modality))
        if media_format and media_format != "dicom":
            self._instance_form.addRow("Format:", QLabel(media_format.upper()))
        if series_desc:
            self._instance_form.addRow("Series:", QLabel(series_desc))
        if frame_rate and frame_rate > 0:
            self._instance_form.addRow("Frame rate:", QLabel(f"{frame_rate:.1f} fps"))
        if frame_time_ms and frame_time_ms > 0:
            self._instance_form.addRow("Frame time:", QLabel(f"{frame_time_ms:.1f} ms"))
        if number_of_frames > 1:
            self._instance_form.addRow("Frames:", QLabel(str(number_of_frames)))
        if pixel_spacing:
            self._instance_form.addRow("Spacing:", QLabel(pixel_spacing))
        if patient_height_m is not None and patient_height_m > 0:
            self._instance_form.addRow("Height:", QLabel(f"{patient_height_m * 100:.0f} cm"))
        if patient_weight_kg is not None and patient_weight_kg > 0:
            self._instance_form.addRow("Weight:", QLabel(f"{patient_weight_kg:.1f} kg"))
        if patient_height_m and patient_weight_kg and patient_height_m > 0 and patient_weight_kg > 0:
            bmi = patient_weight_kg / (patient_height_m ** 2)
            self._instance_form.addRow("BMI:", QLabel(f"{bmi:.1f}"))
        self._instance_group.show()

    def update_measurement_info(
        self,
        *,
        label: str = "",
        value_mm: float | None = None,
        start: tuple[float, float] | None = None,
        end: tuple[float, float] | None = None,
    ) -> None:
        """Update the measurement information section."""
        self._clear_form(self._measurement_form)
        if not label:
            self._measurement_group.hide()
            return
        self._measurement_form.addRow("Label:", QLabel(label))
        if value_mm is not None:
            self._measurement_form.addRow("Value:", QLabel(f"{value_mm:.1f} mm"))
        if start and end:
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            pixel_len = (dx**2 + dy**2) ** 0.5
            self._measurement_form.addRow("Pixel length:", QLabel(f"{pixel_len:.1f} px"))
        self._measurement_group.show()

    def update_contour_info(
        self,
        *,
        chamber: str = "",
        phase: str = "",
        point_count: int = 0,
        area_px: float | None = None,
    ) -> None:
        """Update the contour information section."""
        self._clear_form(self._contour_form)
        if not chamber and not phase:
            self._contour_group.hide()
            return
        if chamber:
            self._contour_form.addRow("Chamber:", QLabel(chamber))
        if phase:
            self._contour_form.addRow("Phase:", QLabel(phase))
        if point_count:
            self._contour_form.addRow("Points:", QLabel(str(point_count)))
        if area_px is not None:
            self._contour_form.addRow("Area:", QLabel(f"{area_px:.1f} px²"))
        self._contour_group.show()

    def clear_all(self) -> None:
        """Hide all sections."""
        self._instance_group.hide()
        self._measurement_group.hide()
        self._contour_group.hide()

    def _clear_form(self, form: QFormLayout) -> None:
        """Remove all rows from a form layout."""
        while form.rowCount() > 0:
            form.removeRow(0)
