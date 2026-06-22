const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8080/api/v1';

async function parseEnvelope(response) {
  if (!response.ok) {
    throw new Error(`API error (${response.status})`);
  }
  const body = await response.json();
  if (!body.ok) {
    throw new Error(body.error?.message || 'API request failed');
  }
  return body.data;
}

/** Map backend inspection DTO to HMI view model (Phase 2/3 contract). */
export function mapApiInspection(item) {
  const frame = item.frame || {};
  const inf = item.inference || {};
  const score = Number(inf.anomaly_score ?? 0);
  const decision =
    item.decision ||
    (score >= 0.85 ? 'red' : score >= 0.55 ? 'amber' : 'green');

  return {
    id: item.inspection_id || item.id,
    part: frame.recipe_id || frame.camera_id || 'unknown',
    score,
    decision,
    defect: inf.status === 'anomaly' ? inf.defect_class || 'anomaly detected' : 'none',
    timestamp: frame.captured_at || new Date().toISOString(),
    heatmapUri: item.heatmap?.uri || inf.heatmap_uri || null,
    raw: item,
  };
}

export async function runInspection(cameraId = 'cam-01', recipeId = 'recipe-default') {
  const r = await fetch(`${API_BASE}/inspections/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ camera_id: cameraId, recipe_id: recipeId }),
  });
  return mapApiInspection(await parseEnvelope(r));
}

export async function fetchRecentInspections(limit = 20) {
  const r = await fetch(`${API_BASE}/inspections/recent?limit=${limit}`);
  const data = await parseEnvelope(r);
  return (data.items || []).map(mapApiInspection);
}

export async function fetchTrendSummary() {
  const r = await fetch(`${API_BASE}/results/trend-summary`);
  return parseEnvelope(r);
}

export async function fetchLicenseStatus() {
  const r = await fetch(`${API_BASE}/license/status`);
  return parseEnvelope(r);
}

export async function fetchObservabilitySummary() {
  const r = await fetch(`${API_BASE}/observability/summary`);
  return parseEnvelope(r);
}
