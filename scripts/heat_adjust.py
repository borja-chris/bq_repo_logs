from __future__ import annotations

# Mark Hadley temperature + dew point pace-adjustment chart.
# sum = temp_f + dew_point_f -> pace slowdown fraction (midpoint of band).
# Each entry: (inclusive upper bound of sum, fraction, label).
_BANDS: list[tuple[int, float, str]] = [
    (100, 0.0, "none"),
    (110, 0.0025, "light"),
    (120, 0.0075, "light"),
    (130, 0.015, "moderate"),
    (140, 0.025, "moderate"),
    (150, 0.0375, "heavy"),
    (160, 0.0525, "heavy"),
    (170, 0.07, "heavy"),
    (180, 0.09, "severe"),
]
_ABOVE_MAX = (0.09, "hard-not-recommended")


def heat_load_sum(temp_f: float, dew_point_f: float) -> int:
    return round(temp_f + dew_point_f)


def _band(load_sum: int) -> tuple[float, str]:
    for upper, fraction, label in _BANDS:
        if load_sum <= upper:
            return fraction, label
    return _ABOVE_MAX


def pace_adjust_fraction(load_sum: int) -> float:
    return _band(load_sum)[0]


def heat_band_label(load_sum: int) -> str:
    return _band(load_sum)[1]


def heat_neutral_pace_seconds(actual_sec_per_mi: int, fraction: float) -> int:
    return round(actual_sec_per_mi / (1 + fraction))
