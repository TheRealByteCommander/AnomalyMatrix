-- Core schema: recipes, RBAC, audit, model registry, feedback (BUILD_READY_SPEC v1)

CREATE TABLE IF NOT EXISTS roles (
  role_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  role_id TEXT NOT NULL REFERENCES roles(role_id),
  api_key TEXT UNIQUE,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recipes (
  recipe_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  recipe_version TEXT NOT NULL DEFAULT 'v1',
  camera_profile JSONB NOT NULL DEFAULT '{}'::jsonb,
  lighting_profile JSONB NOT NULL DEFAULT '{}'::jsonb,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_registry (
  model_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  provider TEXT NOT NULL,
  dataset_version TEXT NOT NULL DEFAULT 'v1',
  status TEXT NOT NULL DEFAULT 'active',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
  audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  resource_type TEXT,
  resource_id TEXT,
  before_state JSONB,
  after_state JSONB,
  reason TEXT,
  request_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback_events (
  feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  inspection_id TEXT NOT NULL,
  actor TEXT NOT NULL,
  verdict TEXT NOT NULL,
  comment TEXT,
  recipe_version TEXT,
  model_version TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_inspection ON feedback_events(inspection_id);
CREATE INDEX IF NOT EXISTS idx_model_registry_status ON model_registry(status);

-- Default roles (IEC 62443-oriented)
INSERT INTO roles (role_id, display_name) VALUES
  ('operator', 'Operator'),
  ('qa_lead', 'QA Lead'),
  ('process_engineer', 'Process Engineer'),
  ('admin', 'Admin')
ON CONFLICT (role_id) DO NOTHING;

-- Default users (DEV ONLY api keys — rotate before production; never reuse these in prod)
INSERT INTO users (user_id, display_name, role_id, api_key) VALUES
  ('operator-1', 'Line Operator', 'operator', 'amx-key-operator'),
  ('qa-1', 'QA Lead', 'qa_lead', 'amx-key-qa'),
  ('engineer-1', 'Process Engineer', 'process_engineer', 'amx-key-engineer'),
  ('admin-1', 'System Admin', 'admin', 'amx-key-admin')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO recipes (recipe_id, name, recipe_version, camera_profile, lighting_profile) VALUES
  ('recipe-default', 'Default Seam Inspection', 'v1', '{"camera_id":"cam-01","exposure_ms":10}', '{"gain_db":2}')
ON CONFLICT (recipe_id) DO NOTHING;

INSERT INTO model_registry (model_id, name, model_version, provider, dataset_version, status) VALUES
  ('patchcore-mvp', 'PatchCore MVP', 'v0', 'stub', 'v1', 'active'),
  ('opencv-ready', 'OpenCV Ready Baseline', 'v0', 'opencv_ready', 'v1', 'active')
ON CONFLICT (model_id) DO NOTHING;
