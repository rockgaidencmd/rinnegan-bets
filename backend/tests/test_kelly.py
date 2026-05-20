"""Tests for Kelly Criterion + EV + Verdict logic.

These tests verify the math against known scenarios — wrong math here
means real money lost, so coverage is non-negotiable.
"""

import pytest

from core.bankroll.kelly import (
    EV_APOSTAR_MIN,
    KELLY_APOSTAR_MIN,
    KELLY_CAP,
    compute_ev,
    kelly_fraction,
    verdict_from_ev_kelly,
)
from core.types import (
    EV,
    Apostar,
    Esperar,
    KellyFraction,
    NoApostar,
    Odds,
    Probability,
    Stake,
)


# --- compute_ev ---

class TestComputeEV:

    def test_fair_coin_at_even_odds_is_zero_ev(self):
        """50% chance × 2.0 odds × $10 stake = exactly 0 EV."""
        ev = compute_ev(Probability(0.5), Odds(2.0), Stake(10.0))
        assert ev == pytest.approx(0.0)

    def test_positive_ev_when_we_have_edge(self):
        """60% chance × 2.0 odds × $10 = +$2 EV (long-run profit)."""
        # win: 0.6 × 1.0 × 10 = $6
        # lose: 0.4 × 10 = $4
        # net: $6 - $4 = $2
        ev = compute_ev(Probability(0.6), Odds(2.0), Stake(10.0))
        assert ev == pytest.approx(2.0)

    def test_negative_ev_when_market_overprices(self):
        """40% chance × 2.0 odds × $10 = -$2 EV."""
        ev = compute_ev(Probability(0.4), Odds(2.0), Stake(10.0))
        assert ev == pytest.approx(-2.0)

    def test_high_odds_compound_ev(self):
        """20% chance at 6.0 odds: win 5x stake."""
        # win: 0.2 × 5.0 × 100 = $100
        # lose: 0.8 × 100 = $80
        # net: $20
        ev = compute_ev(Probability(0.2), Odds(6.0), Stake(100.0))
        assert ev == pytest.approx(20.0)

    def test_zero_stake_means_zero_ev(self):
        ev = compute_ev(Probability(0.7), Odds(2.5), Stake(0.0))
        assert ev == pytest.approx(0.0)


# --- kelly_fraction ---

class TestKellyFraction:

    def test_zero_when_no_edge(self):
        """50% prob at 2.0 odds: Kelly = 0 (no edge)."""
        k = kelly_fraction(Probability(0.5), Odds(2.0))
        assert k == pytest.approx(0.0)

    def test_zero_when_negative_edge(self):
        """40% prob at 2.0 odds: edge negative → bet nothing."""
        k = kelly_fraction(Probability(0.4), Odds(2.0))
        assert k == pytest.approx(0.0)

    def test_classic_kelly_formula(self):
        """60% prob at 2.0 odds: f* = (1×0.6 - 0.4)/1 = 0.2 → bet 20%."""
        k = kelly_fraction(Probability(0.6), Odds(2.0))
        assert k == pytest.approx(0.2)

    def test_kelly_caps_at_25_percent(self):
        """Heavy favorite at high odds would suggest > 25% — capped."""
        # 90% prob at 2.0 odds: f* = (1×0.9 - 0.1)/1 = 0.8 → would suggest 80%
        k = kelly_fraction(Probability(0.9), Odds(2.0))
        assert k == pytest.approx(KELLY_CAP)

    def test_kelly_uses_custom_cap(self):
        k = kelly_fraction(Probability(0.9), Odds(2.0), cap=0.10)
        assert k == pytest.approx(0.10)

    def test_zero_when_odds_at_one(self):
        """Odds = 1.0 → no payout above stake → bet nothing."""
        k = kelly_fraction(Probability(0.99), Odds(1.0))
        assert k == pytest.approx(0.0)

    def test_zero_prob_returns_zero(self):
        k = kelly_fraction(Probability(0.0), Odds(2.0))
        assert k == pytest.approx(0.0)

    def test_high_odds_low_prob_small_fraction(self):
        """5% prob at 25.0 odds: f* = (24×0.05 - 0.95)/24 = 0.0104 → 1%."""
        k = kelly_fraction(Probability(0.05), Odds(25.0))
        assert k == pytest.approx(0.0104, abs=0.001)


# --- verdict_from_ev_kelly ---

class TestVerdictFromEVKelly:

    def test_apostar_when_both_thresholds_exceeded(self):
        """EV > 5% AND Kelly > 2% → APOSTAR."""
        ev = EV(1.0)  # > EV_APOSTAR_MIN (0.05)
        kelly = KellyFraction(0.10)  # > KELLY_APOSTAR_MIN (0.02)
        verdict = verdict_from_ev_kelly(ev, kelly)
        assert isinstance(verdict, Apostar)

    def test_esperar_when_ev_positive_but_below_threshold(self):
        ev = EV(0.02)  # positive but < 0.05
        kelly = KellyFraction(0.01)  # positive but < 0.02
        verdict = verdict_from_ev_kelly(ev, kelly)
        assert isinstance(verdict, Esperar)

    def test_esperar_when_kelly_zero_but_ev_positive(self):
        """Edge case: tiny positive EV, zero Kelly → still 'Esperar'."""
        ev = EV(0.01)
        kelly = KellyFraction(0.0)
        verdict = verdict_from_ev_kelly(ev, kelly)
        assert isinstance(verdict, Esperar)

    def test_no_apostar_when_negative_ev(self):
        ev = EV(-0.5)
        kelly = KellyFraction(0.0)
        verdict = verdict_from_ev_kelly(ev, kelly)
        assert isinstance(verdict, NoApostar)

    def test_verdict_includes_reason_string(self):
        ev = EV(2.0)
        kelly = KellyFraction(0.10)
        verdict = verdict_from_ev_kelly(ev, kelly, reason_context="strong form")
        assert isinstance(verdict, Apostar)
        assert "2.00" in verdict.reason
        assert "strong form" in verdict.reason


# --- Real-world scenarios ---

class TestRealWorldScenarios:

    def test_evens_bet_no_edge_says_no(self):
        """Bookies offer 2.0, we agree 50% — no edge, no bet."""
        prob = Probability(0.5)
        odds = Odds(2.0)
        stake = Stake(10.0)
        ev = compute_ev(prob, odds, stake)
        kelly = kelly_fraction(prob, odds)
        verdict = verdict_from_ev_kelly(ev, kelly)
        assert isinstance(verdict, NoApostar)

    def test_value_bet_says_apostar(self):
        """We think 60%, bookies offer 2.0 (their estimate is 50%) → bet."""
        prob = Probability(0.6)
        odds = Odds(2.0)
        stake = Stake(10.0)
        ev = compute_ev(prob, odds, stake)
        kelly = kelly_fraction(prob, odds)
        verdict = verdict_from_ev_kelly(ev, kelly)
        assert isinstance(verdict, Apostar)
        assert ev > 0
        assert kelly > 0

    def test_underdog_value_bet(self):
        """We see a real 25% chance at 5.0 odds (market thinks 20%)."""
        # EV (per $1) = 0.25 * 4 - 0.75 * 1 = 0.25 → 25% return
        # Kelly = (4*0.25 - 0.75)/4 = 0.0625 → bet 6.25%
        prob = Probability(0.25)
        odds = Odds(5.0)
        stake = Stake(10.0)
        ev = compute_ev(prob, odds, stake)
        kelly = kelly_fraction(prob, odds)
        verdict = verdict_from_ev_kelly(ev, kelly)
        assert isinstance(verdict, Apostar)
        assert ev == pytest.approx(2.5)  # $2.50 EV on $10 stake
        assert kelly == pytest.approx(0.0625)

    def test_bookmaker_overprices_we_dont_bet(self):
        """Real 40% but odds only 2.0 (implies 50%) → market thinks more."""
        prob = Probability(0.4)
        odds = Odds(2.0)
        stake = Stake(10.0)
        ev = compute_ev(prob, odds, stake)
        verdict = verdict_from_ev_kelly(ev, kelly_fraction(prob, odds))
        assert isinstance(verdict, NoApostar)
