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
  { id: 'INSP-44210', part: 'RotorHousing', score: 0.13, decision: 'green', defect: 'none', timestamp: new Date().toISOString() },
  { id: 'INSP-44209', part: 'RotorHousing', score: 0.67, decision: 'amber', defect: 'edge burr', timestamp: new Date(Date.now()-60_000).toISOString() },
  { id: 'INSP-44208', part: 'RotorHousing', score: 0.91, decision: 'red', defect: 'seam void', timestamp: new Date(Date.now()-120_000).toISOString() },
];

export const configSummary = {
  opcUaProfile: 'sign+encrypt',
  recipeVersion: '12',
  modelProfile: 'PatchCore default',
  auditMode: 'immutable',
};
