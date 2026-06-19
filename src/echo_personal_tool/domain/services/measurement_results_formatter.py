"""Compact GE-style measurement results text for on-image overlay."""

from __future__ import annotations

from echo_personal_tool.domain.models.measurements import MeasurementSnapshot


def format_results_overlay(
    snapshot: MeasurementSnapshot | None,
    *,
    time_calibrated: bool = False,
    amplitude_only: bool | None = None,
) -> str:
    """Return multi-line summary of session-computed values (study-wide)."""
    if amplitude_only is not None:
        time_calibrated = not amplitude_only
    if snapshot is None:
        return ""

    lines: list[str] = []

    dop = snapshot.doppler
    if dop is not None:
        _append(lines, "E", dop.e_cm_s, "cm/s")
        _append(lines, "A", dop.a_cm_s, "cm/s")
        _append(lines, "E/A", dop.e_a_ratio, "")
        if time_calibrated:
            _append(lines, "DT", dop.dt_ms, "ms")
            _append(lines, "IVRT", dop.ivrt_ms, "ms")
            _append(lines, "AT", dop.at_ms, "ms")
        _append(lines, "e' sept", dop.e_prime_sept_cm_s, "cm/s")
        _append(lines, "e' lat", dop.e_prime_lat_cm_s, "cm/s")
        _append(lines, "e' mean", dop.e_prime_avg_cm_s, "cm/s")
        _append(lines, "E/e'", dop.e_over_e_prime, "")
        _append(lines, "E/e' sept", dop.e_over_e_prime_sept, "")
        _append(lines, "E/e' lat", dop.e_over_e_prime_lat, "")
        _append(lines, "e'/a'", dop.e_prime_over_a_prime, "")
        _append(lines, "Vpeak", dop.vpeak_cm_s, "cm/s")
        _append(lines, "PGpeak", dop.pgpeak_mmhg, "mmHg")
        _append(lines, "TR Vmax", dop.tr_vmax_cm_s, "cm/s")
        if time_calibrated:
            _append(lines, "VTI", dop.vti_cm, "cm")
            _append(lines, "Vmean", dop.vmean_cm_s, "cm/s")
            _append(lines, "PGmean", dop.pgmean_mmhg, "mmHg")

    volume_unit = "mL" if snapshot.spacing_calibrated else "px³"

    lvef = snapshot.lvef
    if lvef is not None:
        if lvef.a4c and lvef.a4c.edv_ml is not None:
            _append(lines, "EDV 4C", lvef.a4c.edv_ml, volume_unit)
        if lvef.a4c and lvef.a4c.esv_ml is not None:
            _append(lines, "ESV 4C", lvef.a4c.esv_ml, volume_unit)
        if lvef.a2c and lvef.a2c.edv_ml is not None:
            _append(lines, "EDV 2C", lvef.a2c.edv_ml, volume_unit)
        if lvef.a2c and lvef.a2c.esv_ml is not None:
            _append(lines, "ESV 2C", lvef.a2c.esv_ml, volume_unit)
        _append(lines, "LVEF", lvef.lvef_percent, "%")

    teich = snapshot.teichholz
    if teich is not None:
        _append(lines, "EDV (T)", teich.edv_ml, volume_unit)
        _append(lines, "ESV (T)", teich.esv_ml, volume_unit)
        _append(lines, "LVEF (T)", teich.lvef_percent, "%")

    if snapshot.lvm_g is not None:
        _append(lines, "LVM", snapshot.lvm_g, "g")

    if snapshot.la_volume and snapshot.la_volume.volume_ml is not None:
        _append(lines, "LAV", snapshot.la_volume.volume_ml, volume_unit)

    if snapshot.rv_fac_percent is not None:
        _append(lines, "FAC", snapshot.rv_fac_percent, "%")

    if snapshot.diastology_grade:
        lines.append(snapshot.diastology_grade)

    idx = snapshot.indexed
    if idx is not None and idx.bsa_m2 is not None:
        _append(lines, "BSA", idx.bsa_m2, "m²", decimals=2)

    for measurement in snapshot.linear_measurements:
        lines.append(f"  {measurement.display_text()}")

    return "\n".join(lines)


def _append(
    lines: list[str],
    label: str,
    value: float | None,
    suffix: str,
    *,
    decimals: int = 1,
) -> None:
    if value is None:
        return
    unit = f" {suffix}" if suffix else ""
    lines.append(f"{label}: {value:.{decimals}f}{unit}")
