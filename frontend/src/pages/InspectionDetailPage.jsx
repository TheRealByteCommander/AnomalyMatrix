import StatusBadge from '../components/StatusBadge';

export default function InspectionDetailPage({ selectedInspection }) {
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
    </section>
  );
}
