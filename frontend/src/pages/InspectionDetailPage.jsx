import { inspections } from '../data/sampleData';
import StatusBadge from '../components/StatusBadge';

export default function InspectionDetailPage() {
  const selected = inspections[2];
  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">Inspection Detail</p>
          <h2>{selected.id}</h2>
          <p className="muted">Part: {selected.part} · Time: {selected.ts}</p>
        </div>
        <StatusBadge state={selected.decision}>{selected.defect}</StatusBadge>
      </article>
      <article className="card">
        <h3>Operator actions</h3>
        <ul className="muted">
          <li>Review anomaly heatmap</li>
          <li>Confirm defect class</li>
          <li>Submit QA feedback</li>
        </ul>
      </article>
    </section>
  );
}
