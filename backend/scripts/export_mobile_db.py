"""Export a slim, pre-populated SQLite for the mobile app to bundle.

The mobile app (Expo, standalone — no FastAPI backend) ships
`mobile/assets/rinnegan_initial.db` and copies it to the device's
writable storage on first launch. After that, the app reads/writes
locally. This script generates that file from the current backend DB.

What we include:
  - teams: full table (catalog)
  - matches: only rows with home_goals NOT NULL (played matches with
    results — used for team form/xG averages)
  - fixtures: snapshot of upcoming matches per league via the running
    backend's /api/fixtures endpoint (best-effort — needs backend up
    on localhost:8000; if down, the table is created empty)

What we DON'T include (empty schemas):
  - predictions, bets, bankroll_snapshots: user-local state, starts
    empty so each install begins with $0 bankroll
  - data_cache, model_performance, alembic_version: backend-only

Usage:
    cd backend && source venv/bin/activate
    python scripts/export_mobile_db.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

try:
    import requests  # type: ignore
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DB = REPO_ROOT / "backend" / "rinnegan.db"
DEST_DB = REPO_ROOT / "mobile" / "assets" / "rinnegan_initial.db"
BACKEND_URL = "http://localhost:8000"

# Same league codes / model families as core/leagues.py — duplicated
# here to keep this script importable without the backend package.
LEAGUE_CODES = ["PL", "PD", "BL1", "SA", "FL1", "CL", "LIB", "EC1"]


# Schemas — same shape as backend/db/models.py but inlined so this
# script has no Python import dependency on the backend package.
SCHEMA_SQL = """
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(120) NOT NULL,
    league VARCHAR(20) NOT NULL,
    country VARCHAR(60),
    football_data_id INTEGER,
    sofascore_id INTEGER,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE (slug, league)
);
CREATE INDEX ix_teams_name ON teams (name);
CREATE INDEX ix_teams_sofascore_id ON teams (sofascore_id);

CREATE TABLE matches (
    id INTEGER PRIMARY KEY,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    league VARCHAR(20) NOT NULL,
    match_date DATETIME NOT NULL,
    home_goals INTEGER,
    away_goals INTEGER,
    result VARCHAR(1),
    home_xg REAL,
    away_xg REAL,
    home_possession REAL,
    away_possession REAL,
    home_shots_on_target INTEGER,
    away_shots_on_target INTEGER,
    home_corners INTEGER,
    away_corners INTEGER,
    home_yellow_cards INTEGER,
    away_yellow_cards INTEGER,
    source VARCHAR(30) NOT NULL,
    external_id VARCHAR(60),
    fetched_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (home_team_id) REFERENCES teams (id),
    FOREIGN KEY (away_team_id) REFERENCES teams (id),
    UNIQUE (source, external_id)
);
CREATE INDEX ix_matches_home_team_date ON matches (home_team_id, match_date);
CREATE INDEX ix_matches_away_team_date ON matches (away_team_id, match_date);
CREATE INDEX ix_matches_league_date ON matches (league, match_date);

-- Fixtures: NEW table only in mobile (backend fetches live from SofaScore).
-- Snapshot bundled with the app; refreshed later via TODO refresh mechanism.
CREATE TABLE fixtures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league VARCHAR(20) NOT NULL,
    match_date DATETIME NOT NULL,
    home_team_id INTEGER,
    home_team_name VARCHAR(120) NOT NULL,
    away_team_id INTEGER,
    away_team_name VARCHAR(120) NOT NULL,
    fetched_at DATETIME NOT NULL,
    UNIQUE (league, match_date, home_team_name, away_team_name)
);
CREATE INDEX ix_fixtures_league_date ON fixtures (league, match_date);

CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    match_date DATETIME NOT NULL,
    league VARCHAR(20) NOT NULL,
    model_version VARCHAR(40) NOT NULL,
    pre_score REAL NOT NULL,
    implied_prob REAL NOT NULL,
    my_prob REAL NOT NULL,
    ev REAL NOT NULL,
    kelly_fraction REAL NOT NULL,
    quota REAL NOT NULL,
    stake REAL NOT NULL,
    verdict VARCHAR(20) NOT NULL,
    reasoning TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (home_team_id) REFERENCES teams (id),
    FOREIGN KEY (away_team_id) REFERENCES teams (id)
);
CREATE INDEX ix_predictions_match_date ON predictions (match_date);

CREATE TABLE bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL UNIQUE,
    quota_used REAL NOT NULL CHECK (quota_used > 1),
    stake_amount REAL NOT NULL CHECK (stake_amount > 0),
    placed_at DATETIME NOT NULL,
    outcome VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (outcome IN ('pending', 'won', 'lost', 'void')),
    payout_amount REAL,
    settled_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (prediction_id) REFERENCES predictions (id)
);
CREATE INDEX ix_bets_outcome ON bets (outcome);

CREATE TABLE bankroll_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    balance REAL NOT NULL,
    change_amount REAL NOT NULL,
    reason VARCHAR(30) NOT NULL CHECK (reason IN (
        'deposit', 'withdrawal', 'bet_won', 'bet_lost', 'bet_void', 'adjustment'
    )),
    related_bet_id INTEGER,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (related_bet_id) REFERENCES bets (id) ON DELETE SET NULL
);
CREATE INDEX ix_bankroll_snapshots_created_at ON bankroll_snapshots (created_at);
"""


def _copy_table(src: sqlite3.Connection, dest: sqlite3.Connection,
                table: str, where: str | None = None) -> int:
    """Copy rows from src.table to dest.table. Returns row count."""
    sql = f"SELECT * FROM {table}"
    if where:
        sql += f" WHERE {where}"
    rows = src.execute(sql).fetchall()
    if not rows:
        return 0
    # Get column names from first row (sqlite3.Row supports keys())
    cols = rows[0].keys()
    placeholders = ", ".join("?" for _ in cols)
    col_list = ", ".join(cols)
    insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    dest.executemany(insert_sql, [tuple(r) for r in rows])
    return len(rows)


def _fetch_fixtures_from_backend(dest: sqlite3.Connection) -> int:
    """Best-effort: pull fixtures for each league from the running backend."""
    if not HAS_REQUESTS:
        print("  ! requests not installed — skipping fixtures snapshot")
        return 0

    total = 0
    for code in LEAGUE_CODES:
        try:
            res = requests.get(
                f"{BACKEND_URL}/api/fixtures",
                params={"league": code, "days": 14, "limit": 50},
                timeout=10,
            )
            res.raise_for_status()
            data = res.json()
            fixtures = data.get("fixtures", [])
        except Exception as e:
            print(f"  ! {code}: skipped ({type(e).__name__}: {e})")
            continue

        if not fixtures:
            print(f"  - {code}: 0 fixtures")
            continue

        inserted = 0
        for f in fixtures:
            try:
                dest.execute(
                    """
                    INSERT OR IGNORE INTO fixtures
                    (league, match_date, home_team_id, home_team_name,
                     away_team_id, away_team_name, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        f["league"],
                        f["match_date"],
                        f.get("home_team_id"),
                        f["home_team_name"],
                        f.get("away_team_id"),
                        f["away_team_name"],
                    ),
                )
                inserted += 1
            except sqlite3.Error as e:
                print(f"  ! fixture insert failed: {e}")
        print(f"  - {code}: {inserted} fixtures")
        total += inserted

    return total


def main() -> int:
    if not SRC_DB.exists():
        print(f"ERROR: source DB not found at {SRC_DB}", file=sys.stderr)
        return 1

    DEST_DB.parent.mkdir(parents=True, exist_ok=True)
    if DEST_DB.exists():
        DEST_DB.unlink()
        print(f"removed previous {DEST_DB.name}")

    print(f"source: {SRC_DB}")
    print(f"dest:   {DEST_DB}")
    print()

    src = sqlite3.connect(f"file:{SRC_DB}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    dest = sqlite3.connect(DEST_DB)

    try:
        # 1. schema
        dest.executescript(SCHEMA_SQL)
        print("schema created")

        # 2. teams
        n_teams = _copy_table(src, dest, "teams")
        print(f"teams:   {n_teams} rows")

        # 3. matches (only with results)
        n_matches = _copy_table(
            src, dest, "matches", where="home_goals IS NOT NULL"
        )
        print(f"matches: {n_matches} rows (with results only)")

        # 4. fixtures via backend HTTP (best-effort)
        print("fixtures (via backend):")
        n_fixtures = _fetch_fixtures_from_backend(dest)
        print(f"fixtures: {n_fixtures} rows total")

        dest.commit()

        # 5. compact
        dest.execute("VACUUM")
        print("VACUUM done")

        size_mb = DEST_DB.stat().st_size / (1024 * 1024)
        print(f"\nfinal size: {size_mb:.2f} MB")
    finally:
        src.close()
        dest.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
