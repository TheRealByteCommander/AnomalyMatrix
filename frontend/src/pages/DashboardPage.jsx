import { useMemo, useState, useEffect } from 'react';
import { hmiState } from '../data/sampleData';
import { runInspection, fetchRecentInspections, fetchObservabilitySummary } from '../services';
import StatusBadge from '../components/StatusBadge';
import ContextHelp from '../components/ContextHelp';
import { useI18n } from '../i18n/I18nProvider';
import { SCREEN_IDS } from '../i18n/screens';

export default function DashboardPage({ inspections, setInspections, setSelectedInspectionId, goTo, openHelp }) {
  const { t, locale } = useI18n();
  const [runState, setRunState] = useState('idle');
  const [notice, setNotice] = useState(() => t('dashboard.ready'));
  const [kpis, setKpis] = useState(hmiState.kpis);

  useEffect(() => {
    if (runState === 'idle') setNotice(t('dashboard.ready'));
  }, [locale, t, runState]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const summary = await fetchObservabilitySummary();
        if (!cancelled) {
          setKpis({
            cycleMsP95: summary.inference_p95_ms || hmiState.kpis.cycleMsP95,
            anomalyRate: summary.inspection_count
              ? ((summary.anomaly_count / summary.inspection_count) * 100).toFixed(1)
              : hmiState.kpis.anomalyRate,
            queueLagMs: hmiState.kpis.queueLagMs,
            opcUaPublishErrorRate: summary.opc_ua_publish_error_rate_pct ?? hmiState.kpis.opcUaPublishErrorRate,
          });
        }
      } catch {
        // keep seed KPIs when API unavailable
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [inspections.length]);

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

  const stateClass = runState === 'error' ? 'state-red' : runState === 'running' ? 'state-amber' : runState === 'success' ? 'state-green' : 'state-amber';

  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">{t('dashboard.eyebrow')}</p>
          <h2>{hmiState.line}</h2>
          <p className="muted">{t('common.recipe')} {hmiState.recipe} · {t('common.model')} {hmiState.modelVersion}</p>
          <ContextHelp articleId="dashboard-overview" onOpen={openHelp} />
        </div>
        <StatusBadge state={hmiState.status}>{t('dashboard.statusTrendWarning')}</StatusBadge>
      </article>

      <article className="card run-panel">
        <div>
          <h3>{t('dashboard.actionTitle')}</h3>
          <p className="muted">{t('dashboard.actionHint')}</p>
        </div>
        <div className="run-actions">
          <button type="button" className="tab active" onClick={handleRunInspection} disabled={runState === 'running'}>
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
              <span>{i.part}</span>
              <StatusBadge state={i.decision}>{t(`decision.${i.decision}`)}</StatusBadge>
            </button>
          ))}
        </div>
      </article>
    </section>
  );
}
