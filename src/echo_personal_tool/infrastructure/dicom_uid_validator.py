"""DICOM UID validation for path safety."""

from __future__ import annotations

import re

_UID_PATTERN = re.compile(r'^[0-9.]+$')


def validate_dicom_uid(uid: str) -> bool:
    """Validate DICOM UID contains only digits and dots."""
    return bool(_UID_PATTERN.match(uid)) and len(uid) > 0


def safe_uid_path_component(uid: str) -> str:
    """Return safe path component from UID, raising ValueError if invalid."""
    if not validate_dicom_uid(uid):
        raise ValueError(f"Invalid DICOM UID: {uid!r}")
    return uid
