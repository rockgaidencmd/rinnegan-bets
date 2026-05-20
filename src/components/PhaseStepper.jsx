export function PhaseStepper({ currentPhase, onPhaseChange }) {
  const phases = [
    { label: "Prepartido" },
    { label: "Contexto" },
    { label: "En Vivo" },
  ];

  return (
    <div className="stepper">
      {phases.map((s, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", flex: i < 2 ? 1 : 0 }}>
          <div
            className={`step ${currentPhase === i ? "active" : currentPhase > i ? "done" : ""}`}
            onClick={() => onPhaseChange(i)}
            style={{ cursor: "pointer" }}
          >
            <div className="step-num">{currentPhase > i ? "✓" : i + 1}</div>
            <div className="step-label">{s.label}</div>
          </div>
          {i < 2 && <div className={`step-line ${currentPhase > i ? "done" : ""}`} />}
        </div>
      ))}
    </div>
  );
}
