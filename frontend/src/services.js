const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8080/api/v1';
const TOKEN_KEY = 'amx_access_token';

const defaultHeaders = {
  'X-AMX-Role': import.meta.env.VITE_AMX_ROLE || 'operator',
  'X-AMX-User': import.meta.env.VITE_AMX_USER || 'hmi-operator',
};

export function getStoredToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || '';
  } catch {
    return '';
  }
}

export function setStoredToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore storage errors
  }
}

function withHeaders(extra = {}) {
  const token = getStoredToken();
  const auth = token ? { Authorization: `Bearer ${token}` } : {};
  return { ...defaultHeaders, ...auth, ...extra };
}

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
    headers: withHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ camera_id: cameraId, recipe_id: recipeId }),
  });
  return mapApiInspection(await parseEnvelope(r));
}

export async function fetchRecentInspections(limit = 20) {
  const r = await fetch(`${API_BASE}/inspections/recent?limit=${limit}`, { headers: withHeaders() });
  const data = await parseEnvelope(r);
  return (data.items || []).map(mapApiInspection);
}

export async function fetchTrendSummary() {
  const r = await fetch(`${API_BASE}/results/trend-summary`, { headers: withHeaders() });
  return parseEnvelope(r);
}

export async function fetchLicenseStatus() {
  const r = await fetch(`${API_BASE}/license/status`, { headers: withHeaders() });
  return parseEnvelope(r);
}

export async function fetchObservabilitySummary() {
  const r = await fetch(`${API_BASE}/observability/summary`, { headers: withHeaders() });
  return parseEnvelope(r);
}

export async function fetchRecipes() {
  const r = await fetch(`${API_BASE}/recipes`, { headers: withHeaders() });
  return parseEnvelope(r);
}

export async function fetchModels() {
  const r = await fetch(`${API_BASE}/models`, { headers: withHeaders() });
  return parseEnvelope(r);
}

export async function submitFeedback({ inspectionId, verdict, comment = '', recipeVersion = 'v1', modelVersion = 'v0' }) {
  const r = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: withHeaders({
      'Content-Type': 'application/json',
      'X-AMX-Role': import.meta.env.VITE_AMX_FEEDBACK_ROLE || 'qa_lead',
    }),
    body: JSON.stringify({
      inspection_id: inspectionId,
      verdict,
      comment,
      recipe_version: recipeVersion,
      model_version: modelVersion,
    }),
  });
  return parseEnvelope(r);
}

export async function login(userId, password) {
  const r = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, password }),
    credentials: 'include',
  });
  const data = await parseEnvelope(r);
  if (data.access_token) setStoredToken(data.access_token);
  return data;
}

export async function fetchAuthMe() {
  const r = await fetch(`${API_BASE}/auth/me`, { headers: withHeaders(), credentials: 'include' });
  return parseEnvelope(r);
}

export async function fetchFeedback(inspectionId) {
  const q = inspectionId ? `?inspection_id=${encodeURIComponent(inspectionId)}` : '';
  const r = await fetch(`${API_BASE}/feedback${q}`, {
    headers: withHeaders({ 'X-AMX-Role': import.meta.env.VITE_AMX_FEEDBACK_ROLE || 'qa_lead' }),
  });
  return parseEnvelope(r);
}
