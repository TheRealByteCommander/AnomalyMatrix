export const CUSTOM_RECIPE_ID = 'recipe-custom';
export const DEFAULT_RECIPE_ID = 'recipe-default';

export function recipeFixtures() {
  return [
    {
      recipe_id: DEFAULT_RECIPE_ID,
      name: 'Default',
      recipe_version: 'v1',
      active: true,
      protected: true,
      status: 'active',
      camera_profile: { camera_id: 'cam-01', exposure_ms: 10 },
      lighting_profile: { gain_db: 2 },
      decision_thresholds: { amber: 0.55, red: 0.85 },
    },
    {
      recipe_id: CUSTOM_RECIPE_ID,
      name: 'Custom Seam',
      recipe_version: 'v2',
      active: false,
      status: 'inactive',
      camera_profile: { camera_id: 'cam-02', exposure_ms: 8 },
      lighting_profile: { gain_db: 1 },
      decision_thresholds: { amber: 0.4, red: 0.7 },
    },
  ];
}

export function inspectionDto({ recipeId = DEFAULT_RECIPE_ID, id = 'INSP-E2E-1' } = {}) {
  return {
    inspection_id: id,
    decision: 'green',
    frame: {
      recipe_id: recipeId,
      camera_id: 'cam-01',
      captured_at: new Date().toISOString(),
      recipe_version: recipeId === CUSTOM_RECIPE_ID ? 'v2' : 'v1',
    },
    inference: {
      anomaly_score: 0.12,
      status: 'ok',
      heatmap_uri: 'placeholder:none',
      model_version: 'v0',
    },
    heatmap: { uri: 'placeholder:none', placeholder: true, kind: 'none' },
    decision_thresholds: { amber: 0.55, red: 0.85 },
    qa: { pending: false, auto_decision: 'green' },
    camera_ids: ['cam-01'],
    view_count: 1,
  };
}

function corsHeaders(request) {
  const origin = request.headers()['origin'] || 'http://127.0.0.1:5173';
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Allow-Headers': 'content-type,authorization,x-amx-role,x-amx-user',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    'Content-Type': 'application/json',
  };
}

function json(request, data, status = 200) {
  return {
    status,
    headers: corsHeaders(request),
    body: JSON.stringify({ ok: true, data, meta: { requestId: 'e2e' } }),
  };
}

export async function mockHmiApi(page, options = {}) {
  const state = {
    recipes: options.recipes || recipeFixtures(),
    inspections: [],
    runRequests: [],
    feedbackRequests: [],
  };

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    if (request.method() === 'OPTIONS') {
      await route.fulfill({ status: 204, headers: corsHeaders(request), body: '' });
      return;
    }

    const url = new URL(request.url());
    const path = url.pathname.replace(/\/+$/, '');
    const method = request.method();
    let body = {};
    try {
      body = request.postDataJSON() || {};
    } catch {
      body = {};
    }

    if (path.endsWith('/auth/me') && method === 'GET') {
      await route.fulfill(json(request, {
        user_id: 'operator-1',
        display_name: 'E2E Operator',
        role: 'operator',
        role_id: 'operator',
        permissions: ['inspection.run', 'inspection.read', 'recipes.read'],
      }));
      return;
    }
    if (path.endsWith('/auth/logout') && method === 'POST') {
      await route.fulfill(json(request, { logged_out: true }));
      return;
    }
    if (path.endsWith('/inspections/recent') && method === 'GET') {
      await route.fulfill(json(request, { items: state.inspections, count: state.inspections.length }));
      return;
    }
    if (path.endsWith('/inspections/run') && method === 'POST') {
      state.runRequests.push(body);
      const item = inspectionDto({
        recipeId: body.recipe_id || DEFAULT_RECIPE_ID,
        id: `INSP-E2E-${state.runRequests.length}`,
      });
      state.inspections = [item, ...state.inspections].slice(0, 20);
      await route.fulfill(json(request, item));
      return;
    }
    if (path.endsWith('/recipes') && method === 'GET') {
      await route.fulfill(json(request, { items: state.recipes, count: state.recipes.length }));
      return;
    }
    if (path.endsWith('/models') && method === 'GET') {
      await route.fulfill(json(request, {
        items: [],
        active: null,
        memory_bank: { loaded: false },
        training_samples: { count: 0, recipe_id: url.searchParams.get('recipe_id') || DEFAULT_RECIPE_ID },
        nio_samples: { count: 0, recipe_id: url.searchParams.get('recipe_id') || DEFAULT_RECIPE_ID },
      }));
      return;
    }
    if (path.endsWith('/cameras') && method === 'GET') {
      await route.fulfill(json(request, {
        cameras: [
          { camera_id: 'cam-01', label: 'Cam 01', available: true, selected: true },
          { camera_id: 'cam-02', label: 'Cam 02', available: true, selected: false },
        ],
        driver: 'stub',
        max_selectable: 4,
        selection: { camera_ids: ['cam-01'] },
      }));
      return;
    }
    if (path.endsWith('/observability/summary') && method === 'GET') {
      await route.fulfill(json(request, {
        inference_latency_mean_ms: 12,
        inspection_count: state.inspections.length,
        anomaly_count: 0,
        trend_warning: false,
        trend_severity: 'green',
        opc_ua_publish_error_rate_pct: 0,
      }));
      return;
    }
    if (path.endsWith('/results/trend-summary') && method === 'GET') {
      await route.fulfill(json(request, {
        avg_score: 0.12,
        max_score: 0.12,
        anomaly_count: 0,
        count: state.inspections.length,
        trend_warning: false,
        trend_severity: 'green',
        by_camera: [],
      }));
      return;
    }
    if (path.endsWith('/license/status') && method === 'GET') {
      await route.fulfill(json(request, {
        active: true,
        tier: 'dev',
        mode: 'local',
        billing_enabled: false,
        grace_active: false,
        features: ['inspection'],
      }));
      return;
    }
    if (path.endsWith('/station/vision-profile') && method === 'GET') {
      await route.fulfill(json(request, {
        station_id: 'eol-1',
        line_id: 'line-a',
        name: 'EOL default',
        max_cameras: 4,
        cameras: [],
        checklist: {},
      }));
      return;
    }
    if (path.endsWith('/station/recommendations') && method === 'GET') {
      await route.fulfill(json(request, { items: [] }));
      return;
    }
    if (path.endsWith('/storage/stats') && method === 'GET') {
      await route.fulfill(json(request, { object_count: 0, total_bytes: 0, avg_bytes: 0 }));
      return;
    }
    if (path.endsWith('/storage/retention') && method === 'GET') {
      await route.fulfill(json(request, { ttl_days: 30, archive_bucket: '', archive_prefix: '', enabled: true }));
      return;
    }
    if (path.endsWith('/system/watchdog') && method === 'GET') {
      await route.fulfill(json(request, { status: 'ok', gap_detected: false, capture_count: 0, gap_count: 0 }));
      return;
    }
    if (path.endsWith('/mqtt/status') && method === 'GET') {
      await route.fulfill(json(request, { enabled: false, connected: false }));
      return;
    }
    if (path.endsWith('/feedback') && method === 'POST') {
      state.feedbackRequests.push(body);
      const current = state.inspections[0] || inspectionDto();
      if (body.verdict === 'confirm_anomaly') {
        current.decision = 'red';
        current.qa = { ...(current.qa || {}), verdict: 'confirm_anomaly', override: 'nio', pending: false };
      }
      await route.fulfill(json(request, {
        inspection: current,
        nio_sample: body.verdict === 'confirm_anomaly' ? { stored: true } : null,
      }));
      return;
    }

    await route.fulfill(json(request, {}));
  });

  return state;
}
