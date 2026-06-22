import { useEffect, useMemo, useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import { fetchTrendSummary } from '../services';

function trendState(value) {
  if (value >= 0.85) return 'red';
  if (value >= 0.55) return 'amber';
  return 'green';
}

export default function TrendsPage({ inspections }) {
  const [summary, setSummary] = useState(null);
  const latest = inspections.slice(0, 10);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchTrendSummary();
        if (!cancelled) setSummary(data);
      } catch {
        if (!cancelled) setSummary(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [inspections.length]);

  const localAvg = latest.length ? latest.reduce((s, x) => s + x.score, 0) / latest.length : 0;
  const avg = summary?.avg_score ?? localAvg;
  const worst = summary?.max_score ?? (latest.length ? Math.max(...latest.map((x) => x.score)) : 0);
  const fails = summary?.anomaly_count ?? latest.filter((x) => x.decision === 'red').length;
  const total = summary?.count ?? latest.length;

  const sourceLabel = useMemo(
    () => (summary ? 'API trend-summary' : 'lokale Inspektionen'),
    [summary]
  );

  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">Trend Monitor</p>
          <h2>Inspection trend summary</h2>
          <p className="muted">Quelle: {sourceLabel}</p>
        </div>
        <StatusBadge state={trendState(avg)}>avg {avg.toFixed(2)}</StatusBadge>
      </article>

      <article className="card kpi-grid">
        <div><label>Average score</label><strong>{avg.toFixed(2)}</strong></div>
        <div><label>Worst score</label><strong>{worst.toFixed(2)}</strong></div>
        <div><label>Anomaly count</label><strong>{fails}</strong></div>
        <div><label>Total samples</label><strong>{total}</strong></div>
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
