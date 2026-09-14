import { useMemo, useState, useEffect } from 'react';
import { hmiState } from '../data/sampleData';
import { resolveRecipeSelection } from '../recipeSelection';
import { canShowHeatmapImage, formatAnomalyScore } from '../heatmapDisplay';
import { runInspection, fetchRecentInspections, fetchObservabilitySummary, fetchRecipes, fetchModels, fetchTrendSummary, fetchCameras, fetchWatchdog } from '../services';
import StatusBadge from '../components/StatusBadge';
import ContextHelp from '../components/ContextHelp';
import { useI18n } from '../i18n/I18nProvider';
import { SCREEN_IDS } from '../i18n/screens';

export default function DashboardPage({
  inspections,
  setInspections,
  setSelectedInspectionId,
  goTo,
  openHelp,
  selectedRecipeId,
  setSelectedRecipeId = () => {},
}) {
  const { t, locale } = useI18n();
  const [runState, setRunState] = useState('idle');
  const [notice, setNotice] = useState(() => t('dashboard.ready'));
  const [showMore, setShowMore] = useState(false);
  const [kpis, setKpis] = useState(hmiState.kpis);
  const [context, setContext] = useState({
    line: hmiState.line,
    recipe: hmiState.recipe,
    modelVersion: hmiState.modelVersion,
    memoryBankLoaded: false,
    memoryBankKnown: false,
  });
  const [trendStatus, setTrendStatus] = useState({
    warning: true,
    severity: hmiState.status,
  });
  const [cameras, setCameras] = useState([]);
  const [watchdog, setWatchdog] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const recipeId = resolveRecipeSelection(recipes, selectedRecipeId) || selectedRecipeId || 'recipe-default';

  useEffect(() => {
    if (runState === 'idle') setNotice(t('dashboard.ready'));
  }, [locale, t, runState]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [summary, recipeData, modelData, trend, cameraData, wd] = await Promise.all([
          fetchObservabilitySummary(),
          fetchRecipes().catch(() => ({ items: [] })),
          fetchModels().catch(() => ({ items: [] })),
          fetchTrendSummary().catch(() => null),
          fetchCameras().catch(() => ({ cameras: [] })),
          fetchWatchdog().catch(() => null),
        ]);
        if (cancelled) return;

        const recipeItems = recipeData.items || [];
        const activeRecipe =
          recipeItems.find((r) => r.active === true || r.status === 'active') || recipeItems[0];
          const items = modelData.items || [];
          const activeModel = items.find((m) => m.status === 'active') || modelData.active || items[0];
        const latestCameras = inspections[0]?.cameraIds || [];
        const latestCamera = latestCameras[0] || inspections[0]?.raw?.frame?.camera_id;

        setRecipes(recipeItems);
        if (recipeItems.length) {
          setSelectedRecipeId((prev) => resolveRecipeSelection(recipeItems, prev));
        }

        setContext({
          line: latestCameras.length > 1
            ? `Cameras ${latestCameras.join('+')}`
            : latestCamera
              ? `Camera ${latestCamera}`
              : activeRecipe?.name || hmiState.line,
          recipe: activeRecipe?.recipe_id || activeRecipe?.name || hmiState.recipe,
          modelVersion: activeModel?.model_version || activeModel?.name || hmiState.modelVersion,
          memoryBankLoaded: Boolean(modelData.memory_bank?.loaded),
          memoryBankKnown: modelData.memory_bank != null,
        });

        setCameras(cameraData.cameras || []);
        setWatchdog(wd);

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
  }, [inspections.length, inspections[0]?.id, setSelectedRecipeId]);

  const anomalyRate = useMemo(() => {
    if (!inspections.length) return 0;
    const bad = inspections.filter((x) => x.decision !== 'green').length;
    return ((bad / inspections.length) * 100).toFixed(1);
  }, [inspections]);

  async function handleRunInspection() {
    setRunState('running');
    setNotice(t('dashboard.noticeRunning'));
    try {
      const selectedCameraIds = cameras.filter((cam) => cam.selected).map((cam) => cam.camera_id);
      const result = await runInspection(
        null,
        recipeId,
        selectedCameraIds.length ? selectedCameraIds : null
      );
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

  const latest = inspections[0] || null;
  const decision = latest?.decision || 'idle';
  const needsQa = decision === 'red' || decision === 'amber';
  const statusLabel = trendStatus.warning
    ? t(`dashboard.statusTrend.${trendStatus.severity}`)
    : t('dashboard.statusOk');
  const camerasOnline = cameras.filter((cam) => cam.available !== false).length;
  const recipeLabel = recipes.find((r) => r.recipe_id === recipeId)?.name || recipeId;

  return (
    <section className="home-page">
      <article className={`home-hero decision-${decision}`}>
        <p className="eyebrow">{t('dashboard.lastInspection')}</p>
        <p className="home-decision" data-testid="home-decision">
          {latest ? t(`decision.${decision}`) : t('dashboard.idleDecision')}
        </p>
        <p className="home-score" data-testid="home-score">
          {latest ? formatAnomalyScore(latest.score) : '—'}
        </p>
        <p className="muted home-meta">
          {latest ? latest.id : t('dashboard.noResult')}
          {latest?.epc ? ` · EPC ${latest.epc}` : ''}
          {` · ${t('common.model')} ${context.modelVersion}`}
        </p>
        <StatusBadge state={trendStatus.warning ? trendStatus.severity : 'green'}>{statusLabel}</StatusBadge>
        <ContextHelp articleId="dashboard-overview" onOpen={openHelp} />
      </article>

      <div className="home-main">
        {canShowHeatmapImage(latest) ? (
          <button
            type="button"
            className="home-heatmap"
            onClick={() => goTo(SCREEN_IDS.inspectionDetail)}
            aria-label={t('inspectionDetail.heatmapAria')}
          >
            <img src={latest.heatmapUri} alt={t('inspectionDetail.heatmapAria')} />
          </button>
        ) : (
          <div className="home-heatmap home-heatmap-empty">
            <span className="muted">{t('inspectionDetail.heatmapPlaceholder')}</span>
          </div>
        )}

        <div className="home-controls">
          {recipes.length ? (
            <label className="recipe-select-label">
              {t('common.recipe')}
              <select
                value={recipeId}
                onChange={(e) => setSelectedRecipeId(e.target.value)}
                data-testid="dashboard-recipe"
              >
                {recipes.map((recipe) => (
                  <option key={recipe.recipe_id} value={recipe.recipe_id}>
                    {recipe.name || recipe.recipe_id}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <p className="muted">{recipeLabel}</p>
          )}

          <button
            type="button"
            className="primary home-run"
            data-testid="dashboard-run"
            onClick={handleRunInspection}
            disabled={runState === 'running'}
          >
            {runState === 'running' ? t('dashboard.running') : t('dashboard.run')}
          </button>

          <p className="muted home-notice" role="status">{notice}</p>

          <div className="home-secondary">
            <button type="button" className="tab" data-testid="dashboard-open-detail" onClick={() => goTo(SCREEN_IDS.inspectionDetail)}>
              {needsQa ? t('dashboard.qaNeeded') : t('dashboard.openDetail')}
            </button>
            <button type="button" className="tab" data-testid="dashboard-training" onClick={() => goTo(SCREEN_IDS.training)}>
              {t('nav.training')}
            </button>
            <a
              className="tab"
              href="/heatmap"
              target="amx-heatmap-display"
              rel="noopener noreferrer"
              data-testid="dashboard-heatmap-display"
            >
              {t('heatmapDisplay.openMonitor')}
            </a>
          </div>
        </div>
      </div>

      <div className="home-status-row">
        {watchdog ? (
          <div data-testid="endurance-watchdog">
            <span className="muted">{t('storage.watchdog')}</span>
            <StatusBadge state={watchdog.gap_detected ? 'amber' : 'green'}>{watchdog.status}</StatusBadge>
          </div>
        ) : null}
        <div>
          <span className="muted">{t('dashboard.camerasTitle')}</span>
          <strong>{cameras.length ? `${camerasOnline}/${cameras.length}` : '—'}</strong>
        </div>
        <button type="button" className="text-btn" onClick={() => setShowMore((v) => !v)}>
          {showMore ? t('dashboard.less') : t('dashboard.more')}
        </button>
      </div>

      {showMore ? (
        <article className="home-more">
          <div className="kpi-grid">
            <div><label>{t('dashboard.kpiCycle')}</label><strong>{kpis.cycleMsP95} ms</strong></div>
            <div><label>{t('dashboard.kpiAnomalyRate')}</label><strong>{anomalyRate}%</strong></div>
            <div><label>{t('dashboard.kpiQueueLag')}</label><strong>{kpis.queueLagMs} ms</strong></div>
            <div><label>{t('dashboard.kpiOpcError')}</label><strong>{kpis.opcUaPublishErrorRate}%</strong></div>
          </div>
          {cameras.length ? (
            <ul className="camera-select-list">
              {cameras.map((cam) => (
                <li key={cam.camera_id}>
                  <strong>{cam.label || cam.camera_id}</strong>
                  {' '}
                  <StatusBadge state={cam.available === false ? 'red' : 'green'}>
                    {cam.available === false ? t('configuration.camerasOffline') : t('configuration.camerasOnline')}
                  </StatusBadge>
                </li>
              ))}
            </ul>
          ) : null}
          {inspections.length ? (
            <div className="simple-list">
              {inspections.slice(0, 5).map((i) => (
                <button
                  key={i.id}
                  type="button"
                  className="simple-row"
                  onClick={() => {
                    setSelectedInspectionId(i.id);
                    goTo(SCREEN_IDS.inspectionDetail);
                  }}
                >
                  <span>{new Date(i.timestamp).toLocaleTimeString()}</span>
                  <span className="muted">{i.id}</span>
                  <StatusBadge state={i.decision}>{t(`decision.${i.decision}`)}</StatusBadge>
                </button>
              ))}
            </div>
          ) : null}
        </article>
      ) : null}
    </section>
  );
}
