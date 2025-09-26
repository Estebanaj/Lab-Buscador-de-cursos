# util.py
import urllib.parse
import requests
import bs4  # beautifulsoup4

def is_absolute_url(url: str) -> bool:
    p = urllib.parse.urlparse(url)
    return p.scheme in ("http", "https") and bool(p.netloc)

def remove_fragment(url: str) -> str:
    u = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, u.query, ""))

def convert_if_relative_url(page_url: str, found_url: str):
    """Si found_url es relativa, la convierte respecto a page_url. Si es absoluta, la normaliza.
       Devuelve None si no se puede convertir."""
    if not found_url:
        return None
    try:
        if is_absolute_url(found_url):
            return remove_fragment(found_url)
        absu = urllib.parse.urljoin(page_url, found_url)
        return remove_fragment(absu)
    except Exception:
        return None

def get_request(url: str):
    """Devuelve el objeto response o None si falla."""
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code >= 400:
            return None
        return r
    except Exception:
        return None

def read_request(request):
    """Devuelve el HTML como string o None si falla (p.ej. decodificación)."""
    try:
        return request.text
    except Exception:
        return None

def get_request_url(request) -> str:
    """URL final (puede diferir de la original si hubo redirección)."""
    return str(request.url)

def is_url_ok_to_follow(url: str, domain: str) -> bool:
    """Reglas del enunciado para seguir URLs dentro del dominio, sin '@'/'mailto:' 
       y con nombre de archivo sin extensión o extensión .html."""
    try:
        if not is_absolute_url(url):
            return False
        u = urllib.parse.urlparse(url)
        if u.netloc != domain:
            return False
        if "@" in url or "mailto:" in url:
            return False
        path = u.path or ""
        if "." in path and not path.endswith(".html"):
            return False
        return True
    except Exception:
        return False

def find_sequence(tag: bs4.element.Tag):
    """Busca subsecuencias asociadas a un bloque (si tu catálogo las usa).
       Devuelve lista de <div> de subsecuencia o [] si no hay."""
    # Heurística mínima: buscar contenedores de 'item-programa' y retornar divs hijos 'card-body'
    subs = []
    # caso 1: si tag ya es un contenedor de programa con subsecuencias
    if tag.has_attr("class") and any("item-programa" in c for c in tag.get("class", [])):
        subs = tag.find_all("div", class_="card-body")
    # caso 2: buscar descendientes que representen listas/secuencias
    if not subs:
        containers = tag.find_all("div", class_="item-programa")
        for c in containers:
            subs.extend(c.find_all("div", class_="card-body"))
    return subs or []