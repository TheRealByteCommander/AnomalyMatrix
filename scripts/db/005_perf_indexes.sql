-- Composite index for common recipe + recency filters (trend / query paths)
CREATE INDEX IF NOT EXISTS idx_inspections_recipe_created
  ON inspections (recipe_id, created_at DESC);
