const IMP_OPTIONS = [
  { key: "final", icon: "🏆", label: "Final / Copa", sub: "Máxima presión", bonus: 15 },
  { key: "clasif", icon: "🎯", label: "Clasificatorio", sub: "Obligados a ganar", bonus: 10 },
  { key: "normal", icon: "⚽", label: "Liga normal", sub: "Sin presión extra", bonus: 0 },
  { key: "calendario", icon: "📅", label: "Solo calendario", sub: "Puede ir con suplentes", bonus: -15 },
];

function calcTeamStats(games) {
  const played = games.filter(g => g.res);
  if (!played.length) return null;
  const wins = played.filter(g => g.res === "W").length;
  const draws = played.filter(g => g.res === "D").length;
  const losses = played.filter(g => g.res === "L").length;
  const gf = played.reduce((a, g) => a + (parseFloat(g.gf) || 0), 0);
  const gc = played.reduce((a, g) => a + (parseFloat(g.gc) || 0), 0);
  const tar = played.reduce((a, g) => a + (parseFloat(g.tar) || 0), 0);
  const cor = played.reduce((a, g) => a + (parseFloat(g.cor) || 0), 0);
  const n = played.length;
  return {
    wins, draws, losses, n,
    avgGF: (gf / n).toFixed(1),
    avgGC: (gc / n).toFixed(1),
    avgTar: (tar / n).toFixed(1),
    avgCor: (cor / n).toFixed(1),
    formScore: ((wins * 3 + draws) / (n * 3)) * 100,
  };
}

function calcPreScore(match) {
  const hs = calcTeamStats(match.home.games);
  const as = calcTeamStats(match.away.games);
  if (!hs || !as) return null;
  const impBonus = IMP_OPTIONS.find(o => o.key === match.context.importance)?.bonus || 0;
  const ausBonus = match.context.ausencias === "si" ? -10 : 0;
  const formDiff = hs.formScore - as.formScore;
  const attackScore = Math.min(100, parseFloat(hs.avgGF) * 20);
  const defenseScore = Math.max(0, 100 - parseFloat(as.avgGC) * 20);
  const base = (formDiff + 100) / 2 * 0.5 + attackScore * 0.25 + defenseScore * 0.25;
  return Math.max(0, Math.min(100, base + impBonus + ausBonus));
}

function calcLiveScore(live) {
  const posLocal = parseFloat(live.posLocal) || 0;
  const ataLocal = parseFloat(live.ataLocal) || 0;
  const ataVisit = parseFloat(live.ataVisit) || 0;
  const corLocal = parseFloat(live.corLocal) || 0;
  const corVisit = parseFloat(live.corVisit) || 0;
  const tarVisit = parseFloat(live.tarVisit) || 0;
  const minuto = parseFloat(live.minuto) || 45;
  const timeFactor = minuto > 60 ? 1.2 : minuto > 30 ? 1.0 : 0.8;
  const posScore = (posLocal / 100) * 30;
  const ataScore = ataLocal + ataVisit > 0 ? (ataLocal / (ataLocal + ataVisit)) * 35 : 17.5;
  const corScore = corLocal + corVisit > 0 ? (corLocal / (corLocal + corVisit)) * 20 : 10;
  const tarScore = tarVisit * 5;
  return Math.min(100, (posScore + ataScore + corScore + tarScore) * timeFactor);
}

function calcEV(myProb, quota, stake) {
  if (quota <= 0 || !stake) return null;
  const p = myProb / 100;
  const g = stake * (quota - 1);
  return p * g - (1 - p) * stake;
}

function getVerdict(score) {
  if (score >= 68) return { cls: "go", icon: "🟢", label: "APOSTAR", sub: "Señales sólidas detectadas" };
  if (score >= 45) return { cls: "wait", icon: "🟡", label: "ESPERAR", sub: "Señales mixtas — aguarda más info" };
  return { cls: "no", icon: "🔴", label: "NO APOSTAR", sub: "Condiciones desfavorables" };
}

export {
  IMP_OPTIONS,
  calcTeamStats,
  calcPreScore,
  calcLiveScore,
  calcEV,
  getVerdict,
};
