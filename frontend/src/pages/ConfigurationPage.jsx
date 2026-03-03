import { configSummary } from '../data/sampleData';
import StatusBadge from '../components/StatusBadge';

export default function ConfigurationPage() {
  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">Configuration</p>
          <h2>Recipe & integration profile</h2>
          <p className="muted">Wireframe-level config visibility, no write actions in scaffold.</p>
        </div>
        <StatusBadge state="green">Config valid</StatusBadge>
      </article>
      <article className="card kpi-grid">
        <div><label>OPC UA profile</label><strong>{configSummary.opcUaProfile}</strong></div>
        <div><label>Recipe version</label><strong>{configSummary.recipeVersion}</strong></div>
        <div><label>Model profile</label><strong>{configSummary.modelProfile}</strong></div>
        <div><label>Audit mode</label><strong>{configSummary.auditMode}</strong></div>
      </article>
    </section>
  );
}
