-- Script SQL para criar as tabelas manualmente (caso não use SQLAlchemy migrations)

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  name TEXT,
  email TEXT UNIQUE,
  password_hash TEXT,
  role TEXT DEFAULT 'user',
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS submissions (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  url TEXT,
  status TEXT DEFAULT 'queued',
  result JSONB,
  job_id TEXT UNIQUE,
  created_at TIMESTAMP DEFAULT now(),
  processed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS training_cases (
  id SERIAL PRIMARY KEY,
  title TEXT,
  description TEXT,
  payload_url TEXT,
  lesson JSONB,
  created_at TIMESTAMP DEFAULT now()
);

-- Tabela de quarentena
CREATE TABLE IF NOT EXISTS quarantine (
  id SERIAL PRIMARY KEY,
  item_type TEXT NOT NULL,
  item_identifier TEXT NOT NULL,
  threat_analysis JSONB NOT NULL,
  risk_level TEXT NOT NULL,
  quarantined_at TIMESTAMP DEFAULT now(),
  released_at TIMESTAMP,
  released_by INTEGER REFERENCES users(id),
  status TEXT DEFAULT 'quarantined',
  notes TEXT
);

-- Tabela de blacklist
CREATE TABLE IF NOT EXISTS blacklist (
  id SERIAL PRIMARY KEY,
  item_type TEXT NOT NULL,
  item_value TEXT NOT NULL UNIQUE,
  threat_type TEXT,
  added_at TIMESTAMP DEFAULT now(),
  added_by INTEGER REFERENCES users(id),
  is_active BOOLEAN DEFAULT true,
  notes TEXT
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_submissions_job_id ON submissions(job_id);
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_quarantine_status ON quarantine(status);
CREATE INDEX IF NOT EXISTS idx_quarantine_item ON quarantine(item_type, item_identifier);
CREATE INDEX IF NOT EXISTS idx_blacklist_value ON blacklist(item_value);
CREATE INDEX IF NOT EXISTS idx_blacklist_active ON blacklist(is_active);

-- Tabela de logs de ataques (para análise forense)
CREATE TABLE IF NOT EXISTS attack_logs (
  id SERIAL PRIMARY KEY,
  client_ip TEXT NOT NULL,
  attack_type TEXT NOT NULL,
  risk_level TEXT NOT NULL,
  metadata JSONB NOT NULL,
  report JSONB,
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_attack_logs_ip ON attack_logs(client_ip);
CREATE INDEX IF NOT EXISTS idx_attack_logs_created ON attack_logs(created_at);

