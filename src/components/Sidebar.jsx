/**
 * Sidebar — fixed left nav for switching between views.
 * Controlled: parent owns the activeView state.
 */

const NAV_ITEMS = [
  { key: 'predict', icon: '🎯', label: 'Predicción' },
  { key: 'leagues', icon: '🏆', label: 'Ligas' },
  { key: 'matches', icon: '⚽', label: 'Partidos' },
  { key: 'history', icon: '📊', label: 'Historial' },
];


export function Sidebar({ activeView, onSelect, mobileOpen, onMobileClose }) {
  return (
    <>
      {mobileOpen && <div className="sidebar-backdrop" onClick={onMobileClose} />}
      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-logo">
          RINNEG<em>AN</em>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              className={`sidebar-item ${activeView === item.key ? 'sidebar-item-active' : ''}`}
              onClick={() => {
                onSelect(item.key);
                onMobileClose?.();
              }}
              type="button"
            >
              <span className="sidebar-icon">{item.icon}</span>
              <span className="sidebar-label">{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-version">v2 · 3 fases</div>
        </div>
      </aside>
    </>
  );
}
