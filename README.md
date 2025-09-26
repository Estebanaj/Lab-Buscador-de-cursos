# Lab-Buscador-de-cursos

Este taller implementa un **sistema de búsqueda de cursos** a partir del catálogo de Educación Virtual de la Universidad Javeriana.  
Incluye un **crawler BFS**, un **índice invertido** y la persistencia en **PostgreSQL**, con métricas para comparar y buscar cursos.

---

## 1️⃣ Descripción del taller

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

## 2️⃣ Métricas de comparación entre cursos

Cada curso se representa como un **conjunto de tokens** de su título y descripción.  
La comparación se realiza entre estos conjuntos.

### 🔹 Similitud de Jaccard
\[
\text{Jaccard}(A,B) = \frac{|A \cap B|}{|A \cup B|}
\]

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

## 3️⃣ Comparación curso–curso (ejemplo práctico)

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

