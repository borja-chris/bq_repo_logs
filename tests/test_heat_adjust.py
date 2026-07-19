from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


def load_module():
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    module_path = scripts_dir / "heat_adjust.py"
    spec = importlib.util.spec_from_file_location("heat_adjust_under_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load heat_adjust.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


h = load_module()


class HeatAdjustTest(unittest.TestCase):
    def test_heat_load_sum_rounds_to_int(self) -> None:
        self.assertEqual(h.heat_load_sum(92.0, 71.0), 163)
        self.assertEqual(h.heat_load_sum(87.4, 60.6), 148)

    def test_pace_adjust_fraction_band_boundaries(self) -> None:
        self.assertEqual(h.pace_adjust_fraction(100), 0.0)
        self.assertEqual(h.pace_adjust_fraction(101), 0.0025)
        self.assertEqual(h.pace_adjust_fraction(110), 0.0025)
        self.assertEqual(h.pace_adjust_fraction(111), 0.0075)
        self.assertEqual(h.pace_adjust_fraction(163), 0.07)
        self.assertEqual(h.pace_adjust_fraction(180), 0.09)
        self.assertEqual(h.pace_adjust_fraction(181), 0.09)

    def test_heat_band_label(self) -> None:
        self.assertEqual(h.heat_band_label(100), "none")
        self.assertEqual(h.heat_band_label(115), "light")
        self.assertEqual(h.heat_band_label(135), "moderate")
        self.assertEqual(h.heat_band_label(163), "heavy")
        self.assertEqual(h.heat_band_label(175), "severe")
        self.assertEqual(h.heat_band_label(181), "hard-not-recommended")

    def test_heat_neutral_pace_worked_example(self) -> None:
        # ran 9:20/mi = 560 s/mi, sum 163 -> 7% -> 560 / 1.07 = 523 s = 8:43/mi
        fraction = h.pace_adjust_fraction(163)
        self.assertEqual(h.heat_neutral_pace_seconds(560, fraction), 523)

    def test_heat_neutral_pace_zero_fraction_is_identity(self) -> None:
        self.assertEqual(h.heat_neutral_pace_seconds(560, 0.0), 560)


if __name__ == "__main__":
    unittest.main()
