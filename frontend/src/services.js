const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api/v1';

export async function runInspection() {
  const r = await fetch(`${API_BASE}/inspections/run`, { method: 'POST' });
  if (!r.ok) throw new Error(`Inspection failed (${r.status})`);
  const body = await r.json();
  return body.data;
}

export async function fetchRecentInspections() {
  const r = await fetch(`${API_BASE}/inspections/recent`);
  if (!r.ok) throw new Error(`Recent inspections failed (${r.status})`);
  const body = await r.json();
  return body.data.items || [];
}
