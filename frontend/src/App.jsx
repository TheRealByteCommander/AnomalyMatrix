import { useMemo, useState } from 'react';
import DashboardPage from './pages/DashboardPage';
import InspectionDetailPage from './pages/InspectionDetailPage';
import TrendsPage from './pages/TrendsPage';
import ConfigurationPage from './pages/ConfigurationPage';

const pages = {
  Dashboard: DashboardPage,
  'Inspection Detail': InspectionDetailPage,
  Trends: TrendsPage,
  Configuration: ConfigurationPage,
};

export default function App() {
  const [active, setActive] = useState('Dashboard');
  const ActivePage = useMemo(() => pages[active], [active]);

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AnomalyMatrix HMI · MVP Scaffold</p>
          <h1>Operator-first Inspection Interface</h1>
        </div>
        <nav className="tabs" aria-label="Primary screens">
          {Object.keys(pages).map((name) => (
            <button
              key={name}
              onClick={() => setActive(name)}
              className={name === active ? 'tab active' : 'tab'}
            >
              {name}
            </button>
          ))}
        </nav>
      </header>
      <ActivePage />
    </div>
  );
}
