import { useState } from "react";

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #080a0f;
    --s1: #0d1017;
    --s2: #131720;
    --s3: #1a1f2e;
    --border: #1e2535;
    --green: #00f5a0;
    --yellow: #f5c400;
    --red: #ff3d5a;
    --blue: #4488ff;
    --text: #dde2f0;
    --muted: #4a5270;
    --r: 10px;
  }
  body { background: var(--bg); color: var(--text); font-family: 'Barlow Condensed', sans-serif; min-height: 100vh; overflow-x: hidden; }
  .mono { font-family: 'IBM Plex Mono', monospace; }

  /* LAYOUT */
  .app { max-width: 860px; margin: 0 auto; padding: 20px 14px 80px; }

  /* HEADER */
  .hdr { display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; padding-bottom: 18px; border-bottom: 1px solid var(--border); }
  .hdr-logo { font-size: 1.6rem; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; }
  .hdr-logo em { color: var(--green); font-style: normal; }
  .hdr-tag { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: var(--muted); border: 1px solid var(--border); padding: 3px 10px; border-radius: 99px; }

  /* MATCH SELECTOR */
  .match-bar { display: flex; gap: 8px; margin-bottom: 22px; align-items: center; }
  .match-btn { flex: 1; padding: 10px 8px; border-radius: var(--r); border: 1px solid var(--border); background: var(--s1); color: var(--muted); font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 0.82rem; cursor: pointer; transition: all 0.2s; text-align: center; letter-spacing: 0.5px; position: relative; }
  .match-btn.active { background: var(--s3); border-color: var(--green); color: var(--text); }
  .match-btn .dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; margin-right: 6px; background: var(--muted); }
  .match-btn.active .dot { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .match-btn.ready .dot { background: var(--yellow); }
  .match-btn.live-mode .dot { background: var(--red); animation: pulse 1s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  .add-match-btn { width: 42px; height: 42px; border-radius: var(--r); border: 1px dashed var(--border); background: transparent; color: var(--muted); font-size: 1.3rem; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; flex-shrink: 0; }
  .add-match-btn:hover { border-color: var(--green); color: var(--green); }

  /* PHASE STEPPER */
  .stepper { display: flex; align-items: center; margin-bottom: 24px; }
  .step { display: flex; align-items: center; gap: 8px; flex: 1; cursor: pointer; }
  .step-num { width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--border); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.8rem; color: var(--muted); transition: all 0.2s; flex-shrink: 0; }
  .step.active .step-num { border-color: var(--green); color: var(--green); background: rgba(0,245,160,0.08); }
  .step.done .step-num { border-color: var(--green); background: var(--green); color: var(--bg); }
  .step-label { font-size: 0.78rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
  .step.active .step-label { color: var(--text); }
  .step.done .step-label { color: var(--green); }
  .step-line { flex: 0 0 24px; height: 1px; background: var(--border); margin: 0 4px; }
  .step-line.done { background: var(--green); }

  /* CARD */
  .card { background: var(--s1); border: 1px solid var(--border); border-radius: var(--r); padding: 20px; margin-bottom: 14px; }
  .card-hdr { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  .card-title { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); }
  .card-badge { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; padding: 2px 10px; border-radius: 99px; }
  .badge-green { background: rgba(0,245,160,0.1); color: var(--green); }
  .badge-yellow { background: rgba(245,196,0,0.1); color: var(--yellow); }
  .badge-red { background: rgba(255,61,90,0.1); color: var(--red); }

  /* FORM ELEMENTS */
  .field { margin-bottom: 14px; }
  .lbl { font-size: 0.7rem; font-weight: 700; color: var(--muted); margin-bottom: 5px; display: block; letter-spacing: 0.08em; text-transform: uppercase; }
  .inp { width: 100%; background: var(--s2); border: 1px solid var(--border); border-radius: 7px; padding: 10px 13px; color: var(--text); font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; outline: none; transition: border-color 0.2s; }
  .inp:focus { border-color: var(--green); }
  .inp::placeholder { color: var(--muted); }
  .inp-sm { padding: 7px 10px; font-size: 0.8rem; }
  .g2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .g3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
  .g4 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px; }

  /* PILL SELECTOR */
  .pill-group { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 4px; }
  .pill-opt { padding: 6px 14px; border-radius: 99px; border: 1px solid var(--border); background: var(--s2); color: var(--muted); font-weight: 700; font-size: 0.78rem; cursor: pointer; transition: all 0.18s; letter-spacing: 0.04em; }
  .pill-opt.sel { background: var(--green); border-color: var(--green); color: var(--bg); }
  .pill-opt.sel-y { background: var(--yellow); border-color: var(--yellow); color: var(--bg); }
  .pill-opt.sel-r { background: var(--red); border-color: var(--red); color: #fff; }

  /* MATCH TABLE */
  .match-tbl { width: 100%; border-collapse: collapse; }
  .match-tbl th { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); padding: 6px 8px; text-align: center; border-bottom: 1px solid var(--border); }
  .match-tbl th:first-child { text-align: left; }
  .match-tbl td { padding: 8px; text-align: center; border-bottom: 1px solid rgba(30,37,53,0.5); font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; }
  .match-tbl td:first-child { text-align: left; font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 0.88rem; }
  .match-tbl tr:last-child td { border-bottom: none; }
  .res-w { color: var(--green); font-weight: 600; }
  .res-l { color: var(--red); font-weight: 600; }
  .res-d { color: var(--yellow); font-weight: 600; }

  /* STAT MINI */
  .stat-row { display: flex; gap: 8px; margin-bottom: 10px; }
  .stat-mini { flex: 1; background: var(--s2); border-radius: 8px; padding: 10px; text-align: center; border: 1px solid var(--border); }
  .stat-mini-val { font-family: 'IBM Plex Mono', monospace; font-size: 1.05rem; font-weight: 600; margin-bottom: 2px; }
  .stat-mini-lbl { font-size: 0.62rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }

  /* DIVIDER */
  .sep { border: none; border-top: 1px solid var(--border); margin: 16px 0; }

  /* TEAM HEADER */
  .team-hdr { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; padding: 12px 14px; background: var(--s2); border-radius: 8px; border: 1px solid var(--border); }
  .team-circle { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 0.9rem; flex-shrink: 0; }
  .team-circle.home { background: rgba(68,136,255,0.15); color: var(--blue); border: 1px solid rgba(68,136,255,0.3); }
  .team-circle.away { background: rgba(255,61,90,0.15); color: var(--red); border: 1px solid rgba(255,61,90,0.3); }
  .team-name-big { font-size: 1rem; font-weight: 800; letter-spacing: 0.5px; }
  .team-role { font-size: 0.7rem; color: var(--muted); font-weight: 600; letter-spacing: 0.06em; }

  /* VERDICT BOX */
  .verdict { border-radius: var(--r); padding: 22px 20px; margin-top: 6px; text-align: center; border: 2px solid; transition: all 0.3s; }
  .verdict.go { background: rgba(0,245,160,0.06); border-color: var(--green); }
  .verdict.wait { background: rgba(245,196,0,0.06); border-color: var(--yellow); }
  .verdict.no { background: rgba(255,61,90,0.06); border-color: var(--red); }
  .verdict-icon { font-size: 2.2rem; margin-bottom: 8px; }
  .verdict-main { font-size: 1.8rem; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px; }
  .verdict-main.go { color: var(--green); }
  .verdict-main.wait { color: var(--yellow); }
  .verdict-main.no { color: var(--red); }
  .verdict-sub { font-size: 0.82rem; color: var(--muted); font-weight: 600; }
  .verdict-score { font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; margin-top: 10px; color: var(--muted); }

  /* LIVE INPUTS */
  .live-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .live-inp-wrap { background: var(--s2); border: 1px solid var(--border); border-radius: 9px; padding: 12px 14px; }
  .live-inp-label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin-bottom: 6px; }
  .live-inp-val { font-family: 'IBM Plex Mono', monospace; font-size: 1.5rem; font-weight: 600; color: var(--text); }
  .live-inp-field { width: 100%; background: transparent; border: none; outline: none; font-family: 'IBM Plex Mono', monospace; font-size: 1.5rem; font-weight: 600; color: var(--text); }

  /* PROGRESS BAR */
  .prog-wrap { background: var(--s2); border-radius: 99px; height: 6px; overflow: hidden; margin-top: 6px; }
  .prog-bar { height: 100%; border-radius: 99px; transition: width 0.4s; }

  /* BTN */
  .btn { display: block; width: 100%; padding: 13px; border: none; border-radius: 8px; font-family: 'Barlow Condensed', sans-serif; font-weight: 800; font-size: 1rem; cursor: pointer; transition: all 0.2s; margin-top: 12px; letter-spacing: 1px; text-transform: uppercase; }
  .btn-green { background: var(--green); color: var(--bg); }
  .btn-green:hover { opacity: 0.85; transform: translateY(-1px); }
  .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--muted); }
  .btn-outline:hover { border-color: var(--green); color: var(--green); }

  /* EV DISPLAY */
  .ev-strip { display: flex; justify-content: space-around; padding: 14px 0; border-top: 1px solid var(--border); margin-top: 14px; }
  .ev-item { text-align: center; }
  .ev-item-val { font-family: 'IBM Plex Mono', monospace; font-size: 1.1rem; font-weight: 600; }
  .ev-item-lbl { font-size: 0.63rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }

  /* IMPORTANCE SELECTOR */
  .imp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .imp-card { padding: 12px 10px; border-radius: 8px; border: 1px solid var(--border); background: var(--s2); cursor: pointer; transition: all 0.18s; text-align: center; }
  .imp-card.sel { border-color: var(--green); background: rgba(0,245,160,0.06); }
  .imp-icon { font-size: 1.4rem; margin-bottom: 4px; }
  .imp-label { font-size: 0.78rem; font-weight: 700; }
  .imp-sub { font-size: 0.65rem; color: var(--muted); margin-top: 2px; }

  /* MATCH NAME INPUT */
  .match-name-inp { width: 100%; background: transparent; border: none; outline: none; font-family: 'Barlow Condensed', sans-serif; font-weight: 800; font-size: 1.1rem; color: var(--text); }
  .match-name-inp::placeholder { color: var(--muted); }

  /* FORM RESULTS ROW */
  .results-row { display: flex; gap: 6px; margin-top: 6px; }
  .res-pill { flex: 1; padding: 7px 4px; border-radius: 7px; border: 1px solid var(--border); background: var(--s2); color: var(--muted); font-weight: 800; font-size: 0.82rem; cursor: pointer; transition: all 0.18s; text-align: center; }
  .res-pill.w { background: rgba(0,245,160,0.15); border-color: var(--green); color: var(--green); }
  .res-pill.d { background: rgba(245,196,0,0.15); border-color: var(--yellow); color: var(--yellow); }
  .res-pill.l { background: rgba(255,61,90,0.15); border-color: var(--red); color: var(--red); }

  .phase-nav { display: flex; gap: 8px; margin-top: 4px; }

  @media(max-width:580px){
    .g3,.g4{grid-template-columns:1fr 1fr;}
    .live-grid{grid-template-columns:1fr 1fr;}
    .imp-grid{grid-template-columns:1fr 1fr;}
  }
`;

const emptyMatch = (id) => ({
  id,
  name: "",
  phase: 0, // 0=prepartido, 1=contexto, 2=envivo
  home: { name: "", games: Array(5).fill({ res: "", gf: "", gc: "", tar: "", cor: "" }) },
  away: { name: "", games: Array(5).fill({ res: "", gf: "", gc: "", tar: "", cor: "" }) },
  context: { importance: "", local: "", ausencias: "no", quota: "", stake: "" },
  live: { posLocal: "", posVisit: "", ataLocal: "", ataVisit: "", corLocal: "", corVisit: "", tarLocal: "", tarVisit: "", minuto: "", liveQuota: "", liveStake: "" },
});

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
  // Form score diferencial
  const formDiff = hs.formScore - as.formScore; // -100 to 100
  // GF/GC
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
  const p = myProb / 100;
  const g = stake * (quota - 1);
  return p * g - (1 - p) * stake;
}

function getVerdict(score) {
  if (score >= 68) return { cls: "go", icon: "🟢", label: "APOSTAR", sub: "Señales sólidas detectadas" };
  if (score >= 45) return { cls: "wait", icon: "🟡", label: "ESPERAR", sub: "Señales mixtas — aguarda más info" };
  return { cls: "no", icon: "🔴", label: "NO APOSTAR", sub: "Condiciones desfavorables" };
}

function TeamForm({ team, onChange }) {
  const updateGame = (i, field, val) => {
    const games = team.games.map((g, idx) => idx === i ? { ...g, [field]: val } : g);
    onChange({ ...team, games });
  };
  return (
    <div>
      <table className="match-tbl">
        <thead>
          <tr>
            <th>Partido</th>
            <th>Res</th>
            <th>GF</th>
            <th>GC</th>
            <th>Tar</th>
            <th>Cor</th>
          </tr>
        </thead>
        <tbody>
          {team.games.map((g, i) => (
            <tr key={i}>
              <td style={{ color: "var(--muted)", fontSize: "0.75rem" }}>P{i + 1}</td>
              <td>
                <div className="results-row" style={{ gap: 3 }}>
                  {["W", "D", "L"].map(r => (
                    <div key={r} className={`res-pill ${g.res === r ? (r === "W" ? "w" : r === "D" ? "d" : "l") : ""}`}
                      style={{ padding: "4px 2px", fontSize: "0.72rem" }}
                      onClick={() => updateGame(i, "res", g.res === r ? "" : r)}>{r}</div>
                  ))}
                </div>
              </td>
              {["gf", "gc", "tar", "cor"].map(f => (
                <td key={f}>
                  <input className="inp inp-sm" style={{ textAlign: "center", padding: "5px 4px", width: "100%" }}
                    type="number" min="0" max="20" placeholder="0"
                    value={g[f]} onChange={e => updateGame(i, f, e.target.value)} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function App() {
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

  const preScore = calcPreScore(match);
  const liveScore = calcLiveScore(match.live);
  const quota = parseFloat(match.context.quota) || 0;
  const stake = parseFloat(match.context.stake) || 10;
  const impliedProb = quota > 0 ? (1 / quota) * 100 : 0;
  const myProb = preScore !== null ? Math.min(95, impliedProb + (preScore - 50) * 0.4) : impliedProb;
  const ev = quota > 0 ? calcEV(myProb, quota, stake) : null;

  // Live quota — overrides pre-match quota in phase 2
  const liveQuota = parseFloat(match.live.liveQuota) || 0;
  const liveStake = parseFloat(match.live.liveStake) || stake;

  const finalScore = match.phase === 2
    ? preScore !== null ? preScore * 0.5 + liveScore * 0.5 : liveScore
    : preScore !== null ? preScore : 0;
  const verdict = getVerdict(finalScore);

  const liveImpliedProb = liveQuota > 0 ? (1 / liveQuota) * 100 : 0;
  const liveMyProb = Math.min(95, liveImpliedProb + (finalScore - 50) * 0.4);
  const liveEV = liveQuota > 0 ? calcEV(liveMyProb, liveQuota, liveStake) : null;
  const liveEdge = liveMyProb - liveImpliedProb;

  const phaseComplete = [
    match.home.name && match.away.name && match.home.games.some(g => g.res),
    match.context.importance !== "",
    true,
  ];

  return (
    <>
      <style>{CSS}</style>
      <div className="app">

        {/* HEADER */}
        <div className="hdr">
          <div className="hdr-logo">RINNEG<em>AN</em> <span style={{ color: "var(--muted)", fontWeight: 400 }}>BETS</span></div>
          <div className="hdr-tag">v2 · 3 FASES</div>
        </div>

        {/* MATCH SELECTOR */}
        <div className="match-bar">
          {matches.map((m, i) => (
            <button key={m.id} className={`match-btn ${i === active ? "active" : ""} ${m.phase === 2 ? "live-mode" : m.phase === 1 ? "ready" : ""}`}
              onClick={() => setActive(i)}>
              <span className="dot" />
              {m.name || `Partido ${i + 1}`}
            </button>
          ))}
          {matches.length < 3 && (
            <button className="add-match-btn" onClick={addMatch}>+</button>
          )}
        </div>

        {/* PHASE STEPPER */}
        <div className="stepper">
          {[{ label: "Prepartido" }, { label: "Contexto" }, { label: "En Vivo" }].map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", flex: i < 2 ? 1 : 0 }}>
              <div className={`step ${match.phase === i ? "active" : match.phase > i ? "done" : ""}`}
                onClick={() => setPhase(i)} style={{ cursor: "pointer" }}>
                <div className="step-num">{match.phase > i ? "✓" : i + 1}</div>
                <div className="step-label">{s.label}</div>
              </div>
              {i < 2 && <div className={`step-line ${match.phase > i ? "done" : ""}`} />}
            </div>
          ))}
        </div>

        {/* ── FASE 0: PREPARTIDO ── */}
        {match.phase === 0 && (
          <>
            <div className="card">
              <div className="card-hdr">
                <div className="card-title">Nombre del partido</div>
              </div>
              <input className="match-name-inp" placeholder="ej: Barcelona vs Liga de Quito"
                value={match.name} onChange={e => setMatch({ ...match, name: e.target.value })} />
            </div>

            {/* HOME */}
            <div className="card">
              <div className="team-hdr">
                <div className="team-circle home">L</div>
                <div>
                  <input className="inp" style={{ background: "transparent", border: "none", padding: "0", fontWeight: 800, fontSize: "1rem" }}
                    placeholder="Equipo local..." value={match.home.name}
                    onChange={e => setMatch({ ...match, home: { ...match.home, name: e.target.value } })} />
                  <div className="team-role">LOCAL · Últimos 5 partidos</div>
                </div>
              </div>
              <TeamForm team={match.home} onChange={home => setMatch({ ...match, home })} />
              {calcTeamStats(match.home.games) && (() => {
                const s = calcTeamStats(match.home.games);
                return (
                  <div className="stat-row" style={{ marginTop: 12 }}>
                    <div className="stat-mini"><div className="stat-mini-val res-w">{s.wins}G</div><div className="stat-mini-lbl">Ganados</div></div>
                    <div className="stat-mini"><div className="stat-mini-val res-d">{s.draws}E</div><div className="stat-mini-lbl">Empates</div></div>
                    <div className="stat-mini"><div className="stat-mini-val res-l">{s.losses}P</div><div className="stat-mini-lbl">Perdidos</div></div>
                    <div className="stat-mini"><div className="stat-mini-val">{s.avgGF}</div><div className="stat-mini-lbl">GF/prom</div></div>
                    <div className="stat-mini"><div className="stat-mini-val">{s.avgGC}</div><div className="stat-mini-lbl">GC/prom</div></div>
                  </div>
                );
              })()}
            </div>

            {/* AWAY */}
            <div className="card">
              <div className="team-hdr">
                <div className="team-circle away">V</div>
                <div>
                  <input className="inp" style={{ background: "transparent", border: "none", padding: "0", fontWeight: 800, fontSize: "1rem" }}
                    placeholder="Equipo visitante..." value={match.away.name}
                    onChange={e => setMatch({ ...match, away: { ...match.away, name: e.target.value } })} />
                  <div className="team-role">VISITANTE · Últimos 5 partidos</div>
                </div>
              </div>
              <TeamForm team={match.away} onChange={away => setMatch({ ...match, away })} />
              {calcTeamStats(match.away.games) && (() => {
                const s = calcTeamStats(match.away.games);
                return (
                  <div className="stat-row" style={{ marginTop: 12 }}>
                    <div className="stat-mini"><div className="stat-mini-val res-w">{s.wins}G</div><div className="stat-mini-lbl">Ganados</div></div>
                    <div className="stat-mini"><div className="stat-mini-val res-d">{s.draws}E</div><div className="stat-mini-lbl">Empates</div></div>
                    <div className="stat-mini"><div className="stat-mini-val res-l">{s.losses}P</div><div className="stat-mini-lbl">Perdidos</div></div>
                    <div className="stat-mini"><div className="stat-mini-val">{s.avgGF}</div><div className="stat-mini-lbl">GF/prom</div></div>
                    <div className="stat-mini"><div className="stat-mini-val">{s.avgGC}</div><div className="stat-mini-lbl">GC/prom</div></div>
                  </div>
                );
              })()}
            </div>

            <button className="btn btn-green" onClick={() => setPhase(1)}>
              Continuar → Contexto del partido
            </button>
          </>
        )}

        {/* ── FASE 1: CONTEXTO ── */}
        {match.phase === 1 && (
          <>
            <div className="card">
              <div className="card-hdr"><div className="card-title">Importancia del partido</div></div>
              <div className="imp-grid">
                {IMP_OPTIONS.map(o => (
                  <div key={o.key} className={`imp-card ${match.context.importance === o.key ? "sel" : ""}`}
                    onClick={() => setMatch({ ...match, context: { ...match.context, importance: o.key } })}>
                    <div className="imp-icon">{o.icon}</div>
                    <div className="imp-label">{o.label}</div>
                    <div className="imp-sub">{o.sub}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-hdr"><div className="card-title">¿Ausencias clave en el local?</div></div>
              <div className="pill-group">
                {[{ k: "no", l: "No hay ausencias" }, { k: "si", l: "Sí — titular importante" }].map(o => (
                  <div key={o.k} className={`pill-opt ${match.context.ausencias === o.k ? (o.k === "si" ? "sel-r" : "sel") : ""}`}
                    onClick={() => setMatch({ ...match, context: { ...match.context, ausencias: o.k } })}>{o.l}</div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-hdr"><div className="card-title">Cuota y stake</div></div>
              <div className="g2">
                <div className="field">
                  <label className="lbl">Cuota ofrecida</label>
                  <input className="inp" type="number" step="0.01" placeholder="ej: 1.85"
                    value={match.context.quota} onChange={e => setMatch({ ...match, context: { ...match.context, quota: e.target.value } })} />
                </div>
                <div className="field">
                  <label className="lbl">Stake ($)</label>
                  <input className="inp" type="number" placeholder="ej: 10"
                    value={match.context.stake} onChange={e => setMatch({ ...match, context: { ...match.context, stake: e.target.value } })} />
                </div>
              </div>
              {quota > 0 && preScore !== null && (
                <div style={{ background: "var(--s2)", borderRadius: 8, padding: "12px 14px", border: "1px solid var(--border)", marginTop: 6 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--muted)", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>Valor Esperado (EV)</span>
                    <span className="mono" style={{ fontSize: "1.2rem", fontWeight: 600, color: ev >= 0 ? "var(--green)" : "var(--red)" }}>
                      {ev >= 0 ? "+" : ""}{ev?.toFixed(2)}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
                    <span style={{ fontSize: "0.72rem", color: "var(--muted)" }}>Prob. implícita: <span className="mono" style={{ color: "var(--text)" }}>{impliedProb.toFixed(1)}%</span></span>
                    <span style={{ fontSize: "0.72rem", color: "var(--muted)" }}>Mi prob: <span className="mono" style={{ color: "var(--green)" }}>{myProb.toFixed(1)}%</span></span>
                    <span style={{ fontSize: "0.72rem", color: "var(--muted)" }}>Edge: <span className="mono" style={{ color: myProb > impliedProb ? "var(--green)" : "var(--red)" }}>{(myProb - impliedProb) > 0 ? "+" : ""}{(myProb - impliedProb).toFixed(1)}%</span></span>
                  </div>
                </div>
              )}
            </div>

            {preScore !== null && (
              <div className="card">
                <div className="card-hdr">
                  <div className="card-title">Score prepartido</div>
                  <span className={`card-badge ${preScore >= 68 ? "badge-green" : preScore >= 45 ? "badge-yellow" : "badge-red"}`}>{preScore.toFixed(0)}/100</span>
                </div>
                <div className="prog-wrap">
                  <div className="prog-bar" style={{ width: `${preScore}%`, background: preScore >= 68 ? "var(--green)" : preScore >= 45 ? "var(--yellow)" : "var(--red)" }} />
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: 8 }}>
                  Basado en forma reciente · diferencial de goles · importancia · ausencias
                </div>
              </div>
            )}

            <div className="phase-nav">
              <button className="btn btn-outline" style={{ flex: 1 }} onClick={() => setPhase(0)}>← Volver</button>
              <button className="btn btn-green" style={{ flex: 2 }} onClick={() => setPhase(2)}>Ir a En Vivo →</button>
            </div>
          </>
        )}

        {/* ── FASE 2: EN VIVO ── */}
        {match.phase === 2 && (
          <>
            <div className="card">
              <div className="card-hdr">
                <div className="card-title">🔴 Datos en vivo — copia de tu app de resultados</div>
                <div className="card-badge badge-red">EN VIVO</div>
              </div>

              <div className="field">
                <label className="lbl">Minuto del partido</label>
                <input className="inp" type="number" min="1" max="120" placeholder="45"
                  value={match.live.minuto} onChange={e => setMatch({ ...match, live: { ...match.live, minuto: e.target.value } })} />
              </div>

              {/* CUOTA EN VIVO */}
              <div style={{ background: "var(--s2)", border: "1px solid rgba(245,196,0,0.25)", borderRadius: 9, padding: "14px", marginBottom: 10 }}>
                <div style={{ fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--yellow)", marginBottom: 10 }}>
                  ⚡ Cuota actual en vivo
                </div>
                <div className="g2">
                  <div className="field" style={{ marginBottom: 0 }}>
                    <label className="lbl">Cuota en vivo</label>
                    <input className="inp" type="number" step="0.01" placeholder="ej: 1.60"
                      style={{ borderColor: liveQuota > 0 ? "rgba(245,196,0,0.4)" : "" }}
                      value={match.live.liveQuota} onChange={e => setMatch({ ...match, live: { ...match.live, liveQuota: e.target.value } })} />
                  </div>
                  <div className="field" style={{ marginBottom: 0 }}>
                    <label className="lbl">Stake en vivo ($)</label>
                    <input className="inp" type="number" placeholder={stake || "10"}
                      value={match.live.liveStake} onChange={e => setMatch({ ...match, live: { ...match.live, liveStake: e.target.value } })} />
                  </div>
                </div>
                {liveEV !== null && (
                  <div style={{ marginTop: 12, padding: "10px 12px", borderRadius: 8, background: liveEV >= 0 ? "rgba(0,245,160,0.07)" : "rgba(255,61,90,0.07)", border: `1px solid ${liveEV >= 0 ? "rgba(0,245,160,0.3)" : "rgba(255,61,90,0.3)"}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "0.72rem", color: "var(--muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>EV en vivo</span>
                      <span className="mono" style={{ fontSize: "1.3rem", fontWeight: 700, color: liveEV >= 0 ? "var(--green)" : "var(--red)" }}>
                        {liveEV >= 0 ? "+" : ""}{liveEV.toFixed(2)}
                      </span>
                    </div>
                    <div style={{ display: "flex", gap: 16, marginTop: 7 }}>
                      <span style={{ fontSize: "0.7rem", color: "var(--muted)" }}>Prob. implícita: <span className="mono" style={{ color: "var(--text)" }}>{liveImpliedProb.toFixed(1)}%</span></span>
                      <span style={{ fontSize: "0.7rem", color: "var(--muted)" }}>Mi prob: <span className="mono" style={{ color: "var(--green)" }}>{liveMyProb.toFixed(1)}%</span></span>
                      <span style={{ fontSize: "0.7rem", color: "var(--muted)" }}>Edge: <span className="mono" style={{ color: liveEdge > 0 ? "var(--green)" : "var(--red)" }}>{liveEdge > 0 ? "+" : ""}{liveEdge.toFixed(1)}%</span></span>
                    </div>
                    {quota > 0 && liveQuota !== quota && (
                      <div style={{ marginTop: 7, fontSize: "0.68rem", color: "var(--muted)" }}>
                        Cuota prepartido: <span className="mono" style={{ color: "var(--muted)" }}>{quota}</span>
                        {liveQuota < quota
                          ? <span style={{ color: "var(--red)", marginLeft: 6 }}>↓ bajó {(quota - liveQuota).toFixed(2)} — mercado anticipa gol</span>
                          : <span style={{ color: "var(--green)", marginLeft: 6 }}>↑ subió {(liveQuota - quota).toFixed(2)} — oportunidad abierta</span>
                        }
                      </div>
                    )}
                  </div>
                )}
              </div>

              <hr className="sep" />

              <div style={{ marginBottom: 10 }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 8, alignItems: "center", marginBottom: 10 }}>
                  <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--blue)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{match.home.name || "Local"}</div>
                  <div style={{ fontSize: "0.65rem", color: "var(--muted)", textAlign: "center" }}>VS</div>
                  <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--red)", textTransform: "uppercase", letterSpacing: "0.08em", textAlign: "right" }}>{match.away.name || "Visitante"}</div>
                </div>

                {[
                  { label: "Posesión %", lKey: "posLocal", rKey: "posVisit", hint: "Suma debe dar 100" },
                  { label: "Ataques peligrosos", lKey: "ataLocal", rKey: "ataVisit", hint: "" },
                  { label: "Tiros de esquina", lKey: "corLocal", rKey: "corVisit", hint: "" },
                  { label: "Tarjetas amarillas", lKey: "tarLocal", rKey: "tarVisit", hint: "" },
                ].map(row => (
                  <div key={row.label} style={{ marginBottom: 10 }}>
                    <div style={{ fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", textAlign: "center", marginBottom: 5 }}>{row.label}</div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 8, alignItems: "center" }}>
                      <input className="inp" type="number" min="0" placeholder="0" style={{ textAlign: "center", borderColor: "rgba(68,136,255,0.3)" }}
                        value={match.live[row.lKey]} onChange={e => setMatch({ ...match, live: { ...match.live, [row.lKey]: e.target.value } })} />
                      <div style={{ width: 8, height: 1, background: "var(--border)" }} />
                      <input className="inp" type="number" min="0" placeholder="0" style={{ textAlign: "center", borderColor: "rgba(255,61,90,0.3)" }}
                        value={match.live[row.rKey]} onChange={e => setMatch({ ...match, live: { ...match.live, [row.rKey]: e.target.value } })} />
                    </div>
                    {row.hint && <div style={{ fontSize: "0.62rem", color: "var(--muted)", textAlign: "center", marginTop: 3 }}>{row.hint}</div>}
                  </div>
                ))}
              </div>
            </div>

            {/* VEREDICTO FINAL */}
            <div className={`verdict ${verdict.cls}`}>
              <div className="verdict-icon">{verdict.icon}</div>
              <div className={`verdict-main ${verdict.cls}`}>{verdict.label}</div>
              <div className="verdict-sub">{verdict.sub}</div>
              <div className="verdict-score mono">
                Score final: {finalScore.toFixed(0)}/100
                {liveEV !== null && ` · EV en vivo: ${liveEV >= 0 ? "+" : ""}${liveEV.toFixed(2)}`}
              </div>
              {liveEV !== null && (
                <div style={{ marginTop: 10, fontSize: "0.75rem", padding: "6px 14px", borderRadius: 99, display: "inline-block", background: liveEV >= 0 ? "rgba(0,245,160,0.1)" : "rgba(255,61,90,0.1)", color: liveEV >= 0 ? "var(--green)" : "var(--red)", fontFamily: "'IBM Plex Mono',monospace" }}>
                  {liveEV >= 0 ? "✅ EV POSITIVO EN VIVO" : "❌ EV NEGATIVO EN VIVO"}
                </div>
              )}
            </div>

            <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={() => setPhase(1)}>← Volver al contexto</button>
          </>
        )}

      </div>
    </>
  );
}
