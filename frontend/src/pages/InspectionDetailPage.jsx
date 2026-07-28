import { useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import ContextHelp from '../components/ContextHelp';
import { submitFeedback } from '../services';
import { useI18n } from '../i18n/I18nProvider';

const VERDICT_KEYS = ['confirm_anomaly', 'false_positive', 'needs_review'];

export default function InspectionDetailPage({ selectedInspection, openHelp }) {
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

  const passFail =
    selectedInspection.decision === 'red'
      ? t('decision.fail')
      : selectedInspection.decision === 'amber'
        ? t('decision.review')
        : t('decision.pass');

  async function handleFeedbackSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setFeedbackStatus(null);
    try {
      await submitFeedback({
        inspectionId: selectedInspection.id,
        verdict,
        comment,
      });
      setFeedbackStatus({ ok: true, message: t('inspectionDetail.saved') });
      setComment('');
    } catch (err) {
      setFeedbackStatus({ ok: false, message: err.message || t('inspectionDetail.failed') });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">{t('inspectionDetail.eyebrow')}</p>
          <h2>{selectedInspection.id}</h2>
          <p className="muted">
            {t('inspectionDetail.part')}: {selectedInspection.part} · {new Date(selectedInspection.timestamp).toLocaleString()}
          </p>
          <ContextHelp articleId="inspection-detail" onOpen={openHelp} />
        </div>
        <StatusBadge state={selectedInspection.decision}>{passFail}</StatusBadge>
      </article>

      <article className="card detail-grid">
        <div>
          <h3>{t('inspectionDetail.scoreTitle')}</h3>
          <p className="score-big">{selectedInspection.score}</p>
          <p className="muted">{t('inspectionDetail.defectLabel')}: {selectedInspection.defect}</p>
          <p className="muted">
            {t('inspectionDetail.decisionLabel')}:{' '}
            <StatusBadge state={selectedInspection.decision}>{t(`decision.${selectedInspection.decision}`)}</StatusBadge>
          </p>
        </div>
        <div>
          <h3>{t('inspectionDetail.heatmapTitle')}</h3>
          {selectedInspection.heatmapUri &&
          (selectedInspection.heatmapUri.startsWith('/') ||
            selectedInspection.heatmapUri.startsWith('http')) ? (
            <img
              className="heatmap-image"
              src={selectedInspection.heatmapUri}
              alt={t('inspectionDetail.heatmapAria')}
            />
          ) : (
            <div className="heatmap-placeholder" role="img" aria-label={t('inspectionDetail.heatmapAria')}>
              <span>{selectedInspection.heatmapUri || t('inspectionDetail.heatmapPlaceholder')}</span>
            </div>
          )}
          <p className="muted">{t('inspectionDetail.heatmapHint')}</p>
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
