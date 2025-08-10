CREATE TYPE coin_status AS ENUM ('pending','listed','rejected');

CREATE TABLE IF NOT EXISTS coins (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  symbol TEXT,
  chain TEXT,
  contract_address TEXT,
  reasons TEXT[],
  status coin_status NOT NULL DEFAULT 'pending',
  added_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
  decided_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
  decided_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_coins_contract ON coins(contract_address);
CREATE INDEX IF NOT EXISTS idx_coins_status ON coins(status);
