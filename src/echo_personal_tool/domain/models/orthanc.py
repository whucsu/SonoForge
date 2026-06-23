"""Orthanc DICOMweb query result models (no HTTP / Qt dependencies)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StudyInfo:
    study_uid: str
    patient_name: str
    patient_id: str
    study_date: str
    study_description: str
    series_count: int | None = None


@dataclass(frozen=True)
class SeriesInfo:
    series_uid: str
    study_uid: str
    modality: str
    description: str
    instance_count: int | None = None


@dataclass(frozen=True)
class InstanceInfo:
    sop_instance_uid: str
    series_uid: str
    study_uid: str
