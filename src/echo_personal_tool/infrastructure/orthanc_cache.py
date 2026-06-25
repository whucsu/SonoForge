"""Filesystem cache for DICOM instances downloaded from Orthanc."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path


class OrthancSessionCache:
    def __init__(self, root: Path) -> None:
        self._root = root

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        (self._root / f"session-{session_id}").mkdir(parents=True, exist_ok=True)
        return session_id

    def save_instance(
        self,
        session_id: str,
        study_uid: str,
        series_uid: str,
        sop_uid: str,
        data: bytes,
    ) -> Path:
        path = self._root / f"session-{session_id}" / study_uid / series_uid / f"{sop_uid}.dcm"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def study_path(self, session_id: str, study_uid: str) -> Path:
        return self._root / f"session-{session_id}" / study_uid

    def session_path(self, session_id: str) -> Path:
        return self._root / f"session-{session_id}"

    def clear_session(self, session_id: str) -> None:
        session_dir = self._root / f"session-{session_id}"
        if session_dir.exists():
            shutil.rmtree(session_dir)

    def clear_all(self) -> None:
        if not self._root.exists():
            return
        for entry in self._root.iterdir():
            if entry.is_dir() and entry.name.startswith("session-"):
                shutil.rmtree(entry)
