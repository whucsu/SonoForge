"""Unit tests for Orthanc DICOMweb JSON parser."""

from __future__ import annotations

import json
from pathlib import Path

from echo_personal_tool.infrastructure.orthanc_dicom_json import (
    parse_instances,
    parse_series,
    parse_studies,
    tag_value,
)


def test_tag_value_reads_pn_and_uid() -> None:
    item = {"00100010": {"vr": "PN", "Value": ["IVANOV^IVAN"]}}
    assert tag_value(item, "00100010") == "IVANOV^IVAN"


def test_tag_value_reads_pn_alphabetic_dict() -> None:
    item = {
        "00100010": {
            "vr": "PN",
            "Value": [{"Alphabetic": "IVANOV^IVAN", "Ideographic": ""}],
        }
    }
    assert tag_value(item, "00100010") == "IVANOV^IVAN"


def test_tag_value_returns_default_for_missing_tag() -> None:
    assert tag_value({}, "00100010") == ""
    assert tag_value({}, "00100010", default="N/A") == "N/A"


def test_tag_value_reads_ui_study_instance_uid() -> None:
    item = {
        "0020000D": {
            "vr": "UI",
            "Value": ["1.2.410.200001.1.1185.2062614048.1.20240404.1120546412.448.1"],
        }
    }
    assert tag_value(item, "0020000D") == ("1.2.410.200001.1.1185.2062614048.1.20240404.1120546412.448.1")


def test_parse_studies_from_fixture() -> None:
    raw = Path("tests/fixtures/orthanc/studies.json").read_text(encoding="utf-8")
    studies = parse_studies(json.loads(raw))
    assert len(studies) >= 1
    assert studies[0].study_uid.startswith("1.2.")
    assert studies[0].study_uid == ("1.2.410.200001.1.1185.2062614048.1.20240404.1120546412.448.1")
    assert studies[0].patient_name == "TEST^PATIENT"
    assert studies[0].patient_id == "TEST123"
    assert studies[0].study_date == "20240404"
    assert studies[0].study_description == "Echo study"


def test_parse_series_injects_study_uid() -> None:
    study_uid = "1.2.410.200001.1.1185.2062614048.1.20240404.1120546412.448.1"
    payload = [
        {
            "0020000E": {"vr": "UI", "Value": ["1.2.410.200001.1.1185.2062614048.1.20240404.1120546412.448.2"]},
            "00080060": {"vr": "CS", "Value": ["US"]},
            "0008103E": {"vr": "LO", "Value": ["Echo series"]},
            "00201209": {"vr": "IS", "Value": ["10"]},
        }
    ]
    series_list = parse_series(payload, study_uid)
    assert len(series_list) == 1
    assert series_list[0].series_uid == ("1.2.410.200001.1.1185.2062614048.1.20240404.1120546412.448.2")
    assert series_list[0].study_uid == study_uid
    assert series_list[0].modality == "US"
    assert series_list[0].description == "Echo series"
    assert series_list[0].instance_count == 10


def test_parse_instances_injects_study_and_series_uid() -> None:
    study_uid = "1.2.410.200001.1.1185.2062614048.1.20240404.1120546412.448.1"
    series_uid = "1.2.410.200001.1.1185.2062614048.1.20240404.1120546412.448.2"
    payload = [
        {
            "00080018": {
                "vr": "UI",
                "Value": ["1.2.410.200001.1.1185.2062614048.1.20240404.1120546412.448.3"],
            }
        }
    ]
    instances = parse_instances(payload, study_uid, series_uid)
    assert len(instances) == 1
    assert instances[0].sop_instance_uid == ("1.2.410.200001.1.1185.2062614048.1.20240404.1120546412.448.3")
    assert instances[0].study_uid == study_uid
    assert instances[0].series_uid == series_uid
