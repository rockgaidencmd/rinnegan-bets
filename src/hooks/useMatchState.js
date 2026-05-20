import { useState } from 'react';
import { calcPreScore, calcLiveScore, calcEV, getVerdict } from '../utils/calculations.js';

function emptyMatch(id) {
  return {
    id,
    name: "",
    phase: 0,
    home: { name: "", games: Array(5).fill({ res: "", gf: "", gc: "", tar: "", cor: "" }) },
    away: { name: "", games: Array(5).fill({ res: "", gf: "", gc: "", tar: "", cor: "" }) },
    context: { importance: "", local: "", ausencias: "no", quota: "", stake: "" },
    live: { posLocal: "", posVisit: "", ataLocal: "", ataVisit: "", corLocal: "", corVisit: "", tarLocal: "", tarVisit: "", minuto: "", liveQuota: "", liveStake: "" },
  };
}

function useMatchState() {
  const [matches, setMatches] = useState([emptyMatch(1)]);
  const [active, setActive] = useState(0);

  const match = matches[active];

  const setMatch = (updated) => setMatches(ms => ms.map((m, i) => i === active ? updated : m));
  const setPhase = (p) => setMatch({ ...match, phase: p });

  const addMatch = () => {
    if (matches.length >= 3) return;
    const newM = emptyMatch(Date.now());
    setMatches([...matches, newM]);
    setActive(matches.length);
  };

  // Computed values
  const preScore = calcPreScore(match);
  const liveScore = calcLiveScore(match.live);
  const quota = parseFloat(match.context.quota) || 0;
  const stake = parseFloat(match.context.stake) || 10;
  const impliedProb = quota > 0 ? (1 / quota) * 100 : 0;
  const myProb = preScore !== null ? Math.min(95, impliedProb + (preScore - 50) * 0.4) : impliedProb;
  const ev = calcEV(myProb, quota, stake);

  const liveQuota = parseFloat(match.live.liveQuota) || 0;
  const liveStake = parseFloat(match.live.liveStake) || stake;
  const finalScore = match.phase === 2
    ? preScore !== null ? preScore * 0.5 + liveScore * 0.5 : liveScore
    : preScore !== null ? preScore : 0;
  const verdict = getVerdict(finalScore);

  const liveImpliedProb = liveQuota > 0 ? (1 / liveQuota) * 100 : 0;
  const liveMyProb = Math.min(95, liveImpliedProb + (finalScore - 50) * 0.4);
  const liveEV = calcEV(liveMyProb, liveQuota, liveStake);
  const liveEdge = liveMyProb - liveImpliedProb;

  const phaseComplete = [
    match.home.name && match.away.name && match.home.games.some(g => g.res),
    match.context.importance !== "",
    true,
  ];

  return {
    matches,
    active,
    setActive,
    match,
    setMatch,
    setPhase,
    addMatch,
    preScore,
    liveScore,
    quota,
    stake,
    impliedProb,
    myProb,
    ev,
    liveQuota,
    liveStake,
    finalScore,
    verdict,
    liveImpliedProb,
    liveMyProb,
    liveEV,
    liveEdge,
    phaseComplete,
  };
}

export { useMatchState };
