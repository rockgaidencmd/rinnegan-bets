import { formatDateShort } from '../utils/dates.js';


/**
 * MatchHistory — list of recent matches for a team, rendered from a
 * pre-fetched array. Pure presentational: parent owns the data.
 */
export function MatchHistory({ teamId, matches }) {
  if (!matches.length) {
    return <div className="match-history-empty">Sin partidos en BD.</div>;
  }

  return (
    <div className="match-history">
      {matches.map((m) => {
        const isHome = m.home_team_id === teamId;
        const teamGoals = isHome ? m.home_goals : m.away_goals;
        const oppGoals = isHome ? m.away_goals : m.home_goals;
        const oppName = isHome ? m.away_team_name : m.home_team_name;
        const won = teamGoals > oppGoals;
        const drew = teamGoals === oppGoals;
        const resultClass = won ? 'res-w' : drew ? 'res-d' : 'res-l';
        const resultLetter = won ? 'G' : drew ? 'E' : 'P';
        const teamXg = isHome ? m.home_xg : m.away_xg;
        const oppXg = isHome ? m.away_xg : m.home_xg;
        return (
          <div key={m.id} className="match-row">
            <span className={`match-result ${resultClass}`}>{resultLetter}</span>
            <span className="match-date-small mono">{formatDateShort(m.match_date)}</span>
            <span className="match-vs">{isHome ? 'vs' : 'en'}</span>
            <span className="match-opp">{oppName}</span>
            <span className="match-league-tag mono">{m.league}</span>
            <span className="match-score mono">{teamGoals}-{oppGoals}</span>
            {teamXg !== null && teamXg !== undefined && (
              <span className="match-xg mono">
                xG: {teamXg?.toFixed(1)}-{oppXg?.toFixed(1)}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
