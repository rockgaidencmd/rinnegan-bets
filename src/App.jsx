import { useState } from 'react';
import './styles/app.css';
import { BankrollWidget } from './components/BankrollWidget.jsx';
import { HistoryView } from './components/HistoryView.jsx';
import { LeaguesView } from './components/LeaguesView.jsx';
import { MatchesView } from './components/MatchesView.jsx';
import { Sidebar } from './components/Sidebar.jsx';
import { SmartPredict } from './components/SmartPredict.jsx';


const VIEW_TITLES = {
  predict: 'Predicción',
  leagues: 'Ligas',
  matches: 'Partidos',
  history: 'Historial',
};

const SIDEBAR_COLLAPSED_KEY = 'rinnegan:sidebar:collapsed';


export default function App() {
  const [activeView, setActiveView] = useState('predict');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    // Read once on mount — keeps the user's last choice across reloads
    return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === 'true';
  });

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(next));
      return next;
    });
  };

  let view;
  if (activeView === 'predict') view = <SmartPredict />;
  else if (activeView === 'leagues') view = <LeaguesView />;
  else if (activeView === 'matches') view = <MatchesView />;
  else if (activeView === 'history') view = <HistoryView />;

  return (
    <div className={`layout ${sidebarCollapsed ? 'layout-collapsed' : ''}`}>
      <Sidebar
        activeView={activeView}
        onSelect={setActiveView}
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
        collapsed={sidebarCollapsed}
        onToggleCollapsed={toggleSidebar}
      />
      <main className="main">
        <div className="main-topbar">
          <button
            className="hamburger"
            onClick={() => setMobileMenuOpen(true)}
            type="button"
            aria-label="Menu"
          >
            ☰
          </button>
          <div className="main-title">{VIEW_TITLES[activeView]}</div>
        </div>
        <BankrollWidget />
        {view}
      </main>
    </div>
  );
}
