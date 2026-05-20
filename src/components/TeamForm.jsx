export function TeamForm({ team, onChange }) {
  const updateGame = (i, field, val) => {
    const games = team.games.map((g, idx) => idx === i ? { ...g, [field]: val } : g);
    onChange({ ...team, games });
  };

  return (
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
                  <div
                    key={r}
                    className={`res-pill ${g.res === r ? (r === "W" ? "w" : r === "D" ? "d" : "l") : ""}`}
                    style={{ padding: "4px 2px", fontSize: "0.72rem" }}
                    onClick={() => updateGame(i, "res", g.res === r ? "" : r)}
                  >
                    {r}
                  </div>
                ))}
              </div>
            </td>
            {["gf", "gc", "tar", "cor"].map(f => (
              <td key={f}>
                <input
                  className="inp inp-sm"
                  style={{ textAlign: "center", padding: "5px 4px", width: "100%" }}
                  type="number"
                  min="0"
                  max="20"
                  placeholder="0"
                  value={g[f]}
                  onChange={e => updateGame(i, f, e.target.value)}
                />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
