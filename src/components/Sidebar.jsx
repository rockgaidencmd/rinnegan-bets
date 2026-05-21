import { RefreshButton } from './RefreshButton.jsx';


/**
 * Sidebar — left nav for switching between views.
 *
 * Desktop: collapsible (icon-only) via the toggle. State persists in
 * localStorage so it stays collapsed across reloads.
 * Mobile: drawer that slides in from the left.
 */

const NAV_ITEMS = [
  { key: 'predict', icon: '🎯', label: 'Predicción' },
  { key: 'leagues', icon: '🏆', label: 'Ligas' },
  { key: 'matches', icon: '⚽', label: 'Partidos' },
  { key: 'history', icon: '📊', label: 'Historial' },
];


export function Sidebar({
  activeView, onSelect, mobileOpen, onMobileClose,
  collapsed, onToggleCollapsed,
}) {
  return (
    <>
      {mobileOpen && <div className="sidebar-backdrop" onClick={onMobileClose} />}
      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''} ${collapsed ? 'sidebar-collapsed' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <span className="sidebar-logo-name">RINNEG<em>AN</em></span>
            <span className="sidebar-logo-bets">BETS</span>
          </div>
          <button
            className="sidebar-collapse-btn"
            onClick={onToggleCollapsed}
            type="button"
            aria-label={collapsed ? 'Expandir menú' : 'Colapsar menú'}
            title={collapsed ? 'Expandir menú' : 'Colapsar menú'}
          >
            {collapsed ? '›' : '‹'}
          </button>
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
              title={collapsed ? item.label : undefined}
            >
              <span className="sidebar-icon">{item.icon}</span>
              <span className="sidebar-label">{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <RefreshButton collapsed={collapsed} />
        </div>
      </aside>
    </>
  );
}
