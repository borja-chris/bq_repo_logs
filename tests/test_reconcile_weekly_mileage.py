from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace


def load_module():
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    module_path = scripts_dir / "reconcile_weekly_mileage.py"
    spec = importlib.util.spec_from_file_location(
        "reconcile_weekly_mileage_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load reconcile_weekly_mileage.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


r = load_module()


class ReconcileWeeklyMileageTest(unittest.TestCase):
    def test_parse_logged_mileage_reads_the_value(self) -> None:
        text = "- Target mileage: `40`\n- Actual mileage so far: `22.95`\n- Status: `x`"
        self.assertEqual(r.parse_logged_mileage(text), 22.95)

    def test_parse_logged_mileage_missing_returns_none(self) -> None:
        self.assertIsNone(r.parse_logged_mileage("no mileage line here"))

    def test_reconcile_week_matches_when_totals_agree(self) -> None:
        activities = [SimpleNamespace(distance_mi=5.0), SimpleNamespace(distance_mi=3.5)]
        text = "- Actual mileage so far: `8.50`"
        result = r.reconcile_week(date(2026, 6, 22), text, activities)
        self.assertTrue(result.matches)
        self.assertEqual(result.logged, 8.50)
        self.assertEqual(result.expected, 8.50)

    def test_reconcile_week_flags_mismatch_with_both_values(self) -> None:
        activities = [SimpleNamespace(distance_mi=5.0), SimpleNamespace(distance_mi=3.5)]
        text = "- Actual mileage so far: `4.00`"
        result = r.reconcile_week(date(2026, 6, 22), text, activities)
        self.assertFalse(result.matches)
        self.assertEqual(result.logged, 4.00)
        self.assertEqual(result.expected, 8.50)
        line = r.format_result(result)
        self.assertIn("2026-06-22", line)
        self.assertIn("4.00", line)
        self.assertIn("8.50", line)

    def test_reconcile_week_missing_logged_line_is_a_mismatch(self) -> None:
        activities = [SimpleNamespace(distance_mi=6.0)]
        result = r.reconcile_week(date(2026, 6, 22), "no mileage here", activities)
        self.assertFalse(result.matches)
        self.assertIsNone(result.logged)
        self.assertEqual(result.expected, 6.0)
        self.assertIn("missing", r.format_result(result))

    def test_reconcile_week_rounds_to_two_decimals(self) -> None:
        # 5.765 + 3.114 = 8.879 -> 8.88; a log rounded to 8.88 should match.
        activities = [SimpleNamespace(distance_mi=5.765), SimpleNamespace(distance_mi=3.114)]
        text = "- Actual mileage so far: `8.88`"
        self.assertTrue(r.reconcile_week(date(2026, 6, 22), text, activities).matches)


if __name__ == "__main__":
    unittest.main()
