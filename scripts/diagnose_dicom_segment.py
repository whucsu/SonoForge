#!/usr/bin/env python3
"""CLI: diagnose LV auto-segment on DICOM files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path for package imports.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import cv2

from echo_personal_tool.domain.services.segment_diagnostics import (
    diagnose_frame,
    format_diagnostic_report,
    render_diagnostic_overlay,
)
from echo_personal_tool.infrastructure.dicom_reader import DicomReaderImpl


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose ONNX LV segmentation on DICOM files",
    )
    parser.add_argument("path", type=Path, help="Path to DICOM file")
    parser.add_argument("--frame", type=int, default=0, help="Frame index (default: 0)")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write BGR debug overlay PNG (ROI green, mask red)",
    )
    parser.add_argument(
        "--no-onnx",
        action="store_true",
        help="Only report ROI/crop geometry without running ONNX",
    )
    args = parser.parse_args()

    if not args.path.is_file():
        print(f"File not found: {args.path}")
        return 1

    reader = DicomReaderImpl()
    try:
        frame = reader.read_pixels(args.path, args.frame)
    except Exception as exc:
        print(f"Failed to read DICOM frame: {exc}")
        return 1

    report = diagnose_frame(
        frame,
        media_format="dicom",
        source_path=str(args.path),
        frame_index=args.frame,
        run_onnx=not args.no_onnx,
    )
    print(format_diagnostic_report(report))

    if args.output is not None:
        mask = None
        if not args.no_onnx and report.onnx_available:
            from echo_personal_tool.infrastructure.onnx_engine import OnnxInferenceEngine
            from echo_personal_tool.domain.services.segment_roi import (
                echonet_crop_mode_for_media,
            )
            engine = OnnxInferenceEngine()
            roi = report.roi_xyxy
            crop_mode = echonet_crop_mode_for_media("dicom")
            mask = engine.segment(frame, roi_xyxy=roi, crop_mode=crop_mode)
        overlay = render_diagnostic_overlay(frame, roi_xyxy=report.roi_xyxy, mask=mask)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(args.output), overlay)
        print(f"overlay: {args.output}")

    return 0 if not report.issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
