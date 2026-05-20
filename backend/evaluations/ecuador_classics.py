#!/usr/bin/env python3
"""Evaluate the Ecuador model with classic Liga Pro matchups.

Useful to spot-check whether the model gives sensible verdicts for
games tu hermano knows well.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import subprocess


CLASICOS = [
    ("Barcelona SC", "Emelec", 2.10, "El Clásico del Astillero"),
    ("LDU", "Aucas", 1.85, "Clásico Capitalino"),
    ("Independiente del Valle", "LDU", 2.30, "Top vs Top"),
    ("Emelec", "Independiente del Valle", 2.50, "Astillero vs Valle"),
    ("Barcelona SC", "Aucas", 1.95, "BSC en Quito"),
]


def main() -> int:
    print(f"\n{'═' * 70}")
    print(f"  ECUADOR LIGA PRO — Clásicos")
    print(f"{'═' * 70}\n")

    script = BACKEND_DIR / "scripts" / "predict_match.py"

    for home, away, quota, note in CLASICOS:
        print(f"\n>>> {note}")
        subprocess.run(
            [sys.executable, str(script), home, away,
             "--quota", str(quota), "--stake", "10",
             "--importance", "clasif"],
            cwd=BACKEND_DIR,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
