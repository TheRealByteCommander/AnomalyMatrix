import { useMemo, useState } from 'react';
import DashboardPage from './pages/DashboardPage';
import InspectionDetailPage from './pages/InspectionDetailPage';
import TrendsPage from './pages/TrendsPage';
import ConfigurationPage from './pages/ConfigurationPage';
import { inspections as seed } from './data/sampleData';

export default function App() {
  const [active, setActive] = useState('Dashboard');
  const [inspections, setInspections] = useState(seed);
  const [selectedInspectionId, setSelectedInspectionId] = useState(seed[0]?.id ?? null);

  const selectedInspection = useMemo(
    () => inspections.find((i) => i.id === selectedInspectionId) || inspections[0] || null,
    [inspections, selectedInspectionId]
  );

  const pageProps = {
    inspections,
    setInspections,
    selectedInspection,
    setSelectedInspectionId,
    goTo: setActive,
  };

  const pages = {
    Dashboard: <DashboardPage {...pageProps} />,
    'Inspection Detail': <InspectionDetailPage {...pageProps} />,
    Trends: <TrendsPage {...pageProps} />,
    Configuration: <ConfigurationPage {...pageProps} />,
  };

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AnomalyMatrix HMI · Phase 2 Vertical MVP</p>
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
      {pages[active]}
    </div>
  );
}
