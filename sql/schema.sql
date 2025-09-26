-- Crea esquema mínimo para cargar el índice y el diccionario
-- Tabla índice invertido: (curso_id, palabra)
CREATE TABLE IF NOT EXISTS idx (
  curso_id VARCHAR(255) NOT NULL,
  palabra  VARCHAR(255) NOT NULL,
  CONSTRAINT idx_pk PRIMARY KEY (curso_id, palabra)
);

-- Tabla diccionario: id -> url
CREATE TABLE IF NOT EXISTS courses (
  curso_id VARCHAR(255) PRIMARY KEY,
  url      TEXT NOT NULL
);
