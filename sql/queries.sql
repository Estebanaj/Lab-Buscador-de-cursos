-- 1) Dada una palabra, obtener las URLs donde aparece
--   :palabra = parámetro (usa minúsculas como en el índice)
SELECT DISTINCT c.url
FROM idx i
JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra = LOWER(:palabra);

-- 2) Intersección de varias palabras (todas deben aparecer)
--   Cambia :p1, :p2, :p3 por tus palabras
SELECT c.url
FROM idx i
JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra IN (LOWER(:p1), LOWER(:p2), LOWER(:p3))
GROUP BY c.url
HAVING COUNT(DISTINCT i.palabra) = 3;

-- 3) Top cursos por una palabra (aquí cada par es único, así que es una lista simple)
SELECT i.curso_id, c.url
FROM idx i
JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra = LOWER(:palabra)
ORDER BY i.curso_id
LIMIT 20;

-- Cursos que mencionan "empleabilidad"
SELECT DISTINCT c.url
FROM idx i JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra = 'empleabilidad'
LIMIT 10;

-- Cursos relacionados con "salud"
SELECT DISTINCT c.url
FROM idx i JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra = 'salud'
LIMIT 10;

-- Cursos con "inteligencia"
SELECT DISTINCT c.url
FROM idx i JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra = 'inteligencia'
LIMIT 10;

-- Cursos que contienen "competencias" y "digitales"
SELECT c.url
FROM idx i JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra IN ('competencias','digitales')
GROUP BY c.url
HAVING COUNT(DISTINCT i.palabra) = 2;

-- Cursos que hablan de "inteligencia" y "artificial"
SELECT c.url
FROM idx i JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra IN ('inteligencia','artificial')
GROUP BY c.url
HAVING COUNT(DISTINCT i.palabra) = 2;

-- Cursos que contienen "salud" y "seguridad"
SELECT c.url
FROM idx i JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra IN ('salud','seguridad')
GROUP BY c.url
HAVING COUNT(DISTINCT i.palabra) = 2;

-- Cursos que contengan "empleabilidad" o "capital"
SELECT DISTINCT c.url
FROM idx i JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra IN ('empleabilidad','capital')
LIMIT 10;

-- Cursos que contengan "modalidad", "virtual" o "gratuito"
SELECT DISTINCT c.url
FROM idx i JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra IN ('modalidad','virtual','gratuito')
LIMIT 10;

-- Cursos que contienen más de 3 palabras del top 20
SELECT c.url, COUNT(DISTINCT i.palabra) AS coincidencias
FROM idx i JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra IN ('horas','gestion','usd','empleabilidad','virtual',
                    'competencias','digitales','gratuito','modalidad',
                    'educativo','docente','salud','competencia','safety',
                    'seguridad','artificial','inteligencia','principalmente',
                    'francisco','capital')
GROUP BY c.url
HAVING COUNT(DISTINCT i.palabra) >= 3
ORDER BY coincidencias DESC
LIMIT 10;