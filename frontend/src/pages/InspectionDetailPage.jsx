import { useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import ContextHelp from '../components/ContextHelp';
import { isRenderableHeatmap, mapApiInspection, submitFeedback } from '../services';
import { useI18n } from '../i18n/I18nProvider';

const VERDICT_KEYS = ['confirm_anomaly', 'false_positive', 'needs_review'];

function HeatmapBlock({ uri, placeholder, kind, t, aria, fallback }) {
  const real = isRenderableHeatmap(uri) && !placeholder;
  const modelBased = kind === 'patchcore' || kind === 'legacy_spatial';
  const hint = !real
    ? t('inspectionDetail.heatmapHintPlaceholder')
    : modelBased
      ? t('inspectionDetail.heatmapHint')
      : t('inspectionDetail.heatmapHintResidual');
  return (
    <>
      {real ? (
        <img className="heatmap-image" src={uri} alt={aria} />
      ) : (
        <div className="heatmap-placeholder" role="img" aria-label={aria}>
          <span>{fallback}</span>
        </div>
      )}
      <p className="muted">{hint}</p>
      {real && kind === 'legacy_spatial' ? (
        <p className="muted">{t('inspectionDetail.heatmapHintRetrain')}</p>
      ) : null}
    </>
  );
}

export default function InspectionDetailPage({ selectedInspection, setInspections, openHelp }) {
  const { t } = useI18n();
  const [verdict, setVerdict] = useState('needs_review');
  const [comment, setComment] = useState('');
  const [feedbackStatus, setFeedbackStatus] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (!selectedInspection) {
    return (
      <section className="page-grid">
        <article className="card">
          <h2>{t('inspectionDetail.emptyTitle')}</h2>
          <p className="muted">{t('inspectionDetail.emptyHint')}</p>
        </article>
      </section>
    );
  }

  const displayDecision = selectedInspection.decision;
  const passFail = t(`decision.${displayDecision === 'red' ? 'fail' : displayDecision === 'amber' ? 'review' : 'pass'}`);
  const qaNio = selectedInspection.qaOverride === 'nio' || selectedInspection.qaVerdict === 'confirm_anomaly';

  async function handleFeedbackSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setFeedbackStatus(null);
    try {
      const result = await submitFeedback({
        inspectionId: selectedInspection.id,
        verdict,
        comment,
        recipeVersion: selectedInspection.raw?.frame?.recipe_id ? 'v1' : 'v1',
        modelVersion: selectedInspection.modelVersion || 'v0',
      });
      if (result?.inspection && setInspections) {
        const mapped = mapApiInspection(result.inspection);
        setInspections((prev) => {
          const rest = prev.filter((item) => item.id !== mapped.id);
          return [mapped, ...rest];
        });
      }
      const extra =
        verdict === 'confirm_anomaly' && result?.nio_sample
          ? ` ${t('inspectionDetail.nioStored')}`
          : '';
      setFeedbackStatus({ ok: true, message: `${t('inspectionDetail.saved')}${extra}` });
      setComment('');
    } catch (err) {
      setFeedbackStatus({ ok: false, message: err.message || t('inspectionDetail.failed') });
    } finally {
      setSubmitting(false);
    }
  }

  const thresholds = selectedInspection.thresholds || {};

  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">{t('inspectionDetail.eyebrow')}</p>
          <h2>{selectedInspection.id}</h2>
          <p className="muted">
            {t('inspectionDetail.part')}: {selectedInspection.part} · {new Date(selectedInspection.timestamp).toLocaleString()}
            {selectedInspection.epc ? ` · EPC ${selectedInspection.epc}` : ''}
            {selectedInspection.processId ? ` · ${t('inspectionDetail.processId')} ${selectedInspection.processId}` : ''}
          </p>
          <ContextHelp articleId="inspection-detail" onOpen={openHelp} />
        </div>
        <StatusBadge state={displayDecision}>{passFail}</StatusBadge>
      </article>

      {qaNio ? (
        <article className="card" data-testid="qa-nio-banner">
          <p className="ok">{t('inspectionDetail.qaOverrideNio')}</p>
          <p className="muted">
            {t('inspectionDetail.qaAutoDecision', {
              decision: t(`decision.${selectedInspection.autoDecision || 'green'}`),
            })}
            {selectedInspection.qaActor ? ` · ${selectedInspection.qaActor}` : ''}
          </p>
        </article>
      ) : null}

      <article className="card detail-grid">
        <div>
          <h3>{t('inspectionDetail.scoreTitle')}</h3>
          <p className="score-big">{selectedInspection.score}</p>
          <p className="muted">{t('inspectionDetail.defectLabel')}: {selectedInspection.defect}</p>
          <p className="muted">
            {t('inspectionDetail.decisionLabel')}:{' '}
            <StatusBadge state={displayDecision}>{t(`decision.${displayDecision}`)}</StatusBadge>
          </p>
          <p className="muted">
            {t('inspectionDetail.modelVersion')}: {selectedInspection.modelVersion || '—'}
          </p>
          {selectedInspection.epc ? (
            <p className="muted" data-testid="inspection-epc">EPC: {selectedInspection.epc}</p>
          ) : null}
          {selectedInspection.memoryBankKnown ? (
            <p className="muted">
              {t('inspectionDetail.memoryBank')}:{' '}
              {selectedInspection.memoryBankLoaded ? t('training.bankLoaded') : t('training.bankFallback')}
            </p>
          ) : null}
          {thresholds.amber != null && thresholds.red != null ? (
            <p className="muted">
              {t('inspectionDetail.thresholdsUsed')}: {thresholds.amber} / {thresholds.red}
            </p>
          ) : null}
        </div>
        <div>
          <h3>{t('inspectionDetail.heatmapTitle')}</h3>
          <HeatmapBlock
            uri={selectedInspection.heatmapUri}
            placeholder={selectedInspection.heatmapPlaceholder}
            kind={selectedInspection.heatmapKind}
            t={t}
            aria={t('inspectionDetail.heatmapAria')}
            fallback={selectedInspection.heatmapUri || t('inspectionDetail.heatmapPlaceholder')}
          />
        </div>
      </article>

      {selectedInspection.viewCount > 1 && (
        <article className="card">
          <h3>{t('inspectionDetail.viewsTitle')}</h3>
          <p className="muted">
            {t('inspectionDetail.viewsHint', { count: selectedInspection.viewCount })}
          </p>
          <div className="kpi-grid">
            {(selectedInspection.views || []).map((view) => (
              <div key={view.cameraId}>
                <label>{view.cameraId}</label>
                <strong>{view.score}</strong>
                <StatusBadge state={view.decision}>{t(`decision.${view.decision}`)}</StatusBadge>
                {isRenderableHeatmap(view.heatmapUri) && !view.heatmapPlaceholder ? (
                  <img
                    className="heatmap-image"
                    src={view.heatmapUri}
                    alt={`${t('inspectionDetail.viewsHeatmap')} ${view.cameraId}`}
                  />
                ) : null}
              </div>
            ))}
          </div>
        </article>
      )}

      <article className="card">
        <h3>{t('inspectionDetail.feedbackTitle')}</h3>
        <p className="muted">{t('inspectionDetail.feedbackHint')}</p>
        <form className="feedback-form" onSubmit={handleFeedbackSubmit}>
          <label htmlFor="feedback-verdict">{t('inspectionDetail.verdictLabel')}</label>
          <select id="feedback-verdict" value={verdict} onChange={(e) => setVerdict(e.target.value)}>
            {VERDICT_KEYS.map((key) => (
              <option key={key} value={key}>{t(`inspectionDetail.verdicts.${key}`)}</option>
            ))}
          </select>
          <label htmlFor="feedback-comment">{t('inspectionDetail.commentLabel')}</label>
          <textarea
            id="feedback-comment"
            rows={3}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={t('common.optional')}
          />
          <button type="submit" disabled={submitting}>
            {submitting ? t('inspectionDetail.submitting') : t('inspectionDetail.submit')}
          </button>
        </form>
        {feedbackStatus && (
          <p className={feedbackStatus.ok ? 'muted' : 'error-text'} role="status">{feedbackStatus.message}</p>
        )}
      </article>
    </section>
  );
}
