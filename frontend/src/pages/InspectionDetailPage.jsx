import { useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import { submitFeedback } from '../services';

const VERDICTS = [
  { value: 'confirm_anomaly', label: 'Anomalie bestätigen' },
  { value: 'false_positive', label: 'Falsch positiv' },
  { value: 'needs_review', label: 'Nachprüfung nötig' },
];

export default function InspectionDetailPage({ selectedInspection }) {
  const [verdict, setVerdict] = useState('needs_review');
  const [comment, setComment] = useState('');
  const [feedbackStatus, setFeedbackStatus] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (!selectedInspection) {
    return (
      <section className="page-grid">
        <article className="card">
          <h2>No inspection selected</h2>
          <p className="muted">Run pipeline from Dashboard to generate first inspection.</p>
        </article>
      </section>
    );
  }

  const passFail = selectedInspection.decision === 'red' ? 'Fail' : selectedInspection.decision === 'amber' ? 'Review' : 'Pass';

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
      setFeedbackStatus({ ok: true, message: 'Feedback gespeichert.' });
      setComment('');
    } catch (err) {
      setFeedbackStatus({ ok: false, message: err.message || 'Feedback fehlgeschlagen.' });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">Inspection Detail</p>
          <h2>{selectedInspection.id}</h2>
          <p className="muted">Part: {selectedInspection.part} · {new Date(selectedInspection.timestamp).toLocaleString()}</p>
        </div>
        <StatusBadge state={selectedInspection.decision}>{passFail}</StatusBadge>
      </article>

      <article className="card detail-grid">
        <div>
          <h3>Anomaly score</h3>
          <p className="score-big">{selectedInspection.score}</p>
          <p className="muted">Defect label: {selectedInspection.defect}</p>
          <p className="muted">Decision: <StatusBadge state={selectedInspection.decision}>{selectedInspection.decision}</StatusBadge></p>
        </div>
        <div>
          <h3>Heatmap (placeholder)</h3>
          <div className="heatmap-placeholder" role="img" aria-label="Synthetic anomaly heatmap placeholder">
            <span>{selectedInspection.heatmapUri || 'Heatmap Preview Placeholder'}</span>
          </div>
          <p className="muted">Phase 2: wired placeholder for vertical flow; real overlay comes in model integration phase.</p>
        </div>
      </article>

      <article className="card">
        <h3>QA-Feedback</h3>
        <p className="muted">Verdict an Backend senden (QA Lead / Admin).</p>
        <form className="feedback-form" onSubmit={handleFeedbackSubmit}>
          <label htmlFor="feedback-verdict">Verdict</label>
          <select id="feedback-verdict" value={verdict} onChange={(e) => setVerdict(e.target.value)}>
            {VERDICTS.map((v) => (
              <option key={v.value} value={v.value}>{v.label}</option>
            ))}
          </select>
          <label htmlFor="feedback-comment">Kommentar</label>
          <textarea
            id="feedback-comment"
            rows={3}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Optional"
          />
          <button type="submit" disabled={submitting}>{submitting ? 'Sende…' : 'Feedback senden'}</button>
        </form>
        {feedbackStatus && (
          <p className={feedbackStatus.ok ? 'muted' : 'error-text'} role="status">{feedbackStatus.message}</p>
        )}
      </article>
    </section>
  );
}
