"""DICOMweb client port (QIDO-RS + WADO-RS)."""

from __future__ import annotations

from typing import Protocol

from echo_personal_tool.domain.models.orthanc import InstanceInfo, SeriesInfo, StudyInfo


class DicomWebClient(Protocol):
    def ping(self) -> bool: ...

    def query_studies(self, patient_name: str | None = None) -> list[StudyInfo]: ...

    def query_series(self, study_uid: str) -> list[SeriesInfo]: ...

    def query_instances(self, study_uid: str, series_uid: str) -> list[InstanceInfo]: ...

    def download_instance(
        self, study_uid: str, series_uid: str, instance_uid: str
    ) -> bytes: ...
