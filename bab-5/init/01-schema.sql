CREATE TABLE IF NOT EXISTS students (
  id SERIAL PRIMARY KEY,
  nrp VARCHAR(20) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);
INSERT INTO students(nrp, name) VALUES
('31230001', 'Mahasiswa Satu'),
('31230002', 'Mahasiswa Dua')
ON CONFLICT DO NOTHING;
