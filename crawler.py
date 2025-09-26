#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crawler.py
Rastreador BFS del catálogo de Educación Continua U. Javeriana que:
  - Visita hasta n páginas (FIFO, no recursivo) dentro del dominio.
  - Extrae cursos desde bloques <div class="card-body"> en páginas de listado.
  - Construye un índice invertido palabra -> {curso_id} a partir de títulos y descripciones.
  - Normaliza tokens, elimina stopwords y puntuación final (! . :)
  - Persiste:
      * index.csv   : líneas "curso_id|palabra"
      * courses.json: dict {curso_id: url}
Uso:
    from crawler import go
    go(n=200, dictionary="courses.json", output="index.csv")
"""

import collections
import json
import os
import re
import time
from typing import Dict, Set, List, Tuple
from urllib.parse import urlparse, urljoin
from collections import deque

import bs4
import requests

START_URL = "https://educacionvirtual.javeriana.edu.co/nuestros-programas-nuevo"
ALLOWED_DOMAIN = "educacionvirtual.javeriana.edu.co"

# ---------- Utilidades de URL ----------

def remove_fragment(url: str) -> str:
    """Elimina el fragmento #... si existe."""
    if not url:
        return url
    return url.split("#", 1)[0]

def is_absolute_url(url: str) -> bool:
    """True si la URL es absoluta (http/https)."""
    if not url:
        return False
    u = urlparse(url)
    return u.scheme in ("http", "https") and bool(u.netloc)

def convert_if_relative_url(base_url: str, href: str) -> str:
    """Convierte href relativo a absoluto. Retorna None si no puede."""
    if not href:
        return None
    href = href.strip()
    try:
        if is_absolute_url(href):
            return remove_fragment(href)
        # relativo
        absu = urljoin(base_url, href)
        return remove_fragment(absu)
    except Exception:
        return None

def is_url_ok_to_follow(url: str, domain: str) -> bool:
    """
    Criterios:
      1) Absoluta
      2) Mismo dominio
      3) No contiene '@' ni 'mailto:'
      4) Path termina sin extensión o con .html (o no tiene extensión claramente binaria)
    """
    if not is_absolute_url(url):
        return False
    u = urlparse(url)
    if u.netloc != domain:
        return False
    if "@" in url or "mailto:" in url:
        return False
    # Validar extensión
    path = u.path or ""
    # permitir paths como "/algo", "/algo/" o "/algo.html"
    if path.endswith("/") or path.endswith(".html") or (("." not in os.path.basename(path)) and path != ""):
        return True
    # URL raíz
    if path == "":
        return True
    return False

# ---------- Red & Parsing ----------

def get_request(url: str):
    """Envuelve requests.get con manejo de errores y headers básicos."""
    try:
        resp = requests.get(url, timeout=12, headers={
            "User-Agent": "UJ-SearchLab/1.0 (+student project)"
        })
        if resp.status_code >= 400:
            return None
        return resp
    except requests.RequestException:
        return None

def read_request(resp) -> str:
    """Obtiene texto HTML de la respuesta. Puede contener reemplazos de caracteres."""
    if resp is None:
        return ""
    resp.encoding = resp.encoding or "utf-8"
    return resp.text or ""

def get_request_url(resp) -> str:
    """URL final (tras redirecciones)."""
    if resp is None:
        return ""
    return resp.url

# ---------- Tokenización y stopwords ----------

PUNCT_END_RE = re.compile(r"[!.\:]+$")  # signos de puntuación a eliminar al final
TOKEN_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-z0-9_ÁÉÍÓÚÜÑáéíóúüñ]*$")

def load_stopwords(path: str = "stopwords_es.txt") -> Set[str]:
    sw = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w and not w.startswith("#"):
                    sw.add(w)
    # Añade términos comunes del dominio que no aportan
    sw.update({"curso", "cursos", "estudiantes", "profesionales", "programa", "universidad",
               "javeriana", "bogotá", "duración", "nivel", "precio", "fecha", "inicio"})
    return sw

def normalize_token(w: str) -> str:
    w = w.strip()
    w = PUNCT_END_RE.sub("", w)
    w = w.replace("\u00A0", " ")  # &nbsp;
    w = w.lower()
    return w

def valid_word(w: str) -> bool:
    if len(w) <= 1:
        return False
    return bool(TOKEN_RE.match(w))

def tokenize(text: str, stopwords: Set[str]) -> List[str]:
    if not text:
        return []
    raw = re.split(r"\s+", text)
    out = []
    for r in raw:
        t = normalize_token(r)
        if t and valid_word(t) and t not in stopwords:
            out.append(t)
    return out

# ---------- Extracción de cursos desde HTML ----------

def extract_course_blocks(soup: bs4.BeautifulSoup) -> List[bs4.Tag]:
    """
    Devuelve todos los <div class="card-body"> potencialmente asociados a cursos
    (en listados del catálogo).
    """
    return soup.find_all("div", class_="card-body")

def extract_course_from_block(block: bs4.Tag) -> Tuple[str, str, str]:
    """
    Desde un bloque <div class="card-body"> intenta extraer:
      - course_id (último segmento del href del <a>)
      - course_url
      - course_text (título + descripciones <p>)
    Retorna (course_id, course_url, course_text) o (None, None, None) si no se puede.
    """
    try:
        a = block.find("a", href=True)
        if not a:
            return (None, None, None)
        href = a["href"].strip()
        # convertir relativo a absoluto si aplica
        course_url = convert_if_relative_url(START_URL, href)
        if not course_url:
            return (None, None, None)
        # id = último segmento del path (sin '/')
        path = urlparse(course_url).path
        seg = [s for s in path.split("/") if s]
        if not seg:
            return (None, None, None)
        course_id = seg[-1]

        # texto del título + p's
        title = ""
        # Hay títulos en <b class="card-title ..."> o simplemente texto del <a>
        title_b = a.find("b")
        if title_b and title_b.text:
            title = title_b.text.strip()
        else:
            title = a.text.strip()

        desc_parts = []
        for p in block.find_all("p"):
            desc_parts.append(p.get_text(separator=" ", strip=True))
        course_text = (title + " " + " ".join(desc_parts)).strip()
        return (course_id, course_url, course_text)
    except Exception:
        return (None, None, None)

# ---------- Crawler principal ----------

def go(n: int, dictionary: str, output: str, stopwords_path: str = "stopwords_es.txt") -> None:
    stopwords = load_stopwords(stopwords_path)

    visited = set()                    # URLs finales ya visitadas
    queue = deque([START_URL])         # FIFO
    seen_in_queue = {START_URL}        # para no encolar duplicados

    inverted = collections.defaultdict(set)
    courses = {}
    if os.path.exists(dictionary):
        try:
            with open(dictionary, "r", encoding="utf-8") as f:
                prev = json.load(f)
                if isinstance(prev, dict):
                    courses.update(prev)
        except Exception:
            pass

    fetched_cache = {}                 # url_final -> html
    pages_visited = 0

    while queue and pages_visited < n:
        requested = queue.popleft()

        # No sigas si no es válida (absoluta, mismo dominio, etc.)
        if not is_url_ok_to_follow(requested, ALLOWED_DOMAIN):
            continue

        # GET (apoyado en cache)
        if requested in fetched_cache:
            html = fetched_cache[requested]
            final_url = requested
        else:
            resp = get_request(requested)
            if resp is None:
                continue
            final_url = get_request_url(resp) or requested
            html = read_request(resp)
            fetched_cache[final_url] = html

        # Si ya visitamos esa URL final, salta
        if final_url in visited:
            continue
        visited.add(final_url)
        pages_visited += 1

        soup = bs4.BeautifulSoup(html, "html5lib")

        # (1) extrae cursos desde la página actual
        for b in extract_course_blocks(soup):
            cid, curl, ctext = extract_course_from_block(b)
            if cid and curl:
                courses[cid] = curl
                for tk in tokenize(ctext, stopwords):
                    inverted[tk].add(cid)

        # (2) descubre nuevos enlaces y ENCOLA en orden de aparición
        for a in soup.find_all("a", href=True):
            absu = convert_if_relative_url(final_url, a["href"])
            if not absu:
                continue
            if not is_url_ok_to_follow(absu, ALLOWED_DOMAIN):
                continue
            if absu in visited:
                continue
            if absu in seen_in_queue:
                continue
            queue.append(absu)
            seen_in_queue.add(absu)

        time.sleep(0.2)

    # persistencia igual que antes...
    with open(output, "w", encoding="utf-8") as f:
        for word, cset in inverted.items():
            for cid in sorted(cset):
                f.write(f"{cid}|{word}\n")

    with open(dictionary, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)

    print(f"[OK] Páginas visitadas: {pages_visited}")
    print(f"[OK] Cursos mapeados : {len(courses)}")
    print(f"[OK] Palabras índice : {len(inverted)}")