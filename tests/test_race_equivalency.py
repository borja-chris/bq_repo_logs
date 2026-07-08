from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest


def load_module():
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    module_path = scripts_dir / "race_equivalency.py"
    spec = importlib.util.spec_from_file_location(
        "race_equivalency_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load race_equivalency.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


m = load_module()


def seconds_by_name(rows, name: str) -> float:
    for row in rows:
        if row.name == name:
            return row.seconds
    raise KeyError(name)


def pace_by_name(rows, name: str) -> float:
    for row in rows:
        if row.name == name:
            return row.pace_per_mile
    raise KeyError(name)


def band_by_label(bands, label_substr: str):
    matches = [b for b in bands if label_substr.lower() in b.label.lower()]
    if not matches:
        raise KeyError(label_substr)
    if len(matches) > 1:
        raise AssertionError(
            f"label substring {label_substr!r} matched multiple bands: "
            f"{[b.label for b in matches]}"
        )
    return matches[0]


class TimeFormattingTest(unittest.TestCase):
    def test_parse_time_variants(self) -> None:
        self.assertEqual(m.parse_time("1:33:00"), 5580)
        self.assertEqual(m.parse_time("25:30"), 1530)
        self.assertEqual(m.parse_time("45"), 45)

    def test_fmt_time_round_trips(self) -> None:
        self.assertEqual(m.fmt_time(5580), "1:33:00")
        self.assertEqual(m.fmt_time(1530), "25:30")
        self.assertEqual(m.fmt_time(m.parse_time("1:33:00")), "1:33:00")
        self.assertEqual(m.fmt_time(m.parse_time("25:30")), "25:30")

    def test_fmt_pace(self) -> None:
        self.assertEqual(m.fmt_pace(510), "8:30")


class EquivalencyReferenceTest(unittest.TestCase):
    """LHR calculator reference times for a 25:30 5k input."""

    # name -> reference time string from the live LHR calculator
    REFERENCES = {
        "1 Mile": "7:29",
        "3k": "14:41",
        "5k": "25:30",
        "8k": "41:58",
        "10k": "53:09",
        "12k": "1:04:30",
        "15k": "1:21:42",
        "10 Miles": "1:28:02",
        "20k": "1:50:50",
        "Half Marathon": "1:57:18",
        "25k": "2:20:25",
        "30k": "2:50:21",
        "Marathon": "4:04:34",
    }

    def setUp(self) -> None:
        self.rows = m.equivalents(1530, 5000)

    def test_equivalent_times_match_lhr(self) -> None:
        for name, ref_str in self.REFERENCES.items():
            expected = m.parse_time(ref_str)
            actual = seconds_by_name(self.rows, name)
            dist = next(r.distance_m for r in self.rows if r.name == name)
            tol = 2 if dist >= 5000 else 6
            self.assertLessEqual(
                abs(actual - expected),
                tol,
                msg=(
                    f"{name}: expected {ref_str} ({expected}s), "
                    f"got {m.fmt_time(actual)} ({actual:.1f}s), tol={tol}s"
                ),
            )


class TrainingPaceReferenceTest(unittest.TestCase):
    """LHR training-pace bands for a 25:30 5k input, +/-2 s/mi per bound."""

    def setUp(self) -> None:
        self.bands = m.training_paces(m.equivalents(1530, 5000))

    def _assert_band(self, label_substr, low_str, high_str=None) -> None:
        band = band_by_label(self.bands, label_substr)
        exp_low = m.parse_time(low_str)
        exp_high = m.parse_time(high_str) if high_str is not None else exp_low
        self.assertLessEqual(
            abs(band.low - exp_low),
            2,
            msg=f"{band.label} low: expected {low_str} ({exp_low}s/mi), got {m.fmt_pace(band.low)} ({band.low:.1f})",
        )
        self.assertLessEqual(
            abs(band.high - exp_high),
            2,
            msg=f"{band.label} high: expected {high_str} ({exp_high}s/mi), got {m.fmt_pace(band.high)} ({band.high:.1f})",
        )

    def test_easy(self) -> None:
        self._assert_band("Easy", "10:49", "11:49")

    def test_moderate(self) -> None:
        self._assert_band("Moderate", "10:19", "11:19")

    def test_long_run(self) -> None:
        self._assert_band("Long run", "9:49", "11:19")

    def test_speed(self) -> None:
        self._assert_band("Speed", "8:12", "8:33")

    def test_vo2max(self) -> None:
        self._assert_band("VO2max", "7:52", "8:12")

    def test_lactate_threshold(self) -> None:
        self._assert_band("Lactate threshold", "8:33", "8:55")

    def test_strength_single(self) -> None:
        band = band_by_label(self.bands, "Strength")
        self.assertEqual(round(band.low), round(band.high))
        self._assert_band("Strength", "9:09")

    def test_half_tempo_single(self) -> None:
        band = band_by_label(self.bands, "Half tempo")
        self.assertEqual(round(band.low), round(band.high))
        self._assert_band("Half tempo", "8:56")

    def test_marathon_tempo_single(self) -> None:
        band = band_by_label(self.bands, "Marathon tempo")
        self.assertEqual(round(band.low), round(band.high))
        self._assert_band("Marathon tempo", "9:19")

    def test_strides(self) -> None:
        self._assert_band("Strides", "6:59", "7:29")


class StructuralOffsetInvariantTest(unittest.TestCase):
    """Offsets are structural and must hold at any fitness (20:00 5k here)."""

    TOL = 0.5

    def setUp(self) -> None:
        self.rows = m.equivalents(1200, 5000)
        self.bands = m.training_paces(self.rows)
        self.mp = pace_by_name(self.rows, "Marathon")
        self.hm = pace_by_name(self.rows, "Half Marathon")
        self.p5k = pace_by_name(self.rows, "5k")
        self.p10k = pace_by_name(self.rows, "10k")
        self.p3k = pace_by_name(self.rows, "3k")
        self.mile = pace_by_name(self.rows, "1 Mile")

    def test_easy_offsets(self) -> None:
        band = band_by_label(self.bands, "Easy")
        self.assertAlmostEqual(band.low, self.mp + 90, delta=self.TOL)
        self.assertAlmostEqual(band.high, self.mp + 150, delta=self.TOL)

    def test_moderate_offsets(self) -> None:
        band = band_by_label(self.bands, "Moderate")
        self.assertAlmostEqual(band.low, self.mp + 60, delta=self.TOL)
        self.assertAlmostEqual(band.high, self.mp + 120, delta=self.TOL)

    def test_long_run_offsets(self) -> None:
        band = band_by_label(self.bands, "Long run")
        self.assertAlmostEqual(band.low, self.mp + 30, delta=self.TOL)
        self.assertAlmostEqual(band.high, self.mp + 120, delta=self.TOL)

    def test_strength_offset(self) -> None:
        band = band_by_label(self.bands, "Strength")
        self.assertAlmostEqual(band.low, self.mp - 10, delta=self.TOL)
        self.assertAlmostEqual(band.high, self.mp - 10, delta=self.TOL)

    def test_marathon_tempo_offset(self) -> None:
        band = band_by_label(self.bands, "Marathon tempo")
        self.assertAlmostEqual(band.low, self.mp, delta=self.TOL)
        self.assertAlmostEqual(band.high, self.mp, delta=self.TOL)

    def test_half_tempo_offset(self) -> None:
        band = band_by_label(self.bands, "Half tempo")
        self.assertAlmostEqual(band.low, self.hm, delta=self.TOL)
        self.assertAlmostEqual(band.high, self.hm, delta=self.TOL)

    def test_lactate_threshold_offset(self) -> None:
        band = band_by_label(self.bands, "Lactate threshold")
        self.assertAlmostEqual(band.low, self.p10k, delta=self.TOL)
        self.assertAlmostEqual(band.high, self.hm, delta=self.TOL)

    def test_speed_offset(self) -> None:
        band = band_by_label(self.bands, "Speed")
        self.assertAlmostEqual(band.low, self.p5k, delta=self.TOL)
        self.assertAlmostEqual(band.high, self.p10k, delta=self.TOL)

    def test_vo2max_offset(self) -> None:
        band = band_by_label(self.bands, "VO2max")
        self.assertAlmostEqual(band.low, self.p3k, delta=self.TOL)
        self.assertAlmostEqual(band.high, self.p5k, delta=self.TOL)


class RiegelExponentTest(unittest.TestCase):
    def test_long_distance_exponent_is_1_06(self) -> None:
        import math

        t1, d1, d2 = 1200.0, 5000.0, 10000.0
        t2 = m.riegel(t1, d1, d2)
        recovered = math.log(t2 / t1) / math.log(d2 / d1)
        self.assertAlmostEqual(recovered, m.RIEGEL_EXPONENT, delta=0.001)
        self.assertAlmostEqual(recovered, 1.06, delta=0.001)

    def test_short_distance_exponent_is_1_08(self) -> None:
        import math

        t1, d1, d2 = 1200.0, 5000.0, 1609.34  # 5k -> mile
        t2 = m.riegel(t1, d1, d2)
        recovered = math.log(t2 / t1) / math.log(d2 / d1)
        self.assertAlmostEqual(recovered, m.SHORT_EXPONENT, delta=0.001)
        self.assertAlmostEqual(recovered, 1.08, delta=0.001)


class ConstantsTest(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertAlmostEqual(m.RIEGEL_EXPONENT, 1.06)
        self.assertAlmostEqual(m.SHORT_EXPONENT, 1.08)
        self.assertAlmostEqual(m.METERS_PER_MILE, 1609.34)


if __name__ == "__main__":
    unittest.main()
