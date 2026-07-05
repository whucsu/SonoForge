"""Diagnostics for LV auto-segmentation (DICOM and untagged cine)."""

from __future__ import annotations

from echo_personal_tool.domain.services.cine_segment_diagnostics import (
    CineSegmentDiagnosticReport,
    _arc_depth_px,
    _arc_span_px,
    _collect_issues,
    _mask_bbox,
    _mask_centroid,
    diagnose_cine_frame,
    format_diagnostic_report,
    load_video_frame,
    render_diagnostic_overlay,
)

__all__ = [
    "CineSegmentDiagnosticReport",
    "diagnose_cine_frame",
    "diagnose_frame",
    "format_diagnostic_report",
    "load_video_frame",
    "render_diagnostic_overlay",
]


def diagnose_frame(
    frame,
    *,
    media_format: str = "dicom",
    source_path: str | None = None,
    frame_index: int = 0,
    run_onnx: bool = True,
    frozen_roi_xyxy: tuple[float, float, float, float] | None = None,
) -> CineSegmentDiagnosticReport:
    """Build a diagnostic report for one frame (DICOM or cine).

    Thin wrapper around diagnose_cine_frame with media_format default changed to dicom.
    """
    return diagnose_cine_frame(
        frame,
        media_format=media_format,
        source_path=source_path,
        frame_index=frame_index,
        run_onnx=run_onnx,
        frozen_roi_xyxy=frozen_roi_xyxy,
    )


def diagnose_dicom_frame(
    frame,
    *,
    source_path: str | None = None,
    frame_index: int = 0,
    run_onnx: bool = True,
) -> CineSegmentDiagnosticReport:
    """Diagnostic report for a single DICOM frame."""
    return diagnose_frame(
        frame,
        media_format="dicom",
        source_path=source_path,
        frame_index=frame_index,
        run_onnx=run_onnx,
    )
