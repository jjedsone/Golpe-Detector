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

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_submissions_job_id ON submissions(job_id);
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

