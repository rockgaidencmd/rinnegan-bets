"""Kelly Criterion + Expected Value + Verdict logic.

Pure functions. Math validated by unit tests with known edge cases.

References:
    Kelly, J. L. (1956). "A New Interpretation of Information Rate".
    Cap (max 25%) is convention to avoid ruin from variance.
"""

from core.types import (
    EV,
    Apostar,
    Esperar,
    KellyFraction,
    NoApostar,
    Odds,
    Probability,
    Stake,
    Verdict,
)


# Decision thresholds (tunable; documented in plan).
EV_APOSTAR_MIN = 0.05      # Need >5% expected profit to recommend bet
KELLY_APOSTAR_MIN = 0.02   # AND at least 2% of bankroll
KELLY_CAP = 0.25           # Never bet more than 25% even if Kelly says more


def compute_ev(prob: Probability, odds: Odds, stake: Stake) -> EV:
    """Expected Value of the bet.

        EV = p * (odds - 1) * stake  -  (1 - p) * stake

    Positive EV → long-run profitable. Negative EV → don't bet.
    """
    gain_if_win = (odds - 1.0) * stake
    loss_if_lose = stake
    ev = prob * gain_if_win - (1.0 - prob) * loss_if_lose
    return EV(ev)


def kelly_fraction(
    prob: Probability, odds: Odds, cap: float = KELLY_CAP,
) -> KellyFraction:
    """Kelly Criterion: fraction of bankroll to bet for optimal log-growth.

        f* = (b * p - q) / b   where b = odds - 1, q = 1 - p

    Returns 0 when:
    - No edge (negative Kelly)
    - Odds <= 1 (no payout above stake)
    Caps at `cap` (default 0.25) to limit drawdown from variance.
    """
    b = odds - 1.0
    if b <= 0 or prob <= 0:
        return KellyFraction(0.0)

    q = 1.0 - prob
    f_star = (b * prob - q) / b

    if f_star <= 0:
        return KellyFraction(0.0)

    return KellyFraction(min(f_star, cap))


def verdict_from_ev_kelly(
    ev: EV, kelly: KellyFraction, reason_context: str = "",
) -> Verdict:
    """Decide based on EV and Kelly thresholds.

    - APOSTAR: ev > EV_APOSTAR_MIN AND kelly > KELLY_APOSTAR_MIN
    - ESPERAR: any positive signal but below the bet threshold
    - NO_APOSTAR: zero/negative signal
    """
    if ev > EV_APOSTAR_MIN and kelly > KELLY_APOSTAR_MIN:
        return Apostar(reason=f"EV={ev:.2f}, Kelly={kelly:.2%}. {reason_context}".strip())

    if ev > 0 or kelly > 0:
        return Esperar(
            reason=f"Marginal: EV={ev:.2f}, Kelly={kelly:.2%}. {reason_context}".strip()
        )

    return NoApostar(reason=f"No edge: EV={ev:.2f}. {reason_context}".strip())
