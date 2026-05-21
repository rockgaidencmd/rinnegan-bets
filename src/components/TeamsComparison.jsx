import { useState } from 'react';
import { useTeamData } from '../hooks/useTeamData.js';
import { PredictionDetailModal } from './PredictionDetailModal.jsx';


/**
 * TeamsComparison — side-by-side stats of two teams for the prediction screen.
 *
 * Always visible — no click required to see basic comparison. A "Ver detalle"
 * button opens a modal with last matches for each team in tabs.
 */
export function TeamsComparison({ home, away }) {
  const [detailOpen, setDetailOpen] = useState(false);

  const homeData = useTeamData(home.id);
  const awayData = useTeamData(away.id);

  if (homeData.loading || awayData.loading) {
    return (
      <div className="card">
        <div className="card-hdr">
          <div className="card-title">Comparación</div>
        </div>
        <div className="comparison-loading">Cargando stats...</div>
      </div>
    );
  }

  if (!homeData.stats || !awayData.stats) {
    return null;
  }

  return (
    <>
      <div className="card">
        <div className="card-hdr">
          <div className="card-title">Comparación</div>
          <button
            className="btn-link"
            onClick={() => setDetailOpen(true)}
            type="button"
          >
            ver últimos partidos →
          </button>
        </div>

        <div className="comparison-grid">
          <div className="comparison-col">
            <div className="comparison-team-name">{home.name}</div>
            <div className="comparison-role">LOCAL</div>
          </div>
          <div className="comparison-center"></div>
          <div className="comparison-col comparison-col-right">
            <div className="comparison-team-name">{away.name}</div>
            <div className="comparison-role">VISITANTE</div>
          </div>

          <ComparisonRow
            label="Forma (últimos partidos)"
            home={`${homeData.stats.wins}G ${homeData.stats.draws}E ${homeData.stats.losses}P`}
            away={`${awayData.stats.wins}G ${awayData.stats.draws}E ${awayData.stats.losses}P`}
          />
          <ComparisonRow
            label="Score de forma"
            home={`${homeData.stats.form_score.toFixed(0)}`}
            away={`${awayData.stats.form_score.toFixed(0)}`}
            higherIsBetter
            homeNum={homeData.stats.form_score}
            awayNum={awayData.stats.form_score}
          />
          <ComparisonRow
            label="Goles a favor / partido"
            home={homeData.stats.avg_goals_for.toFixed(2)}
            away={awayData.stats.avg_goals_for.toFixed(2)}
            higherIsBetter
            homeNum={homeData.stats.avg_goals_for}
            awayNum={awayData.stats.avg_goals_for}
          />
          <ComparisonRow
            label="Goles concedidos / partido"
            home={homeData.stats.avg_goals_against.toFixed(2)}
            away={awayData.stats.avg_goals_against.toFixed(2)}
            higherIsBetter={false}
            homeNum={homeData.stats.avg_goals_against}
            awayNum={awayData.stats.avg_goals_against}
          />
          {homeData.stats.avg_xg_for !== null && awayData.stats.avg_xg_for !== null && (
            <ComparisonRow
              label="xG / partido"
              home={homeData.stats.avg_xg_for.toFixed(2)}
              away={awayData.stats.avg_xg_for.toFixed(2)}
              higherIsBetter
              homeNum={homeData.stats.avg_xg_for}
              awayNum={awayData.stats.avg_xg_for}
            />
          )}
          {homeData.stats.avg_possession !== null && awayData.stats.avg_possession !== null && (
            <ComparisonRow
              label="Posesión promedio"
              home={`${homeData.stats.avg_possession.toFixed(0)}%`}
              away={`${awayData.stats.avg_possession.toFixed(0)}%`}
              higherIsBetter
              homeNum={homeData.stats.avg_possession}
              awayNum={awayData.stats.avg_possession}
            />
          )}
        </div>
      </div>

      {detailOpen && (
        <PredictionDetailModal
          home={home}
          away={away}
          homeData={homeData}
          awayData={awayData}
          onClose={() => setDetailOpen(false)}
        />
      )}
    </>
  );
}


/** A single comparison row with optional "winner" highlight. */
function ComparisonRow({ label, home, away, higherIsBetter, homeNum, awayNum }) {
  const { homeBetter, awayBetter } = pickWinner({ higherIsBetter, homeNum, awayNum });

  return (
    <>
      <div className={`comparison-value ${homeBetter ? 'comparison-winner' : ''}`}>
        {home}
      </div>
      <div className="comparison-label">{label}</div>
      <div className={`comparison-value comparison-value-right ${awayBetter ? 'comparison-winner' : ''}`}>
        {away}
      </div>
    </>
  );
}


/** Decide which side wins a stat. Returns { homeBetter, awayBetter }. */
function pickWinner({ higherIsBetter, homeNum, awayNum }) {
  if (higherIsBetter === undefined || homeNum === undefined || awayNum === undefined) {
    return { homeBetter: false, awayBetter: false };
  }
  if (homeNum === awayNum) {
    return { homeBetter: false, awayBetter: false };
  }
  const homeWins = higherIsBetter ? homeNum > awayNum : homeNum < awayNum;
  return { homeBetter: homeWins, awayBetter: !homeWins };
}
