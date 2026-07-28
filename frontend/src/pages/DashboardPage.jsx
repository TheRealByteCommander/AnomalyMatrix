import { useMemo, useState, useEffect } from 'react';
import { hmiState } from '../data/sampleData';
import { runInspection, fetchRecentInspections, fetchObservabilitySummary, fetchRecipes, fetchModels, fetchTrendSummary } from '../services';
import StatusBadge from '../components/StatusBadge';
import ContextHelp from '../components/ContextHelp';
import { useI18n } from '../i18n/I18nProvider';
import { SCREEN_IDS } from '../i18n/screens';

export default function DashboardPage({ inspections, setInspections, setSelectedInspectionId, goTo, openHelp }) {
  const { t, locale } = useI18n();
  const [runState, setRunState] = useState('idle');
  const [notice, setNotice] = useState(() => t('dashboard.ready'));
  const [kpis, setKpis] = useState(hmiState.kpis);
  const [context, setContext] = useState({
    line: hmiState.line,
    recipe: hmiState.recipe,
    modelVersion: hmiState.modelVersion,
  });
  const [trendStatus, setTrendStatus] = useState({
    warning: true,
    severity: hmiState.status,
  });

  useEffect(() => {
    if (runState === 'idle') setNotice(t('dashboard.ready'));
  }, [locale, t, runState]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [summary, recipeData, modelData, trend] = await Promise.all([
          fetchObservabilitySummary(),
          fetchRecipes().catch(() => ({ items: [] })),
          fetchModels().catch(() => ({ items: [] })),
          fetchTrendSummary().catch(() => null),
        ]);
        if (cancelled) return;

        const activeRecipe = (recipeData.items || []).find((r) => r.status === 'active') || recipeData.items?.[0];
        const activeModel = (modelData.items || []).find((m) => m.status === 'active') || modelData.items?.[0];
        const latestCameras = inspections[0]?.cameraIds || [];
        const latestCamera = latestCameras[0] || inspections[0]?.raw?.frame?.camera_id;

        setContext({
          line: latestCameras.length > 1
            ? `Cameras ${latestCameras.join('+')}`
            : latestCamera
              ? `Camera ${latestCamera}`
              : activeRecipe?.name || hmiState.line,
          recipe: activeRecipe?.recipe_id || activeRecipe?.name || hmiState.recipe,
          modelVersion: activeModel?.model_version || activeModel?.name || hmiState.modelVersion,
        });

        setKpis({
          cycleMsP95: summary.inference_latency_mean_ms || summary.inference_p95_ms || hmiState.kpis.cycleMsP95,
          anomalyRate: summary.inspection_count
            ? ((summary.anomaly_count / summary.inspection_count) * 100).toFixed(1)
            : hmiState.kpis.anomalyRate,
          queueLagMs: hmiState.kpis.queueLagMs,
          opcUaPublishErrorRate: summary.opc_ua_publish_error_rate_pct ?? hmiState.kpis.opcUaPublishErrorRate,
        });

        const severity = trend?.trend_severity || summary.trend_severity || 'green';
        setTrendStatus({
          warning: Boolean(trend?.trend_warning ?? summary.trend_warning),
          severity,
        });
      } catch {
        // keep seed KPIs when API unavailable
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [inspections.length, inspections[0]?.id]);

  const anomalyRate = useMemo(() => {
    if (!inspections.length) return 0;
    const bad = inspections.filter((x) => x.decision !== 'green').length;
    return ((bad / inspections.length) * 100).toFixed(1);
  }, [inspections]);

  async function handleRunInspection() {
    setRunState('running');
    setNotice(t('dashboard.noticeRunning'));
    try {
      const result = await runInspection();
      const merged = [result, ...inspections.filter((i) => i.id !== result.id)].slice(0, 20);
      setInspections(merged);
      setSelectedInspectionId(result.id);
      setRunState('success');
      setNotice(
        t('dashboard.noticeComplete', {
          id: result.id,
          decision: t(`decision.${result.decision}`).toUpperCase(),
        })
      );
      setTimeout(() => setRunState('idle'), 1500);
    } catch {
      try {
        const latest = await fetchRecentInspections();
        if (latest.length) {
          setInspections(latest);
          setSelectedInspectionId(latest[0].id);
          setRunState('success');
          setNotice(t('dashboard.noticeLoaded', { id: latest[0].id }));
          setTimeout(() => setRunState('idle'), 1500);
          return;
        }
      } catch {
        // ignore nested errors
      }
      setRunState('error');
      setNotice(t('dashboard.noticeFailed'));
    }
  }

  const statusLabel = trendStatus.warning
    ? t(`dashboard.statusTrend.${trendStatus.severity}`)
    : t('dashboard.statusOk');

  const stateClass = runState === 'error' ? 'state-red' : runState === 'running' ? 'state-amber' : runState === 'success' ? 'state-green' : 'state-amber';

  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">{t('dashboard.eyebrow')}</p>
          <h2>{context.line}</h2>
          <p className="muted">{t('common.recipe')} {context.recipe} · {t('common.model')} {context.modelVersion}</p>
          <ContextHelp articleId="dashboard-overview" onOpen={openHelp} />
        </div>
        <StatusBadge state={trendStatus.warning ? trendStatus.severity : 'green'}>{statusLabel}</StatusBadge>
      </article>

      <article className="card run-panel">
        <div>
          <h3>{t('dashboard.actionTitle')}</h3>
          <p className="muted">{t('dashboard.actionHint')}</p>
        </div>
        <div className="run-actions">
          <button type="button" className="tab active" data-testid="dashboard-run" onClick={handleRunInspection} disabled={runState === 'running'}>
            {runState === 'running' ? t('dashboard.running') : t('dashboard.run')}
          </button>
          <button type="button" className="tab" onClick={() => goTo(SCREEN_IDS.inspectionDetail)}>
            {t('dashboard.openDetail')}
          </button>
          <StatusBadge state={stateClass.replace('state-', '')}>{notice}</StatusBadge>
        </div>
      </article>

      <article className="card kpi-grid">
        <div><label>{t('dashboard.kpiCycle')}</label><strong>{kpis.cycleMsP95} ms</strong></div>
        <div><label>{t('dashboard.kpiAnomalyRate')}</label><strong>{anomalyRate}%</strong></div>
        <div><label>{t('dashboard.kpiQueueLag')}</label><strong>{kpis.queueLagMs} ms</strong></div>
        <div><label>{t('dashboard.kpiOpcError')}</label><strong>{kpis.opcUaPublishErrorRate}%</strong></div>
      </article>

      <article className="card">
        <h3>{t('dashboard.latestTitle')}</h3>
        <div className="table">
          {inspections.map((i) => (
            <button
              key={i.id}
              type="button"
              className="row row-btn"
              onClick={() => {
                setSelectedInspectionId(i.id);
                goTo(SCREEN_IDS.inspectionDetail);
              }}
            >
              <span>{new Date(i.timestamp).toLocaleTimeString()}</span>
              <span>{i.id}</span>
              <span>
                {i.viewCount > 1
                  ? `${i.viewCount}×cam`
                  : (i.cameraIds?.[0] || i.part)}
              </span>
              <StatusBadge state={i.decision}>{t(`decision.${i.decision}`)}</StatusBadge>
            </button>
          ))}
        </div>
      </article>
    </section>
  );
}
