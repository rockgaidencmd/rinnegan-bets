import { TeamAutocomplete } from './TeamAutocomplete.jsx';
import { TeamStatsPreview } from './TeamStatsPreview.jsx';


/**
 * Step 1 of the prediction flow — pick home + away teams.
 * Stats preview auto-loads once a team is selected.
 */
export function TeamPickerStep({ home, away, onHomeChange, onAwayChange }) {
  return (
    <>
      <div className="card">
        <div className="card-hdr">
          <div className="card-title">1. Equipos</div>
        </div>
        <TeamAutocomplete
          label="Equipo Local"
          selected={home}
          onSelect={onHomeChange}
          placeholder="ej: IDV, Napoli, BSC..."
        />
        {home && <TeamStatsPreview teamId={home.id} />}
      </div>

      <div className="card">
        <TeamAutocomplete
          label="Equipo Visitante"
          selected={away}
          onSelect={onAwayChange}
          placeholder="ej: LDU, Inter, Emelec..."
        />
        {away && <TeamStatsPreview teamId={away.id} />}
      </div>
    </>
  );
}
