"""Tests for segment_diagnostics (DICOM media_format path)."""

from __future__ import annotations

import numpy as np

from echo_personal_tool.domain.services.segment_diagnostics import (
    diagnose_frame,
    diagnose_dicom_frame,
)
from echo_personal_tool.domain.services.cine_segment_diagnostics import (
    CineSegmentDiagnosticReport,
)


class TestDiagnoseFrame:
    def test_returns_report(self) -> None:
        frame = np.zeros((100, 100), dtype=np.uint8)
        frame[30:70, 20:80] = 150
        report = diagnose_frame(frame, media_format="dicom", run_onnx=False)
        assert isinstance(report, CineSegmentDiagnosticReport)
        assert report.media_format == "dicom"
        assert report.frame_shape == (100, 100)

    def test_default_media_format_is_dicom(self) -> None:
        frame = np.zeros((100, 100), dtype=np.uint8)
        report = diagnose_frame(frame, run_onnx=False)
        assert report.media_format == "dicom"


class TestDiagnoseDicomFrame:
    def test_returns_report(self) -> None:
        frame = np.zeros((100, 100), dtype=np.uint8)
        report = diagnose_dicom_frame(frame, run_onnx=False)
        assert isinstance(report, CineSegmentDiagnosticReport)
        assert report.media_format == "dicom"
