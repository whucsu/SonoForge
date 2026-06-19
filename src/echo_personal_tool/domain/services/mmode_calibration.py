"""Build M-mode calibration from ultrasound panels."""

from __future__ import annotations

from echo_personal_tool.domain.models.frame_panels import (
    MmodeCalibrationState,
    PanelKind,
    UltrasoundPanel,
)


def mmode_state_from_panel(panel: UltrasoundPanel) -> MmodeCalibrationState | None:
    if panel.kind is not PanelKind.M_MODE:
        return None
    vertical_mm = panel.vertical_mm_per_pixel
    if vertical_mm is None or vertical_mm <= 0.0:
        return None
    return MmodeCalibrationState(
        roi=panel.bounds,
        vertical_mm_per_pixel=vertical_mm,
        horizontal_ms_per_pixel=panel.horizontal_ms_per_pixel,
    )
