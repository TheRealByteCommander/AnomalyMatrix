-- Full inspection payload for API round-trip (Phase 3 persistence)
ALTER TABLE inspections ADD COLUMN IF NOT EXISTS payload JSONB;

CREATE INDEX IF NOT EXISTS idx_inspections_payload_gin ON inspections USING GIN (payload);
