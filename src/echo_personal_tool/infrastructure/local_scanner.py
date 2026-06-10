"""Recursive local DICOM directory scanner."""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

import pydicom

from echo_personal_tool.domain.models import (
    InstanceMetadata,
    SeriesMetadata,
    StudyMetadata,
)
from echo_personal_tool.infrastructure.dicom_metadata_mapper import (
    map_instance_metadata,
    parse_study_datetime,
)

logger = logging.getLogger(__name__)

DICOM_EXTENSIONS = {".dcm", ".dicom", ""}


class LocalDicomDirectoryScanner:
    """Scan a folder tree and build study → series → instance hierarchy."""

    def __init__(self, error_log_path: Path | None = None) -> None:
        self._error_log_path = error_log_path

    def scan(self, root: Path) -> list[StudyMetadata]:
        root = root.resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"Not a directory: {root}")

        studies: dict[str, dict[str, list[InstanceMetadata]]] = defaultdict(
            lambda: defaultdict(list)
        )
        study_datetimes: dict[str, object] = {}

        for path in self._iter_dicom_files(root):
            try:
                dataset = pydicom.dcmread(path, stop_before_pixels=True, force=True)
            except Exception as exc:  # noqa: BLE001 — collect and continue per spec
                self._log_scan_error(path, exc)
                continue

            study_uid = str(dataset.get("StudyInstanceUID", "") or "")
            series_uid = str(dataset.get("SeriesInstanceUID", "") or "")
            if not study_uid or not series_uid:
                self._log_scan_error(path, ValueError("Missing Study/Series UID"))
                continue

            instance = map_instance_metadata(dataset, path=path)
            studies[study_uid][series_uid].append(instance)
            if study_uid not in study_datetimes:
                study_datetimes[study_uid] = parse_study_datetime(dataset)

        result: list[StudyMetadata] = []
        for study_uid, series_map in studies.items():
            series_list: list[SeriesMetadata] = []
            for series_uid, instances in series_map.items():
                instances_sorted = tuple(
                    sorted(instances, key=lambda i: i.sop_instance_uid)
                )
                first = instances_sorted[0]
                series_list.append(
                    SeriesMetadata(
                        series_uid=series_uid,
                        study_uid=study_uid,
                        modality=first.modality,
                        description=first.series_description,
                        instances=instances_sorted,
                    )
                )
            series_list.sort(key=lambda s: (s.modality, s.description))
            result.append(
                StudyMetadata(
                    study_uid=study_uid,
                    study_datetime=study_datetimes[study_uid],  # type: ignore[arg-type]
                    series=tuple(series_list),
                )
            )

        result.sort(key=lambda s: s.study_datetime, reverse=True)
        return result

    def _iter_dicom_files(self, root: Path):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in {".dcm", ".dicom"} or path.suffix == "":
                yield path

    def _log_scan_error(self, path: Path, exc: Exception) -> None:
        message = f"{path}: {exc}"
        logger.warning("Scan skip: %s", message)
        if self._error_log_path is None:
            return
        try:
            with self._error_log_path.open("a", encoding="utf-8") as fh:
                fh.write(message + "\n")
        except OSError:
            logger.exception("Failed to write scan error log")
