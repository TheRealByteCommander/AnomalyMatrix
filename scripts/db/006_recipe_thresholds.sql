-- Recipe-level traffic-light thresholds (HMI adjustable)

ALTER TABLE recipes
  ADD COLUMN IF NOT EXISTS decision_thresholds JSONB
  NOT NULL DEFAULT '{"amber": 0.55, "red": 0.85}'::jsonb;

UPDATE recipes
SET decision_thresholds = '{"amber": 0.55, "red": 0.85}'::jsonb
WHERE decision_thresholds IS NULL;
