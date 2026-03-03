import { trends } from '../data/sampleData';
import StatusBadge from '../components/StatusBadge';

export default function TrendsPage() {
  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">Trend Monitor</p>
          <h2>Process drift & warnings</h2>
          <p className="muted">Read-only operator overview with clear thresholds.</p>
        </div>
      </article>
      <article className="card">
        <h3>Trend status</h3>
        <div className="table">
          {trends.map((t) => (
            <div key={t.metric} className="row">
              <span>{t.metric}</span>
              <span>{t.now}</span>
              <span>limit {t.threshold}</span>
              <StatusBadge state={t.state}>{t.state}</StatusBadge>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
