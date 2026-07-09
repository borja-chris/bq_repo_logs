from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


def load_module():
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    module_path = scripts_dir / "monthly_archive.py"
    spec = importlib.util.spec_from_file_location(
        "monthly_archive_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load monthly_archive.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ma = load_module()
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import weekly_entries  # noqa: E402


def daily_log_text(
    planned: str = "",
    completed: str = "",
    time: str = "",
    distance: str = "",
    pace: str = "",
    effort: str = "",
    manual_note: str = "",
) -> str:
    return (
        "# Daily Log\n\n"
        "## Run\n\n"
        f"- Planned: {planned}\n"
        f"- Completed: {completed}\n"
        f"- Time: {time}\n"
        f"- Distance: {distance}\n"
        f"- Pace: {pace}\n"
        f"- Effort: {effort}\n\n"
        "## Managed Notes\n\n"
        "- \n\n"
        "## Manual Notes\n\n"
        f"- {manual_note}\n\n"
        "## Recovery Signals\n\n"
        "- Sleep:\n"
        "- Soreness:\n"
        "- Stress:\n"
        "- Warning signs:\n"
    )


class MoveAndArchiveTest(unittest.TestCase):
    def test_moves_prior_month_leaves_current_month(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            daily_root = Path(tmp)
            prior = daily_root / "2026-06-15.md"
            prior.write_text(
                daily_log_text(
                    completed="4.00 mi run",
                    time="35:00",
                    distance="4.00 mi",
                    effort="imported",
                )
            )
            current = daily_root / "2026-07-01.md"
            current.write_text(daily_log_text())

            results = ma.run_monthly_archive(date(2026, 7, 8), daily_root=daily_root)

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["month"], "2026-06")
            self.assertFalse(prior.exists())
            self.assertTrue(current.exists())
            archived = daily_root / "2026" / "2026-06" / "2026-06-15.md"
            self.assertTrue(archived.exists())
            summary_path = daily_root / "2026" / "2026-06" / "monthly_summary.md"
            self.assertTrue(summary_path.exists())
            self.assertEqual(results[0]["summary_path"], summary_path)
            self.assertEqual(results[0]["moved"], [date(2026, 6, 15)])


class AggregatesTest(unittest.TestCase):
    def test_header_aggregates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            daily_root = Path(tmp)
            (daily_root / "2026-05-01.md").write_text(
                daily_log_text(
                    completed="3.00 mi run",
                    time="30:00",
                    distance="3.00 mi",
                    effort="imported",
                )
            )
            (daily_root / "2026-05-02.md").write_text(
                daily_log_text(
                    completed="6.00 mi run",
                    time="1:00:00",
                    distance="6.00 mi",
                    effort="imported",
                )
            )
            (daily_root / "2026-05-03.md").write_text(
                daily_log_text(completed="off", effort="off")
            )

            results = ma.run_monthly_archive(date(2026, 6, 1), daily_root=daily_root)

            self.assertEqual(len(results), 1)
            summary_text = results[0]["summary_path"].read_text()
            self.assertIn("Daily logs archived: `3`", summary_text)
            self.assertIn("Logged run days: `2`", summary_text)
            self.assertIn("Total mileage: `9.00 mi`", summary_text)
            # 30:00 + 1:00:00 = 1:30:00
            self.assertIn("Total logged time: `1:30:00`", summary_text)
            # 5400s / 9mi = 600s/mi = 10:00/mi
            self.assertIn("Average pace across logged miles: `10:00/mi`", summary_text)
            self.assertIn("Longest logged run: `6.00 mi` on `2026-05-02`", summary_text)


class IdempotencyTest(unittest.TestCase):
    def test_second_run_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            daily_root = Path(tmp)
            (daily_root / "2026-06-15.md").write_text(
                daily_log_text(
                    completed="4.00 mi run",
                    time="35:00",
                    distance="4.00 mi",
                    effort="imported",
                )
            )

            first = ma.run_monthly_archive(date(2026, 7, 8), daily_root=daily_root)
            self.assertEqual(len(first), 1)

            second = ma.run_monthly_archive(date(2026, 7, 8), daily_root=daily_root)
            self.assertEqual(second, [])


class GoldenJuneTest(unittest.TestCase):
    def test_reproduces_committed_june_summary_byte_for_byte(self) -> None:
        # The committed June summary is the deterministic output of
        # render_monthly_summary (verbatim manual notes, not hand-paraphrased),
        # so the archiver must reproduce it exactly. This guards the whole
        # summary format — header stats and every table cell — against drift.
        repo_root = Path(__file__).resolve().parents[1]
        june_dir = repo_root / "logs" / "daily" / "2026" / "2026-06"
        golden_text = (june_dir / "monthly_summary.md").read_text()

        entries = ma.archived_month_entries(repo_root / "logs" / "daily", date(2026, 6, 1))
        rendered = ma.render_monthly_summary("2026-06", entries)

        self.assertEqual(golden_text, rendered)


class RefactorSafetyTest(unittest.TestCase):
    def test_parse_daily_log_text_round_trips_sample_log(self) -> None:
        text = daily_log_text(
            planned="5 mi easy",
            completed="5.00 mi run",
            time="45:00",
            distance="5.00 mi",
            pace="9:00/mi",
            effort="imported",
            manual_note="Felt good.",
        )
        entry = weekly_entries.parse_daily_log_text(date(2026, 6, 1), text)
        self.assertEqual(entry.planned, "5 mi easy")
        self.assertEqual(entry.completed, "5.00 mi run")
        self.assertEqual(entry.time, "45:00")
        self.assertEqual(entry.distance, "5.00 mi")
        self.assertEqual(entry.pace, "9:00/mi")
        self.assertEqual(entry.effort, "imported")
        self.assertEqual(entry.notes, "Felt good.")


if __name__ == "__main__":
    unittest.main()
