import { useState } from 'react';
import { useFixtures } from '../hooks/useFixtures.js';
import { useLeagues } from '../hooks/useLeagues.js';
import { formatDateTime } from '../utils/dates.js';
import { TeamDetailModal } from './TeamDetailModal.jsx';
import { TeamPickerStep } from './TeamPickerStep.jsx';
import { TeamStatsPreview } from './TeamStatsPreview.jsx';


/**
 * FixturePicker — primary way to pick a match: choose league → click upcoming fixture.
 *
 * Two clear modes (mutually exclusive — no "delete team while another is selected" confusion):
 *   - SELECTED: shows the matchup + each team's stats. One "limpiar" button to start over.
 *   - PICKING: shows league chips + upcoming fixtures + a collapsible "búsqueda libre"
 *              fallback for hypothetical matchups.
 */
export function FixturePicker({ home, away, onHomeChange, onAwayChange }) {
  const [league, setLeague] = useState('');
  const [showCustom, setShowCustom] = useState(false);
  const [teamModalFor, setTeamModalFor] = useState(null);  // 'home' | 'away' | null
  const { leagues, loading: leaguesLoading } = useLeagues();
  const { fixtures, loading, error } = useFixtures(league);

  const hasSelection = !!(home && away);

  const handleFixtureClick = (fixture) => {
    if (!fixture.home_team_id || !fixture.away_team_id) return;
    onHomeChange({
      id: fixture.home_team_id,
      name: fixture.home_team_name,
      league: fixture.league,
    });
    onAwayChange({
      id: fixture.away_team_id,
      name: fixture.away_team_name,
      league: fixture.league,
    });
  };

  const clearSelection = () => {
    onHomeChange(null);
    onAwayChange(null);
    setShowCustom(false);
  };

  // ───────────────────────── SELECTED MODE ─────────────────────────
  if (hasSelection) {
    const modalTeam = teamModalFor === 'home' ? home : teamModalFor === 'away' ? away : null;
    return (
      <>
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">1. Partido</div>
            <button className="btn-link" onClick={clearSelection} type="button">
              cambiar partido
            </button>
          </div>

          <div className="fixture-selected">
            <span className="fixture-selected-team">{home.name}</span>
            <span className="fixture-selected-vs">vs</span>
            <span className="fixture-selected-team">{away.name}</span>
          </div>

          <div className="fixture-selected-stats">
            <div className="fixture-selected-stats-col">
              <div className="fixture-selected-stats-header">
                <span className="fixture-selected-stats-label">LOCAL</span>
                <button
                  className="btn-link"
                  onClick={() => setTeamModalFor('home')}
                  type="button"
                >
                  ver partidos →
                </button>
              </div>
              <TeamStatsPreview teamId={home.id} />
            </div>
            <div className="fixture-selected-stats-divider" />
            <div className="fixture-selected-stats-col">
              <div className="fixture-selected-stats-header">
                <span className="fixture-selected-stats-label">VISITANTE</span>
                <button
                  className="btn-link"
                  onClick={() => setTeamModalFor('away')}
                  type="button"
                >
                  ver partidos →
                </button>
              </div>
              <TeamStatsPreview teamId={away.id} />
            </div>
          </div>
        </div>

        {modalTeam && (
          <TeamDetailModal
            team={modalTeam}
            onClose={() => setTeamModalFor(null)}
          />
        )}
      </>
    );
  }

  // ───────────────────────── PICKING MODE ──────────────────────────
  return (
    <>
      <div className="card">
        <div className="card-hdr">
          <div className="card-title">1. Partido</div>
        </div>

        <label className="lbl">Liga</label>
        {leaguesLoading ? (
          <div className="fixtures-status">Cargando ligas...</div>
        ) : (
          <div className="league-chips">
            {leagues.map((l) => (
              <button
                key={l.code}
                className={`league-chip ${league === l.code ? 'league-chip-active' : ''}`}
                onClick={() => setLeague(league === l.code ? '' : l.code)}
                type="button"
                title={league === l.code ? 'Cerrar lista de partidos' : `Ver partidos de ${l.name}`}
              >
                <span className="league-chip-code">{l.code}</span>
                <span className="league-chip-label">{l.name}</span>
              </button>
            ))}
          </div>
        )}

        {league && (
          <div className="fixtures-section">
            <div className="fixtures-section-title">
              Próximos partidos · 7 días
            </div>
            {loading && <div className="fixtures-status">Cargando...</div>}
            {error && <div className="fixtures-status fixtures-error">❌ {error}</div>}
            {!loading && !error && fixtures.length === 0 && (
              <div className="fixtures-status fixtures-empty">
                Sin partidos próximos en los siguientes 7 días.
              </div>
            )}
            {!loading && fixtures.length > 0 && (
              <div className="fixtures-list">
                {fixtures.map((f, i) => {
                  const playable = f.home_team_id && f.away_team_id;
                  return (
                    <button
                      key={`${f.home_team_name}-${f.away_team_name}-${i}`}
                      className={`fixture-card ${playable ? '' : 'fixture-card-disabled'}`}
                      onClick={() => handleFixtureClick(f)}
                      disabled={!playable}
                      type="button"
                      title={playable ? 'Predecir este partido' : 'Equipo no disponible en la BD'}
                    >
                      <div className="fixture-card-date mono">
                        {formatDateTime(f.match_date)}
                      </div>
                      <div className="fixture-card-teams">
                        <span className="fixture-card-home">{f.home_team_name}</span>
                        <span className="fixture-card-vs">vs</span>
                        <span className="fixture-card-away">{f.away_team_name}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Fallback: free search — only relevant before any team is picked */}
      <div className="card">
        <button
          className="custom-pick-toggle"
          onClick={() => setShowCustom(!showCustom)}
          type="button"
        >
          <span>{showCustom ? '▾' : '▸'} Otro partido (búsqueda libre)</span>
        </button>
        {showCustom && (
          <div style={{ marginTop: 14 }}>
            <TeamPickerStep
              home={home}
              away={away}
              onHomeChange={onHomeChange}
              onAwayChange={onAwayChange}
            />
          </div>
        )}
      </div>
    </>
  );
}
