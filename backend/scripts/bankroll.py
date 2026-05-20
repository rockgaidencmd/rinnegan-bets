#!/usr/bin/env python3
"""Bankroll management CLI — deposit, withdraw, view status, see ROI.

Usage examples:
    python scripts/bankroll.py status
    python scripts/bankroll.py deposit 150
    python scripts/bankroll.py withdraw 30
    python scripts/bankroll.py roi
    python scripts/bankroll.py history
"""

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select

from core.bankroll.tracker import BankrollError, BankrollTracker
from db.database import SessionLocal
from db.models import BankrollSnapshot


def cmd_status(tracker: BankrollTracker) -> int:
    balance = tracker.get_current_balance()
    pending = tracker.get_pending_commitment()
    available = tracker.get_available_balance()

    print(f"\n  Balance total:      ${balance:>10.2f}")
    print(f"  Comprometido:        ${pending:>10.2f}  (apuestas pendientes)")
    print(f"  Disponible:          ${available:>10.2f}\n")
    return 0


def cmd_deposit(tracker: BankrollTracker, amount: float) -> int:
    snapshot = tracker.deposit(amount)
    print(f"  ✅ Depositado: ${amount:.2f}")
    print(f"  Nuevo balance: ${snapshot.balance:.2f}\n")
    return 0


def cmd_withdraw(tracker: BankrollTracker, amount: float) -> int:
    snapshot = tracker.withdraw(amount)
    print(f"  ✅ Retirado: ${amount:.2f}")
    print(f"  Nuevo balance: ${snapshot.balance:.2f}\n")
    return 0


def cmd_roi(tracker: BankrollTracker) -> int:
    report = tracker.compute_roi()
    print(f"\n  Apuestas liquidadas: {report.bets_settled}")
    print(f"    Ganadas: {report.bets_won}")
    print(f"    Perdidas: {report.bets_lost}")
    print(f"    Anuladas: {report.bets_void}")
    print(f"  Total apostado:      ${report.total_staked:.2f}")
    print(f"  Total retornado:     ${report.total_returned:.2f}")
    sign = "+" if report.net_profit >= 0 else ""
    print(f"  Ganancia neta:       {sign}${report.net_profit:.2f}")
    print(f"  ROI:                 {sign}{report.roi_pct:.2f}%\n")
    return 0


def cmd_history(tracker: BankrollTracker, session, limit: int = 20) -> int:
    rows = session.execute(
        select(BankrollSnapshot)
        .order_by(BankrollSnapshot.created_at.desc())
        .limit(limit)
    ).scalars().all()

    if not rows:
        print("\n  No hay movimientos todavía.\n")
        return 0

    print(f"\n  Últimos {len(rows)} movimientos:\n")
    print(f"  {'Fecha':<20} {'Razón':<14} {'Cambio':>12} {'Balance':>12}")
    print(f"  {'-'*60}")
    for s in rows:
        change_sign = "+" if s.change_amount >= 0 else ""
        date_str = s.created_at.strftime("%Y-%m-%d %H:%M")
        print(f"  {date_str:<20} {s.reason:<14} "
              f"{change_sign}{s.change_amount:>11.2f} ${s.balance:>11.2f}")
    print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Mostrar balance actual")

    dep = sub.add_parser("deposit", help="Depositar dinero")
    dep.add_argument("amount", type=float)

    wd = sub.add_parser("withdraw", help="Retirar dinero")
    wd.add_argument("amount", type=float)

    sub.add_parser("roi", help="Ver ROI acumulado")

    hist = sub.add_parser("history", help="Ver historial de movimientos")
    hist.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    session = SessionLocal()
    tracker = BankrollTracker(session)

    try:
        if args.cmd == "status":
            return cmd_status(tracker)
        if args.cmd == "deposit":
            return cmd_deposit(tracker, args.amount)
        if args.cmd == "withdraw":
            return cmd_withdraw(tracker, args.amount)
        if args.cmd == "roi":
            return cmd_roi(tracker)
        if args.cmd == "history":
            return cmd_history(tracker, session, args.limit)
        return 1
    except BankrollError as e:
        print(f"\n  ❌ {e}\n")
        return 2
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
