import { useEffect, useMemo, useState } from 'react';
import DashboardPage from './pages/DashboardPage';
import InspectionDetailPage from './pages/InspectionDetailPage';
import TrendsPage from './pages/TrendsPage';
import ConfigurationPage from './pages/ConfigurationPage';
import { inspections as seed } from './data/sampleData';
import { fetchRecentInspections } from './services';

export default function App() {
  const [active, setActive] = useState('Dashboard');
  const [inspections, setInspections] = useState(seed);
  const [selectedInspectionId, setSelectedInspectionId] = useState(seed[0]?.id ?? null);
  const [apiOnline, setApiOnline] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const latest = await fetchRecentInspections();
        if (!cancelled && latest.length) {
          setInspections(latest);
          setSelectedInspectionId(latest[0].id);
          setApiOnline(true);
        }
      } catch {
        if (!cancelled) setApiOnline(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

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
    apiOnline,
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
          <p className="eyebrow">AnomalyMatrix HMI · Phase 3 Real Path</p>
          <h1>Operator-first Inspection Interface</h1>
          <p className="muted">{apiOnline ? 'Backend verbunden (Port 8080)' : 'Offline-Seed-Daten (Backend nicht erreichbar)'}</p>
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
