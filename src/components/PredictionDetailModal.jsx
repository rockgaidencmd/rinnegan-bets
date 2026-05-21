import { useEffect, useState } from 'react';
import { MatchHistory } from './MatchHistory.jsx';


/**
 * PredictionDetailModal — tabbed view of each team's recent matches.
 *
 * Receives already-fetched team data from the parent (no extra requests).
 * Closes on backdrop click, × button, or Escape key.
 */
export function PredictionDetailModal({ home, away, homeData, awayData, onClose }) {
  const [activeTab, setActiveTab] = useState('home');

  // Escape key to close — listen on document so it works regardless of focus
  useEffect(() => {
    const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const activeTeam = activeTab === 'home' ? home : away;
  const activeData = activeTab === 'home' ? homeData : awayData;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} type="button" aria-label="Cerrar">×</button>

        <div className="modal-header">
          <div className="modal-team-name">Últimos partidos</div>
          <div className="modal-team-meta">Detalle por equipo</div>
        </div>

        <div className="tabs">
          <button
            className={`tab ${activeTab === 'home' ? 'tab-active' : ''}`}
            onClick={() => setActiveTab('home')}
            type="button"
          >
            <span className="tab-role">LOCAL</span>
            <span className="tab-name">{home.name}</span>
          </button>
          <button
            className={`tab ${activeTab === 'away' ? 'tab-active' : ''}`}
            onClick={() => setActiveTab('away')}
            type="button"
          >
            <span className="tab-role">VISITANTE</span>
            <span className="tab-name">{away.name}</span>
          </button>
        </div>

        <div className="tab-panel">
          {activeData.loading && <div className="modal-loading">Cargando...</div>}
          {!activeData.loading && (
            <MatchHistory teamId={activeTeam.id} matches={activeData.matches} />
          )}
        </div>
      </div>
    </div>
  );
}
