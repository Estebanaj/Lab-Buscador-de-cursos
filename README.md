# Lab-Buscador-de-cursos

Este taller implementa un **sistema de búsqueda de cursos** a partir del catálogo de Educación Virtual de la Universidad Javeriana.  
Incluye un **crawler BFS**, un **índice invertido** y la persistencia en **PostgreSQL**, con métricas para comparar y buscar cursos.

---

## 1️ Descripción del taller

El objetivo es construir un mini motor de búsqueda capaz de:

1. **Rastrear cursos** en el dominio `educacionvirtual.javeriana.edu.co`.  
2. **Tokenizar y normalizar texto** (minúsculas, stopwords).  
3. **Construir un índice invertido** (palabra → cursos).  
4. **Cargar en PostgreSQL** los archivos generados (`index.csv`, `courses.csv`).  
5. **Consultar** los cursos desde SQL con palabras clave.  
6. **Comparar cursos entre sí** con métricas de similitud.  

### Objetivos de aprendizaje
- Implementar un **crawler iterativo (BFS con cola FIFO)**.  
- Diseñar un **índice invertido** a partir de tokens limpios.  
- Persistir datos en archivos y en una base **relacional**.  
- Escribir **consultas SQL** que recuperen cursos según palabras clave.  
- Aplicar **métricas de comparación** para detectar similitud entre cursos.  

---

## 2️ Métricas de comparación entre cursos

Cada curso se representa como un **conjunto de tokens** de su título y descripción.  
La comparación se realiza entre estos conjuntos.

### 🔹 Similitud de Jaccard
$$
Jaccard(A, B) = \frac{|A \cap B|}{|A \cup B|}
$$

- 0 = cursos completamente distintos.  
- 1 = cursos idénticos.  

Ejemplo:
- Curso A: `{gestion, proyectos, virtual, salud}`  
- Curso B: `{gestion, estrategia, organizaciones}`  
- Jaccard = 1/6 ≈ **0.16**

### 🔹 Coincidencia binaria
\[
\text{Binaria}(A,B) =
\begin{cases}
1 & \text{si } |A \cap B| > 0 \\
0 & \text{si } |A \cap B| = 0
\end{cases}
\]

### 🔹 Extensión opcional: IDF
Palabras raras pesan más:
\[
IDF(t) = \log \frac{N}{df(t)}
\]

---

## 3️ Comparación curso–curso (ejemplo práctico)

### Ejemplo 1: dos cursos
- Curso A: *Gestión de Proyectos en Salud Virtual* → `{gestion, proyectos, salud, virtual}`  
- Curso B: *Estrategia y Gestión de Organizaciones* → `{estrategia, gestion, organizaciones}`  
- Similitud Jaccard = 1/6 = **0.16**

👉 Cursos relacionados débilmente.

### Ejemplo 2: un curso contra todos
Consulta SQL para comparar un curso contra todos los demás:

```sql
SELECT c2.curso_id, c2.url,
       COUNT(*)::float /
       ( (SELECT COUNT(DISTINCT palabra) FROM idx WHERE curso_id = 'cursoA')
       + (SELECT COUNT(DISTINCT palabra) FROM idx WHERE curso_id = c2.curso_id)
       - COUNT(*) ) AS jaccard
FROM idx i1
JOIN idx i2 ON i1.palabra = i2.palabra
JOIN courses c2 ON c2.curso_id = i2.curso_id
WHERE i1.curso_id = 'cursoA' AND i2.curso_id <> 'cursoA'
GROUP BY c2.curso_id, c2.url
ORDER BY jaccard DESC
LIMIT 5;
```
## 4️ Medición de los algoritmos

Esta sección describe **qué medir**, **cómo medirlo** y con **qué consultas SQL** evaluar el rendimiento de cada parte del taller.

---

### 4.1 Crawler: cobertura y desempeño

**Qué medir (KPIs):**
- Páginas visitadas (`pages_visited`)  
- Cursos mapeados (`courses`)  
- Palabras en el índice (`idx`)  
- Tokens por curso (media, min, max)  
- Tiempo total de ejecución  

**Consultas en PostgreSQL:**
```sql
-- Total cursos y total pares (curso, palabra)
SELECT COUNT(*) AS cursos FROM courses;
SELECT COUNT(*) AS pares  FROM idx;

-- Tamaño de vocabulario (palabras únicas)
SELECT COUNT(DISTINCT palabra) AS vocab FROM idx;

-- Distribución de tokens por curso
SELECT AVG(cnt)::numeric(10,2) AS avg_tokens,
       MIN(cnt) AS min_tokens,
       MAX(cnt) AS max_tokens
FROM (
  SELECT curso_id, COUNT(DISTINCT palabra) AS cnt
  FROM idx
  GROUP BY curso_id
) t;
```
## 5️ Índice y stopwords: calidad de términos

El **índice invertido** es la tabla `idx(curso_id, palabra)` generada por el crawler a partir de **títulos + descripciones**.  
Para asegurar calidad, limpiamos tokens a **minúsculas**, quitamos **puntuación** y filtramos **stopwords** (archivo `stopwords_es.txt`).

**Checklist para una buena calidad del índice**
- [x] `stopwords_es.txt` incluye conectores comunes: _de, la, el, en, para, con, por, del, los, las…_  
- [x] `tokenize()` aplica stopwords **antes** de escribir en `index.csv`.  
- [x] (Opcional) normalizar tildes: `gestión → gestion`, `inteligencia → inteligencia`.  
- [x] Re-ejecutar el pipeline tras cambios en stopwords:
  1) `python run_crawler.py`  
  2) regenerar `courses.csv`  
  3) recargar `idx` y `courses` en PostgreSQL

**Consultas de diagnóstico**
```sql
-- Top 20 palabras más frecuentes (detecta si aún quedaron stopwords)
SELECT palabra, COUNT(*) AS freq
FROM idx
GROUP BY palabra
ORDER BY freq DESC
LIMIT 20;

-- Tamaño del vocabulario (palabras únicas)
SELECT COUNT(DISTINCT palabra) AS vocab FROM idx;

-- Distribución de tokens por curso (calidad de cobertura)
SELECT AVG(cnt)::numeric(10,2) AS avg_tokens,
       MIN(cnt) AS min_tokens,
       MAX(cnt) AS max_tokens
FROM (
  SELECT curso_id, COUNT(DISTINCT palabra) AS cnt
  FROM idx
  GROUP BY curso_id
) t;

-- IDF aproximado (palabras raras pesan más)
WITH
N AS (SELECT COUNT(*)::float AS n FROM courses),
DF AS (
  SELECT palabra, COUNT(DISTINCT curso_id) AS df
  FROM idx GROUP BY palabra
)
SELECT d.palabra,
       d.df,
       ROUND(LN(n.n / d.df)::numeric, 4) AS idf
FROM DF d, N n
ORDER BY idf DESC
LIMIT 20;
```

## 6 Búsqueda **binaria** (conteo de coincidencias)

La búsqueda **binaria** puntúa cada curso solo por **cuántas** palabras de la consulta contiene (sin pesos).  
Es una base simple para comparar contra la versión ponderada por IDF.

### 📏 Definición

Sea:
- \( Q \) = conjunto de términos de la consulta (ya normalizados y sin stopwords)
- \( V_c \) = conjunto de términos indexados del curso \( c \)

El **score binario** es:
\[
\text{score}_\text{bin}(c, Q) \;=\; |\,Q \cap V_c\,|
\]

- Más alto = más coincidencias con la consulta.
- Empates se rompen por `curso_id` o por reglas adicionales (p. ej., longitud del curso).

---

### 🧪 SQL – Ranking binario (ejemplo con “inteligencia artificial”)

```sql
WITH Q(term) AS (
  VALUES ('inteligencia'), ('artificial')  -- <-- normaliza aquí tus términos
)
SELECT
  c.url,
  COUNT(DISTINCT i.palabra) AS score_bin
FROM idx i
JOIN courses c ON c.curso_id = i.curso_id
WHERE i.palabra IN (SELECT term FROM Q)
GROUP BY c.url
ORDER BY score_bin DESC, c.url
LIMIT 10;
