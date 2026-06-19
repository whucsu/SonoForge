"""Parse and detect B / M / Doppler panels in composite frames."""

from __future__ import annotations

import numpy as np
from pydicom.dataset import Dataset

from echo_personal_tool.domain.models.doppler_roi import DopplerSpectrogramRoi
from echo_personal_tool.domain.models.frame_panels import (
    FramePanelLayout,
    PanelKind,
    UltrasoundPanel,
)

# DICOM PS3.3 C.8.5.5 RegionSpatialFormat
_SPATIAL_2D = 1
_SPATIAL_M_MODE = 2
_SPATIAL_SPECTRAL = 3

# RegionDataType — tissue / PW / CW Doppler
_DOPPLER_DATA_TYPES = frozenset({0x10, 0x11, 16, 17})


def _bounds_to_roi(x0: float, y0: float, x1: float, y1: float) -> DopplerSpectrogramRoi:
    return DopplerSpectrogramRoi(
        x0=x0,
        y0=y0,
        width=max(1.0, x1 - x0),
        height=max(1.0, y1 - y0),
    )


def _panel_kind(spatial_format: int, data_type: int) -> PanelKind | None:
    if spatial_format == _SPATIAL_M_MODE:
        return PanelKind.M_MODE
    if spatial_format == _SPATIAL_SPECTRAL or data_type in _DOPPLER_DATA_TYPES:
        return PanelKind.DOPPLER
    if spatial_format == _SPATIAL_2D and data_type == 1:
        return PanelKind.B_MODE
    if spatial_format == _SPATIAL_2D:
        return PanelKind.B_MODE
    return None


def parse_panels_from_dataset(dataset: Dataset) -> FramePanelLayout | None:
    regions = dataset.get("SequenceOfUltrasoundRegions")
    if not regions:
        return None

    panels: list[UltrasoundPanel] = []
    for region in regions:
        min_x = region.get("RegionLocationMinX0")
        min_y = region.get("RegionLocationMinY0")
        max_x = region.get("RegionLocationMaxX1")
        max_y = region.get("RegionLocationMaxY1")
        if None in (min_x, min_y, max_x, max_y):
            continue

        spatial = int(region.get("RegionSpatialFormat", 0) or 0)
        data_type = int(region.get("RegionDataType", 0) or 0)
        kind = _panel_kind(spatial, data_type)
        if kind is None:
            continue

        delta_x = region.get("PhysicalDeltaX")
        delta_y = region.get("PhysicalDeltaY")
        phys_x = abs(float(delta_x)) if delta_x is not None else None
        phys_y = abs(float(delta_y)) if delta_y is not None else None
        units_x = region.get("PhysicalUnitsXDirection")
        units_y = region.get("PhysicalUnitsYDirection")

        panels.append(
            UltrasoundPanel(
                kind=kind,
                bounds=_bounds_to_roi(float(min_x), float(min_y), float(max_x), float(max_y)),
                physical_delta_x_cm=phys_x,
                physical_delta_y_cm=phys_y,
                physical_units_x=int(units_x) if units_x is not None else None,
                physical_units_y=int(units_y) if units_y is not None else None,
            )
        )

    if not panels:
        return None
    return FramePanelLayout(panels=tuple(panels))


def detect_panels_heuristic(grayscale: np.ndarray) -> FramePanelLayout | None:
    """Guess stacked B + lower strip (M-mode or Doppler) when DICOM regions are absent."""
    if grayscale.ndim != 2:
        return None
    height, width = grayscale.shape[:2]
    if height < 80 or width < 80:
        return None

    split_y = int(height * 0.62)
    if split_y <= 0 or split_y >= height - 10:
        return None

    upper = _bounds_to_roi(0.0, 0.0, float(width), float(split_y))
    lower = _bounds_to_roi(0.0, float(split_y), float(width), float(height - split_y))

    lower_aspect = lower.width / max(lower.height, 1.0)
    lower_kind = PanelKind.M_MODE if lower_aspect > 4.0 else PanelKind.DOPPLER

    return FramePanelLayout(
        panels=(
            UltrasoundPanel(kind=PanelKind.B_MODE, bounds=upper),
            UltrasoundPanel(kind=lower_kind, bounds=lower),
        )
    )
