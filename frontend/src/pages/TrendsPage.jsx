import { useEffect, useMemo, useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import ContextHelp from '../components/ContextHelp';
import { fetchTrendSummary } from '../services';
import { useI18n } from '../i18n/I18nProvider';

function trendState(value) {
  if (value >= 0.85) return 'red';
  if (value >= 0.55) return 'amber';
  return 'green';
}

export default function TrendsPage({ inspections, openHelp }) {
  const { t } = useI18n();
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
    () => (summary ? t('trends.sourceApi') : t('trends.sourceLocal')),
    [summary, t]
  );

  const trendSeverity = summary?.trend_severity;
  const trendBadgeState = trendSeverity && summary?.trend_warning ? trendSeverity : trendState(avg);
  const trendBadgeLabel = summary?.trend_warning
    ? t(`dashboard.statusTrend.${trendSeverity || 'amber'}`)
    : t('trends.avgBadge', { value: avg.toFixed(2) });

  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">{t('trends.eyebrow')}</p>
          <h2>{t('trends.title')}</h2>
          <p className="muted">{t('trends.source')}: {sourceLabel}</p>
          <ContextHelp articleId="trends-overview" onOpen={openHelp} />
        </div>
        <StatusBadge state={trendBadgeState}>{trendBadgeLabel}</StatusBadge>
      </article>

      <article className="card kpi-grid">
        <div><label>{t('trends.kpiAvg')}</label><strong>{avg.toFixed(2)}</strong></div>
        <div><label>{t('trends.kpiWorst')}</label><strong>{worst.toFixed(2)}</strong></div>
        <div><label>{t('trends.kpiAnomalyCount')}</label><strong>{fails}</strong></div>
        <div><label>{t('trends.kpiTotal')}</label><strong>{total}</strong></div>
      </article>

      <article className="card">
        <h3>{t('trends.pointsTitle')}</h3>
        <div className="table">
          {latest.map((i) => (
            <div key={i.id} className="row">
              <span>{new Date(i.timestamp).toLocaleTimeString()}</span>
              <span>{i.id}</span>
              <span>{i.score}</span>
              <StatusBadge state={i.decision}>{t(`decision.${i.decision}`)}</StatusBadge>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
