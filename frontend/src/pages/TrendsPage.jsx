import StatusBadge from '../components/StatusBadge';

function trendState(value) {
  if (value >= 0.85) return 'red';
  if (value >= 0.55) return 'amber';
  return 'green';
}

export default function TrendsPage({ inspections }) {
  const latest = inspections.slice(0, 10);
  const avg = latest.length ? (latest.reduce((s, x) => s + x.score, 0) / latest.length) : 0;
  const worst = latest.length ? Math.max(...latest.map((x) => x.score)) : 0;
  const fails = latest.filter((x) => x.decision === 'red').length;

  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">Trend Monitor</p>
          <h2>Latest synthetic inspection trend</h2>
          <p className="muted">Live card derived from latest run inspections.</p>
        </div>
        <StatusBadge state={trendState(avg)}>avg {avg.toFixed(2)}</StatusBadge>
      </article>

      <article className="card kpi-grid">
        <div><label>Average score (10)</label><strong>{avg.toFixed(2)}</strong></div>
        <div><label>Worst score</label><strong>{worst.toFixed(2)}</strong></div>
        <div><label>Red count</label><strong>{fails}</strong></div>
        <div><label>Total samples</label><strong>{latest.length}</strong></div>
      </article>

      <article className="card">
        <h3>Latest trend points</h3>
        <div className="table">
          {latest.map((i) => (
            <div key={i.id} className="row">
              <span>{new Date(i.timestamp).toLocaleTimeString()}</span>
              <span>{i.id}</span>
              <span>{i.score}</span>
              <StatusBadge state={i.decision}>{i.decision}</StatusBadge>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
