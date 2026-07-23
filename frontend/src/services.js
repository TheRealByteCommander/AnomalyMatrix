const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8080/api/v1';
const TOKEN_KEY = 'amx_access_token';
const useDevAuthHeaders = import.meta.env.VITE_DEV_AUTH_HEADERS === 'true';

/** In-memory access token only — never persist JWTs in localStorage (XSS surface). */
let memoryAccessToken = '';

// Migrate away from legacy localStorage tokens on load
try {
  const legacy = localStorage.getItem(TOKEN_KEY);
  if (legacy) {
    localStorage.removeItem(TOKEN_KEY);
  }
} catch {
  // ignore
}

export function getStoredToken() {
  return memoryAccessToken;
}

export function setStoredToken(token) {
  memoryAccessToken = token || '';
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore storage errors
  }
}

function withHeaders(extra = {}) {
  const headers = { ...extra };
  if (useDevAuthHeaders) {
    headers['X-AMX-Role'] = import.meta.env.VITE_AMX_ROLE || 'operator';
    headers['X-AMX-User'] = import.meta.env.VITE_AMX_USER || 'hmi-operator';
  }
  const token = getStoredToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function withCredentials(init = {}) {
  return { credentials: 'include', ...init, headers: withHeaders(init.headers || {}) };
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
  const r = await fetch(
    `${API_BASE}/inspections/run`,
    withCredentials({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ camera_id: cameraId, recipe_id: recipeId }),
    })
  );
  return mapApiInspection(await parseEnvelope(r));
}

export async function fetchRecentInspections(limit = 20) {
  const r = await fetch(`${API_BASE}/inspections/recent?limit=${limit}`, withCredentials());
  const data = await parseEnvelope(r);
  return (data.items || []).map(mapApiInspection);
}

export async function fetchTrendSummary() {
  const r = await fetch(`${API_BASE}/results/trend-summary`, withCredentials());
  return parseEnvelope(r);
}

export async function fetchLicenseStatus() {
  const r = await fetch(`${API_BASE}/license/status`, withCredentials());
  return parseEnvelope(r);
}

export async function fetchObservabilitySummary() {
  const r = await fetch(`${API_BASE}/observability/summary`, withCredentials());
  return parseEnvelope(r);
}

export async function fetchRecipes() {
  const r = await fetch(`${API_BASE}/recipes`, withCredentials());
  return parseEnvelope(r);
}

export async function fetchModels() {
  const r = await fetch(`${API_BASE}/models`, withCredentials());
  return parseEnvelope(r);
}

export async function submitFeedback({ inspectionId, verdict, comment = '', recipeVersion = 'v1', modelVersion = 'v0' }) {
  const headers = { 'Content-Type': 'application/json' };
  if (useDevAuthHeaders) {
    headers['X-AMX-Role'] = import.meta.env.VITE_AMX_FEEDBACK_ROLE || 'qa_lead';
  }
  const r = await fetch(
    `${API_BASE}/feedback`,
    withCredentials({
      method: 'POST',
      headers,
      body: JSON.stringify({
        inspection_id: inspectionId,
        verdict,
        comment,
        recipe_version: recipeVersion,
        model_version: modelVersion,
      }),
    })
  );
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
  // Keep JWT only in memory for same-tab API calls; session cookie is authoritative.
  if (data.access_token) setStoredToken(data.access_token);
  return data;
}

export async function logout() {
  try {
    await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' });
  } finally {
    setStoredToken('');
  }
}

export async function fetchAuthMe() {
  const r = await fetch(`${API_BASE}/auth/me`, withCredentials());
  return parseEnvelope(r);
}

export async function fetchFeedback(inspectionId) {
  const q = inspectionId ? `?inspection_id=${encodeURIComponent(inspectionId)}` : '';
  const headers = {};
  if (useDevAuthHeaders) {
    headers['X-AMX-Role'] = import.meta.env.VITE_AMX_FEEDBACK_ROLE || 'qa_lead';
  }
  const r = await fetch(`${API_BASE}/feedback${q}`, withCredentials({ headers }));
  return parseEnvelope(r);
}
