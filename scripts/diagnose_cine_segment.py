#!/usr/bin/env python3
"""Interactive CLI: diagnose LV auto-segment on untagged cine (MP4) files."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from echo_personal_tool.domain.services.cine_segment_diagnostics import (
    diagnose_video_file,
    format_diagnostic_report,
    load_video_frame,
    render_diagnostic_overlay,
)
from echo_personal_tool.domain.services.segment_roi import echonet_crop_mode_for_media
from echo_personal_tool.infrastructure.onnx_engine import OnnxInferenceEngine


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose ONNX LV segmentation on MP4/cine without DICOM tags",
    )
    parser.add_argument("path", type=Path, help="Path to MP4 or video file")
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
    parser.add_argument(
        "--freeze-roi-from-frame",
        type=int,
        default=None,
        metavar="N",
        help="Use ROI from frame N for all ONNX/diagnostics (simulates frozen cine ROI)",
    )
    args = parser.parse_args()

    if not args.path.is_file():
        print(f"File not found: {args.path}")
        return 1

    report = diagnose_video_file(
        args.path,
        frame_index=args.frame,
        run_onnx=not args.no_onnx,
        freeze_roi_from_frame=args.freeze_roi_from_frame,
    )
    print(format_diagnostic_report(report))

    if args.output is not None:
        frame = load_video_frame(args.path, args.frame)
        mask = None
        if not args.no_onnx and report.onnx_available:
            engine = OnnxInferenceEngine()
            roi = report.roi_xyxy
            crop_mode = echonet_crop_mode_for_media("mp4")
            mask = engine.segment(frame, roi_xyxy=roi, crop_mode=crop_mode)
        overlay = render_diagnostic_overlay(frame, roi_xyxy=report.roi_xyxy, mask=mask)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(args.output), overlay)
        print(f"overlay: {args.output}")

    return 0 if not report.issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
