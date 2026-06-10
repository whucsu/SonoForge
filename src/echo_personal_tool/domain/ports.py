"""Domain ports (protocols implemented by infrastructure)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from echo_personal_tool.domain.models import InstanceMetadata, StudyMetadata


class IDicomReader(Protocol):
    def read_pixels(self, path: Path, frame_index: int = 0) -> np.ndarray: ...

    def read_metadata(self, path: Path) -> InstanceMetadata: ...


class IStudyScanner(Protocol):
    def scan(self, root: Path) -> list[StudyMetadata]: ...
