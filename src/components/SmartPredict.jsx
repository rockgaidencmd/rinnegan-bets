import { useState } from 'react';
import { api, ApiError } from '../utils/api.js';
import { useBankroll } from '../hooks/useBankroll.js';
import { TeamAutocomplete } from './TeamAutocomplete.jsx';
import { PredictionResult } from './PredictionResult.jsx';
import { TeamStatsPreview } from './TeamStatsPreview.jsx';


const IMPORTANCE_OPTIONS = [
  { key: 'final', icon: '🏆', label: 'Final / Copa' },
  { key: 'clasif', icon: '🎯', label: 'Clasificatorio' },
  { key: 'normal', icon: '⚽', label: 'Liga normal' },
  { key: 'calendario', icon: '📅', label: 'Solo calendario' },
];


export function SmartPredict() {
  const { balance } = useBankroll();
  const [home, setHome] = useState(null);
  const [away, setAway] = useState(null);
  const [importance, setImportance] = useState('normal');
  const [homeAbsences, setHomeAbsences] = useState(false);
  const [awayAbsences, setAwayAbsences] = useState(false);
  const [quota, setQuota] = useState('');
  const [stake, setStake] = useState('10');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Derived state — no useEffect needed
  const quotaNum = parseFloat(quota);
  const stakeNum = parseFloat(stake);
  const canPredict =
    home && away &&
    Number.isFinite(quotaNum) && quotaNum > 1 &&
    Number.isFinite(stakeNum) && stakeNum > 0;

  const handleReset = () => {
    setPrediction(null);
    setError(null);
  };

  const handleStartOver = () => {
    setHome(null);
    setAway(null);
    setImportance('normal');
    setHomeAbsences(false);
    setAwayAbsences(false);
    setQuota('');
    setStake('10');
    setPrediction(null);
    setError(null);
  };

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.predict({
        home_team: home.name,
        away_team: away.name,
        quota: quotaNum,
        stake: stakeNum,
        importance,
        home_key_absences: homeAbsences,
        away_key_absences: awayAbsences,
      });
      setPrediction(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Error inesperado. ¿Backend corriendo?');
      }
    } finally {
      setLoading(false);
    }
  };

  if (prediction) {
    return (
      <PredictionResult
        prediction={prediction}
        availableBalance={balance?.available || 0}
        onReset={handleStartOver}
      />
    );
  }

  return (
    <>
      <div className="card">
        <div className="card-hdr">
          <div className="card-title">1. Equipos</div>
        </div>
        <TeamAutocomplete
          label="Equipo Local"
          selected={home}
          onSelect={setHome}
          placeholder="ej: IDV, Napoli, BSC..."
        />
        {home && <TeamStatsPreview teamId={home.id} />}
      </div>

      <div className="card">
        <TeamAutocomplete
          label="Equipo Visitante"
          selected={away}
          onSelect={setAway}
          placeholder="ej: LDU, Inter, Emelec..."
        />
        {away && <TeamStatsPreview teamId={away.id} />}
      </div>

      <div className="card">
        <div className="card-hdr">
          <div className="card-title">2. Contexto</div>
        </div>
        <label className="lbl">Importancia del partido</label>
        <div className="imp-grid">
          {IMPORTANCE_OPTIONS.map((o) => (
            <div
              key={o.key}
              className={`imp-card ${importance === o.key ? 'sel' : ''}`}
              onClick={() => setImportance(o.key)}
            >
              <div className="imp-icon">{o.icon}</div>
              <div className="imp-label">{o.label}</div>
            </div>
          ))}
        </div>

        <div className="g2" style={{ marginTop: 12 }}>
          <div className="field">
            <label className="lbl">Ausencias local</label>
            <div className="pill-group">
              {[
                { k: false, l: 'No' },
                { k: true, l: 'Sí' },
              ].map((o) => (
                <div
                  key={String(o.k)}
                  className={`pill-opt ${homeAbsences === o.k ? (o.k ? 'sel-r' : 'sel') : ''}`}
                  onClick={() => setHomeAbsences(o.k)}
                >
                  {o.l}
                </div>
              ))}
            </div>
          </div>
          <div className="field">
            <label className="lbl">Ausencias visitante</label>
            <div className="pill-group">
              {[
                { k: false, l: 'No' },
                { k: true, l: 'Sí' },
              ].map((o) => (
                <div
                  key={String(o.k)}
                  className={`pill-opt ${awayAbsences === o.k ? (o.k ? 'sel-r' : 'sel') : ''}`}
                  onClick={() => setAwayAbsences(o.k)}
                >
                  {o.l}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-hdr">
          <div className="card-title">3. Cuota y Stake</div>
        </div>
        <div className="g2">
          <div className="field">
            <label className="lbl">Cuota ofrecida</label>
            <input
              className="inp"
              type="number"
              step="0.01"
              min="1.01"
              placeholder="ej: 1.85"
              value={quota}
              onChange={(e) => setQuota(e.target.value)}
            />
          </div>
          <div className="field">
            <label className="lbl">Stake ($)</label>
            <input
              className="inp"
              type="number"
              min="0"
              step="1"
              placeholder="ej: 10"
              value={stake}
              onChange={(e) => setStake(e.target.value)}
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--red)' }}>
          <div style={{ color: 'var(--red)' }}>❌ {error}</div>
        </div>
      )}

      <button
        className="btn btn-green"
        onClick={handlePredict}
        disabled={!canPredict || loading}
        type="button"
      >
        {loading ? 'Analizando...' : 'Predecir →'}
      </button>
    </>
  );
}
