#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search.py
Búsqueda de cursos por lista de intereses (keywords).
Carga:
  - 'index.csv'  con líneas 'curso_id|palabra'
  - 'courses.json' dict {curso_id: url}
Retorna: lista de URLs ordenadas por relevancia.

Métrica:
  - Modelo binario + IDF:
      score(curso) = sum_{t in query_tokens ∩ vocab_curso} idf(t)
  - idf(t) = log(1 + N / df(t)), donde N=#cursos únicos, df(t)=#cursos que contienen t
"""

import json
import math
import os
from collections import defaultdict
from typing import Dict, Set, List, Tuple

from crawler import tokenize, load_stopwords  # reutilizamos mismas reglas


def _load_index(index_csv: str) -> Tuple[Dict[str, Set[str]], Set[str]]:
    """
    Carga índice invertido palabra->set(curso_id), y retorna también set de todos los cursos.
    """
    inverted: Dict[str, Set[str]] = defaultdict(set)
    courses_set: Set[str] = set()
    if not os.path.exists(index_csv):
        raise FileNotFoundError(f"No existe {index_csv}")
    with open(index_csv, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            cid, word = line.split("|", 1)
            cid = cid.strip()
            word = word.strip()
            if not cid or not word:
                continue
            inverted[word].add(cid)
            courses_set.add(cid)
    return inverted, courses_set


def _load_courses_dict(dictionary_json: str) -> Dict[str, str]:
    if not os.path.exists(dictionary_json):
        raise FileNotFoundError(f"No existe {dictionary_json}")
    with open(dictionary_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("courses.json inválido")
        return data


def _idf(word: str, inverted: Dict[str, Set[str]], total_courses: int) -> float:
    df = len(inverted.get(word, ()))
    if df == 0:
        return 0.0
    return math.log(1.0 + total_courses / df)


def search(keywords: List[str],
           index_csv: str = "index.csv",
           dictionary_json: str = "courses.json",
           stopwords_path: str = "stopwords_es.txt",
           top_k: int = 20) -> List[str]:
    """
    Dada una lista de palabras de interés, retorna URLs ordenadas por relevancia descendente.
    """
    stopwords = load_stopwords(stopwords_path)
    inverted, courses_set = _load_index(index_csv)
    courses_dict = _load_courses_dict(dictionary_json)

    # normalizar/filtrar query
    query_tokens: List[str] = []
    for kw in keywords:
        query_tokens.extend(tokenize(str(kw), stopwords))
    # quitar duplicados en la query
    query_tokens = list(dict.fromkeys(query_tokens))
    if not query_tokens:
        return []

    # acumular scores
    scores: Dict[str, float] = defaultdict(float)
    N = len(courses_set)

    for t in query_tokens:
        idf = _idf(t, inverted, N)
        for cid in inverted.get(t, ()):
            scores[cid] += idf

    # ordenar por score desc y desempatar por curso_id
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))

    # mapear a URLs (si alguna no está en courses.json, la ignoramos)
    urls = []
    for cid, _ in ranked[:top_k]:
        url = courses_dict.get(cid)
        if url:
            urls.append(url)
    return urls


if __name__ == "__main__":
    # Ejemplo rápido:
    q = ["fotografía", "luminosidad", "composición", "enfoque"]
    result = search(q, index_csv="index.csv", dictionary_json="courses.json")
    print("\nResultados:")
    for u in result:
        print(" -", u)
