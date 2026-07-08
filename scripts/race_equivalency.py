"""Race-equivalency and training-pace calculator.

Reverse-engineered from the Luke Humphrey Running (Hansons) Race Equivalency
Calculator so the repo can anchor plan paces to a measured race instead of a
top-down goal time.

Two things were confirmed empirically against the live LHR calculator
(POST inputs, read outputs, fit the constants):

1. Race equivalency uses Pete Riegel's endurance model:

       T2 = T1 * (D2 / D1) ** 1.06

   The exponent fits to 1.060 across 10k -> marathon (the 1-mile drifts to
   ~1.08, the known short-distance deviation of Riegel; see MILE_EXPONENT).

2. Training paces are fixed offsets from the *equivalent* race paces:

       Easy            = Marathon pace + 1:30 .. + 2:30 /mi
       Moderate        = Marathon pace + 1:00 .. + 2:00 /mi
       Long run        = Marathon pace + 0:30 .. + 2:00 /mi
       Strength        = Marathon pace - 0:10 /mi
       Marathon tempo  = Marathon pace
       Half tempo (HMP)= Half-marathon pace
       Lactate thresh  = 10k pace .. Half-marathon pace
       Speed           = 5k pace .. 10k pace
       VO2max          = 3k pace .. 5k pace
       Strides         = 1-mile pace - 0:30 .. 1-mile pace

Both relationships were verified at two fitness levels (25:30 and 20:00 5k)
and held identically, so they are structural, not curve-fit to one point.

Usage:

    .venv/bin/python scripts/race_equivalency.py 5k 25:30
    .venv/bin/python scripts/race_equivalency.py half 1:33:00
    .venv/bin/python scripts/race_equivalency.py --distance-m 5021 22:10
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

# Pete Riegel fatigue exponent, confirmed exact against the LHR calculator
# from 5k up (10k -> marathon all fit k=1.060 within 1s).
RIEGEL_EXPONENT = 1.06
# Below 5k the LHR model steepens; k~1.08 fits the 1-mile and 3k exactly, and
# the 2-mile / 4k to within ~5s. Sub-5k equivalents are therefore approximate.
SHORT_EXPONENT = 1.08
SHORT_DISTANCE_M = 5000.0

METERS_PER_MILE = 1609.34

# Standard equivalency ladder, in meters. Values match the LHR dropdown.
STANDARD_DISTANCES: list[tuple[str, float]] = [
    ("1 Mile", 1609.34),
    ("3k", 3000.0),
    ("2 Miles", 3218.68),
    ("5k", 5000.0),
    ("8k", 8000.0),
    ("10k", 10000.0),
    ("12k", 12000.0),
    ("15k", 15000.0),
    ("10 Miles", 16090.34),
    ("20k", 20000.0),
    ("Half Marathon", 21097.49),
    ("25k", 25000.0),
    ("30k", 30000.0),
    ("Marathon", 42194.99),
]

# Aliases accepted on the command line -> distance in meters.
DISTANCE_ALIASES: dict[str, float] = {
    "mile": 1609.34,
    "1mile": 1609.34,
    "3k": 3000.0,
    "2mile": 3218.68,
    "5k": 5000.0,
    "8k": 8000.0,
    "10k": 10000.0,
    "12k": 12000.0,
    "15k": 15000.0,
    "10mile": 16090.34,
    "20k": 20000.0,
    "half": 21097.49,
    "halfmarathon": 21097.49,
    "hm": 21097.49,
    "25k": 25000.0,
    "30k": 30000.0,
    "marathon": 42194.99,
    "full": 42194.99,
}


def parse_time(text: str) -> float:
    """Parse ``H:MM:SS``, ``MM:SS``, or ``SS`` into seconds."""
    parts = text.strip().split(":")
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"unrecognized time: {text!r}")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def fmt_time(seconds: float) -> str:
    seconds = round(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def fmt_pace(seconds_per_mile: float) -> str:
    seconds_per_mile = round(seconds_per_mile)
    minutes, secs = divmod(seconds_per_mile, 60)
    return f"{minutes}:{secs:02d}"


def riegel(t1: float, d1: float, d2: float) -> float:
    """Predict time over d2 (meters) from a t1 (seconds) effort over d1."""
    exponent = SHORT_EXPONENT if d2 < SHORT_DISTANCE_M else RIEGEL_EXPONENT
    return t1 * (d2 / d1) ** exponent


@dataclass
class Equivalent:
    name: str
    distance_m: float
    seconds: float

    @property
    def pace_per_mile(self) -> float:
        return self.seconds / (self.distance_m / METERS_PER_MILE)


def equivalents(t1: float, d1: float) -> list[Equivalent]:
    return [
        Equivalent(name, dist, riegel(t1, d1, dist))
        for name, dist in STANDARD_DISTANCES
    ]


def pace_of(rows: list[Equivalent], name: str) -> float:
    for row in rows:
        if row.name == name:
            return row.pace_per_mile
    raise KeyError(name)


@dataclass
class PaceBand:
    label: str
    low: float  # faster bound, seconds per mile
    high: float  # slower bound, seconds per mile

    def render(self) -> str:
        if round(self.low) == round(self.high):
            return fmt_pace(self.low)
        return f"{fmt_pace(self.low)} - {fmt_pace(self.high)}"


def training_paces(rows: list[Equivalent]) -> list[PaceBand]:
    """Derive Hansons training paces from equivalent race paces."""
    mile = pace_of(rows, "1 Mile")
    p3k = pace_of(rows, "3k")
    p5k = pace_of(rows, "5k")
    p10k = pace_of(rows, "10k")
    hm = pace_of(rows, "Half Marathon")
    mp = pace_of(rows, "Marathon")
    return [
        PaceBand("Easy", mp + 90, mp + 150),
        PaceBand("Moderate", mp + 60, mp + 120),
        PaceBand("Long run", mp + 30, mp + 120),
        PaceBand("Speed (5k-10k)", p5k, p10k),
        PaceBand("VO2max (3k-5k)", p3k, p5k),
        PaceBand("Lactate threshold (10k-HM)", p10k, hm),
        PaceBand("Strength (MP-10s)", mp - 10, mp - 10),
        PaceBand("Half tempo / HMP", hm, hm),
        PaceBand("Marathon tempo", mp, mp),
        PaceBand("Strides", mile - 30, mile),
    ]


def resolve_distance(args: argparse.Namespace) -> tuple[str, float]:
    if args.distance_m is not None:
        return (f"{args.distance_m:g} m", float(args.distance_m))
    key = args.distance.lower().replace(" ", "").replace("-", "")
    if key not in DISTANCE_ALIASES:
        raise SystemExit(
            f"unknown distance {args.distance!r}; "
            f"use one of {sorted(set(DISTANCE_ALIASES))} or --distance-m"
        )
    return (args.distance, DISTANCE_ALIASES[key])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "distance",
        nargs="?",
        default="5k",
        help="race distance alias (5k, 10k, half, marathon, ...)",
    )
    parser.add_argument("time", help="race time as H:MM:SS, MM:SS, or seconds")
    parser.add_argument(
        "--distance-m",
        type=float,
        default=None,
        help="custom race distance in meters (overrides the alias)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    name, d1 = resolve_distance(args)
    t1 = parse_time(args.time)

    rows = equivalents(t1, d1)
    pace_in = t1 / (d1 / METERS_PER_MILE)

    print(f"Input: {name}  {fmt_time(t1)}  ({fmt_pace(pace_in)}/mi)")
    print()
    print("Equivalent race performances (Riegel k=1.06):")
    print(f"  {'Distance':<16}{'Time':>10}{'Pace/mi':>10}")
    for row in rows:
        print(f"  {row.name:<16}{fmt_time(row.seconds):>10}{fmt_pace(row.pace_per_mile):>10}")
    print()
    print("Training paces (Hansons offsets from equivalent race pace):")
    for band in training_paces(rows):
        print(f"  {band.label:<28}{band.render():>13}/mi")


if __name__ == "__main__":
    main()
