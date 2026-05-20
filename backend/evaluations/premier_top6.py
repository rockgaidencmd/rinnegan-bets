#!/usr/bin/env python3
"""Evaluate Europe model with Premier League Big 6 matchups."""

import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


BIG_SIX_MATCHES = [
    ("Arsenal", "Manchester City", 2.50, "Title race"),
    ("Liverpool", "Chelsea", 1.90, "Big 6 clash"),
    ("Manchester United", "Tottenham", 2.10, "European spots"),
    ("Manchester City", "Liverpool", 1.85, "Classic rivalry"),
    ("Arsenal", "Tottenham", 1.75, "North London Derby"),
    ("Chelsea", "Arsenal", 2.40, "London Derby"),
]


def main() -> int:
    print(f"\n{'═' * 70}")
    print(f"  PREMIER LEAGUE — Big 6")
    print(f"{'═' * 70}\n")

    script = BACKEND_DIR / "scripts" / "predict_match.py"
    for home, away, quota, note in BIG_SIX_MATCHES:
        print(f"\n>>> {note}")
        subprocess.run(
            [sys.executable, str(script), home, away,
             "--quota", str(quota), "--stake", "10"],
            cwd=BACKEND_DIR,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
