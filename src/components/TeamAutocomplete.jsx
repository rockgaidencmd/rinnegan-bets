import { useState } from 'react';
import { useTeamSearch } from '../hooks/useTeamSearch.js';


/**
 * TeamAutocomplete — input with live search dropdown.
 *
 * Controlled by parent: parent owns `selected` (Team object or null)
 * and provides `onSelect`. User typing is internal state.
 */
export function TeamAutocomplete({ label, selected, onSelect, placeholder }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const { results, loading } = useTeamSearch(query);

  const handleSelect = (team) => {
    onSelect(team);
    setQuery('');
    setOpen(false);
  };

  const handleClear = () => {
    onSelect(null);
    setQuery('');
  };

  if (selected) {
    return (
      <div className="autocomplete-selected">
        <label className="lbl">{label}</label>
        <div className="autocomplete-chip">
          <span className="autocomplete-team-name">{selected.name}</span>
          <span className="autocomplete-team-meta">{selected.league} · {selected.country || '—'}</span>
          <button className="autocomplete-clear" onClick={handleClear} type="button">×</button>
        </div>
      </div>
    );
  }

  return (
    <div className="autocomplete">
      <label className="lbl">{label}</label>
      <input
        className="inp"
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 200)}
        placeholder={placeholder || 'Buscar equipo (ej: IDV, Napoli, BSC)'}
        autoComplete="off"
      />
      {open && query.trim() && (
        <div className="autocomplete-dropdown">
          {loading && <div className="autocomplete-status">Buscando...</div>}
          {!loading && results.length === 0 && (
            <div className="autocomplete-status autocomplete-empty">
              Sin resultados. Intenta otro nombre o alias.
            </div>
          )}
          {!loading && results.map((team) => (
            <button
              key={`${team.id}-${team.league}`}
              className="autocomplete-option"
              onMouseDown={() => handleSelect(team)}
              type="button"
            >
              <span className="autocomplete-team-name">{team.name}</span>
              <span className="autocomplete-team-meta">{team.league} · {team.country || '—'}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
