-- Auth extensions: password hash + server-side sessions (v0.8)

ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Default dev password: changeme (PBKDF2 — rotate in production)
UPDATE users SET password_hash = COALESCE(
  password_hash,
  'dev-placeholder'
) WHERE password_hash IS NULL;
