import { useEffect, useState } from 'react';
import { api } from '../utils/api.js';
import { TeamDetailModal } from './TeamDetailModal.jsx';


export function TeamsByLeague({ leagueCode }) {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTeam, setSelectedTeam] = useState(null);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    (async () => {
      try {
        const data = await api.getTeamsByLeague(leagueCode);
        if (!ignore) {
          setTeams(data);
        }
      } catch {
        if (!ignore) {
          setTeams([]);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    })();
    return () => {
      ignore = true;
    };
  }, [leagueCode]);

  if (loading) {
    return <div className="teams-loading">Cargando equipos...</div>;
  }

  return (
    <>
      <div className="teams-list">
        {teams.map((team) => (
          <button
            key={team.id}
            className="team-chip"
            onClick={() => setSelectedTeam(team)}
            type="button"
          >
            {team.name}
          </button>
        ))}
      </div>
      {selectedTeam && (
        <TeamDetailModal team={selectedTeam} onClose={() => setSelectedTeam(null)} />
      )}
    </>
  );
}
