/**
 * Step 2 — match context (importance + key absences).
 *
 * Fully controlled: parent (usePredictionForm) owns all state.
 */

const IMPORTANCE_OPTIONS = [
  { key: 'final', icon: '🏆', label: 'Final / Copa' },
  { key: 'clasif', icon: '🎯', label: 'Clasificatorio' },
  { key: 'normal', icon: '⚽', label: 'Liga normal' },
  { key: 'calendario', icon: '📅', label: 'Solo calendario' },
];


function AbsenceToggle({ label, value, onChange }) {
  return (
    <div className="field">
      <label className="lbl">{label}</label>
      <div className="pill-group">
        {[
          { k: false, l: 'No' },
          { k: true, l: 'Sí' },
        ].map((o) => (
          <div
            key={String(o.k)}
            className={`pill-opt ${value === o.k ? (o.k ? 'sel-r' : 'sel') : ''}`}
            onClick={() => onChange(o.k)}
          >
            {o.l}
          </div>
        ))}
      </div>
    </div>
  );
}


export function ContextStep({
  importance, onImportanceChange,
  homeAbsences, onHomeAbsencesChange,
  awayAbsences, onAwayAbsencesChange,
}) {
  return (
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
            onClick={() => onImportanceChange(o.key)}
          >
            <div className="imp-icon">{o.icon}</div>
            <div className="imp-label">{o.label}</div>
          </div>
        ))}
      </div>

      <div className="g2" style={{ marginTop: 12 }}>
        <AbsenceToggle
          label="Ausencias local"
          value={homeAbsences}
          onChange={onHomeAbsencesChange}
        />
        <AbsenceToggle
          label="Ausencias visitante"
          value={awayAbsences}
          onChange={onAwayAbsencesChange}
        />
      </div>
    </div>
  );
}
