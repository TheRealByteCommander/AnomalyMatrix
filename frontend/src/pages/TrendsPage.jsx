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
  const byCamera = summary?.by_camera || [];

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
          {summary?.drifting_camera_id ? (
            <p className="muted">
              {t('trends.driftCamera')}: <strong>{summary.drifting_camera_id}</strong>
              {summary.drift_score != null ? ` · ${t('trends.driftScore')} ${Number(summary.drift_score).toFixed(2)}` : ''}
              {summary.score_delta != null ? ` · ${t('trends.scoreDelta')} ${Number(summary.score_delta).toFixed(2)}` : ''}
            </p>
          ) : null}
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
        <h3>{t('trends.byCameraTitle')}</h3>
        <p className="muted">{t('trends.byCameraHint')}</p>
        {!byCamera.length ? (
          <p className="muted">{t('trends.noCameraDrift')}</p>
        ) : (
          <div className="table">
            {byCamera.map((cam) => (
              <div key={cam.camera_id} className="row">
                <span><strong>{cam.camera_id}</strong></span>
                <span>{t('trends.cameraSamples')}: {cam.sample_count ?? cam.window_size ?? 0}</span>
                <span>{t('trends.baseline')}: {Number(cam.baseline_avg_score ?? 0).toFixed(2)}</span>
                <span>{t('trends.scoreDelta')}: {Number(cam.score_delta ?? 0).toFixed(2)}</span>
                <span>{t('trends.driftScore')}: {Number(cam.drift_score ?? 0).toFixed(2)}</span>
                <StatusBadge state={cam.severity || cam.trend_severity || 'green'}>
                  {cam.drift_warning || cam.trend_warning
                    ? (cam.reason || cam.trend_reason || cam.severity || 'drift')
                    : 'ok'}
                </StatusBadge>
              </div>
            ))}
          </div>
        )}
      </article>

      <article className="card">
        <h3>{t('trends.pointsTitle')}</h3>
        <div className="table">
          {latest.map((i) => (
            <div key={i.id} className="row">
              <span>{new Date(i.timestamp).toLocaleTimeString()}</span>
              <span>{i.id}</span>
              <span>{i.viewCount > 1 ? `${i.viewCount} cam` : (i.cameraIds?.[0] || '')}</span>
              <span>{i.score}</span>
              <StatusBadge state={i.decision}>{t(`decision.${i.decision}`)}</StatusBadge>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
