import { hmiState, inspections } from '../data/sampleData';
import StatusBadge from '../components/StatusBadge';

export default function DashboardPage() {
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

      <article className="card kpi-grid">
        <div><label>Cycle p95</label><strong>{hmiState.kpis.cycleMsP95} ms</strong></div>
        <div><label>Anomaly Rate</label><strong>{hmiState.kpis.anomalyRate}%</strong></div>
        <div><label>Queue Lag</label><strong>{hmiState.kpis.queueLagMs} ms</strong></div>
        <div><label>OPC UA Error</label><strong>{hmiState.kpis.opcUaPublishErrorRate}%</strong></div>
      </article>

      <article className="card">
        <h3>Latest inspections</h3>
        <div className="table">
          {inspections.map((i) => (
            <div key={i.id} className="row">
              <span>{i.ts}</span>
              <span>{i.id}</span>
              <span>{i.part}</span>
              <StatusBadge state={i.decision}>{i.decision}</StatusBadge>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
