CREATE TABLE IF NOT EXISTS inspections (
  inspection_id UUID PRIMARY KEY,
  camera_id TEXT NOT NULL,
  recipe_id TEXT NOT NULL,
  anomaly_score DOUBLE PRECISION NOT NULL,
  status TEXT NOT NULL,
  decision TEXT NOT NULL,
  provider TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inspections_recipe ON inspections(recipe_id);
CREATE INDEX IF NOT EXISTS idx_inspections_score ON inspections(anomaly_score);
CREATE INDEX IF NOT EXISTS idx_inspections_created ON inspections(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inspections_recipe_created ON inspections(recipe_id, created_at DESC);
