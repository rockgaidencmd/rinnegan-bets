export function MatchSelector({ matches, active, onSelect, onAdd }) {
  return (
    <div className="match-bar">
      {matches.map((m, i) => (
        <button
          key={m.id}
          className={`match-btn ${i === active ? "active" : ""} ${m.phase === 2 ? "live-mode" : m.phase === 1 ? "ready" : ""}`}
          onClick={() => onSelect(i)}
        >
          <span className="dot" />
          {m.name || `Partido ${i + 1}`}
        </button>
      ))}
      {matches.length < 3 && (
        <button className="add-match-btn" onClick={onAdd}>+</button>
      )}
    </div>
  );
}
