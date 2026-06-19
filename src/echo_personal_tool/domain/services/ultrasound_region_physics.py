"""Interpret DICOM SequenceOfUltrasoundRegions physical deltas and units."""

from __future__ import annotations

from pydicom.dataset import Dataset

# DICOM PS3.3 C.8.5.5 Physical Units
PHYSICAL_UNIT_CM = 3
PHYSICAL_UNIT_SEC = 4
PHYSICAL_UNIT_CM_PER_SEC = 6

# RegionSpatialFormat
SPATIAL_SPECTRAL = 3
SPATIAL_M_MODE = 2

# RegionDataType — spectral / tissue Doppler
DOPPLER_DATA_TYPES = frozenset({0x10, 0x11, 16, 17})


def region_physical_deltas(region: Dataset) -> tuple[float | None, float | None, int | None, int | None]:
    """Return (delta_x, delta_y, units_x, units_y) from one ultrasound region item."""
    dx = region.get("PhysicalDeltaX")
    dy = region.get("PhysicalDeltaY")
    ux = region.get("PhysicalUnitsXDirection")
    uy = region.get("PhysicalUnitsYDirection")
    delta_x = abs(float(dx)) if dx is not None else None
    delta_y = abs(float(dy)) if dy is not None else None
    units_x = int(ux) if ux is not None else None
    units_y = int(uy) if uy is not None else None
    return delta_x, delta_y, units_x, units_y


def horizontal_ms_per_pixel(delta_x: float, units_x: int) -> float | None:
    """M-mode / spectral sweep: seconds per pixel on the time axis."""
    if units_x != PHYSICAL_UNIT_SEC or delta_x <= 0.0:
        return None
    return delta_x * 1000.0


def vertical_mm_per_pixel(delta_y: float, units_y: int) -> float | None:
    """Depth axis in cm → mm per pixel."""
    if units_y != PHYSICAL_UNIT_CM or delta_y <= 0.0:
        return None
    return delta_y * 10.0


def time_span_ms_from_region(width_px: float, delta_x: float, units_x: int) -> float | None:
    """Full horizontal span of a spectrogram/M-mode strip in milliseconds."""
    ms_per_px = horizontal_ms_per_pixel(delta_x, units_x)
    if ms_per_px is None or width_px <= 0.0:
        return None
    return width_px * ms_per_px


def velocity_span_cm_s_from_region(height_px: float, delta_y: float, units_y: int) -> float | None:
    """Full vertical velocity span (cm/s) for spectral Doppler."""
    if units_y != PHYSICAL_UNIT_CM_PER_SEC or delta_y <= 0.0 or height_px <= 0.0:
        return None
    return height_px * delta_y


def is_spectral_doppler_region(region: Dataset) -> bool:
    spatial = int(region.get("RegionSpatialFormat", 0) or 0)
    data_type = int(region.get("RegionDataType", 0) or 0)
    if spatial == SPATIAL_SPECTRAL:
        return True
    return data_type in DOPPLER_DATA_TYPES


def is_mmode_region(region: Dataset) -> bool:
    return int(region.get("RegionSpatialFormat", 0) or 0) == SPATIAL_M_MODE
