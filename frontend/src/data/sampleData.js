export const hmiState = {
  line: 'Line-A / Cell-03',
  recipe: 'Seam_Adhesive_V12',
  modelVersion: 'patchcore-1.4.2',
  status: 'amber',
  statusText: 'Trend warning active',
  kpis: {
    cycleMsP95: 428,
    anomalyRate: 1.8,
    queueLagMs: 94,
    opcUaPublishErrorRate: 0.2,
  },
};

export const inspections = [
  { id: 'INSP-44210', part: 'RotorHousing', score: 0.13, decision: 'green', defect: 'none', ts: '15:42:11' },
  { id: 'INSP-44209', part: 'RotorHousing', score: 0.67, decision: 'amber', defect: 'edge burr', ts: '15:42:01' },
  { id: 'INSP-44208', part: 'RotorHousing', score: 0.91, decision: 'red', defect: 'seam void', ts: '15:41:52' },
];

export const trends = [
  { metric: 'Anomaly score rolling mean', now: 0.41, threshold: 0.55, state: 'amber' },
  { metric: 'Inference p95 (ms)', now: 182, threshold: 250, state: 'green' },
  { metric: 'False warning ratio', now: 2.9, threshold: 2.5, state: 'red' },
];

export const configSummary = {
  opcUaProfile: 'sign+encrypt',
  recipeVersion: '12',
  modelProfile: 'PatchCore default',
  auditMode: 'immutable',
};
