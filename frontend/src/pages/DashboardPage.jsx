import { useMemo, useState } from 'react';
import { hmiState } from '../data/sampleData';
import { runInspection, fetchRecentInspections } from '../services';
import StatusBadge from '../components/StatusBadge';

export default function DashboardPage({ inspections, setInspections, setSelectedInspectionId, goTo }) {
  const [runState, setRunState] = useState('idle'); // idle|running|success|error
  const [notice, setNotice] = useState('Bereit für neue Inspektion.');

  const anomalyRate = useMemo(() => {
    if (!inspections.length) return 0;
    const bad = inspections.filter((x) => x.decision !== 'green').length;
    return ((bad / inspections.length) * 100).toFixed(1);
  }, [inspections]);

  async function handleRunInspection() {
    setRunState('running');
    setNotice('Pipeline wird ausgeführt …');
    try {
      const result = await runInspection();
      const merged = [result, ...inspections.filter((i) => i.id !== result.id)].slice(0, 20);
      setInspections(merged);
      setSelectedInspectionId(result.id);
      setRunState('success');
      setNotice(`Inspektion ${result.id} abgeschlossen (${result.decision.toUpperCase()}).`);
      setTimeout(() => setRunState('idle'), 1500);
    } catch {
      // fallback synthetic refresh path for scaffold usability
      try {
        const latest = await fetchRecentInspections();
        if (latest.length) {
          setInspections(latest);
          setSelectedInspectionId(latest[0].id);
          setRunState('success');
          setNotice(`Inspektion aus latest feed geladen (${latest[0].id}).`);
          setTimeout(() => setRunState('idle'), 1500);
          return;
        }
      } catch {
        // ignore nested errors
      }
      setRunState('error');
      setNotice('Pipeline fehlgeschlagen. Backend-Verbindung prüfen.');
    }
  }

  const stateClass = runState === 'error' ? 'state-red' : runState === 'running' ? 'state-amber' : runState === 'success' ? 'state-green' : 'state-amber';

  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">Operator Dashboard</p>
          <h2>{hmiState.line}</h2>
          <p className="muted">Recipe {hmiState.recipe} · Model {hmiState.modelVersion}</p>
        </div>
        <StatusBadge state={hmiState.status}>{hmiState.statusText}</StatusBadge>
      </article>

      <article className="card run-panel">
        <div>
          <h3>Vertical MVP action</h3>
          <p className="muted">Trigger inspection pipeline and jump to inspection details.</p>
        </div>
        <div className="run-actions">
          <button className="tab active" onClick={handleRunInspection} disabled={runState === 'running'}>
            {runState === 'running' ? 'Running…' : 'Run Inspection Pipeline'}
          </button>
          <button className="tab" onClick={() => goTo('Inspection Detail')}>Open Inspection Detail</button>
          <StatusBadge state={stateClass.replace('state-','')}>{notice}</StatusBadge>
        </div>
      </article>

      <article className="card kpi-grid">
        <div><label>Cycle p95</label><strong>{hmiState.kpis.cycleMsP95} ms</strong></div>
        <div><label>Anomaly Rate</label><strong>{anomalyRate}%</strong></div>
        <div><label>Queue Lag</label><strong>{hmiState.kpis.queueLagMs} ms</strong></div>
        <div><label>OPC UA Error</label><strong>{hmiState.kpis.opcUaPublishErrorRate}%</strong></div>
      </article>

      <article className="card">
        <h3>Latest inspections</h3>
        <div className="table">
          {inspections.map((i) => (
            <button
              key={i.id}
              className="row row-btn"
              onClick={() => {
                setSelectedInspectionId(i.id);
                goTo('Inspection Detail');
              }}
            >
              <span>{new Date(i.timestamp).toLocaleTimeString()}</span>
              <span>{i.id}</span>
              <span>{i.part}</span>
              <StatusBadge state={i.decision}>{i.decision}</StatusBadge>
            </button>
          ))}
        </div>
      </article>
    </section>
  );
}
