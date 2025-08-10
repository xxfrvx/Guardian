CREATE TABLE IF NOT EXISTS users (
  user_id BIGINT PRIMARY KEY,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  language_code TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  accepted_terms_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS reputations (
  user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  score INTEGER NOT NULL DEFAULT 0,
  praises_count INTEGER NOT NULL DEFAULT 0,
  reports_count INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TYPE case_type AS ENUM ('report', 'praise');
CREATE TYPE case_status AS ENUM ('pending', 'approved', 'rejected');

CREATE TABLE IF NOT EXISTS cases (
  id BIGSERIAL PRIMARY KEY,
  type case_type NOT NULL,
  status case_status NOT NULL DEFAULT 'pending',
  target_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  author_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  reason TEXT,
  evidence TEXT,
  moderator_user_id BIGINT,
  decision_reason TEXT,
  decided_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TYPE appeal_status AS ENUM ('pending', 'approved', 'rejected');

CREATE TABLE IF NOT EXISTS appeals (
  id BIGSERIAL PRIMARY KEY,
  case_id BIGINT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  appellant_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  message TEXT,
  status appeal_status NOT NULL DEFAULT 'pending',
  moderator_user_id BIGINT,
  decision_reason TEXT,
  decided_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agreements (
  user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  accepted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  terms_version TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cases_target ON cases(target_user_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_appeals_status ON appeals(status);
