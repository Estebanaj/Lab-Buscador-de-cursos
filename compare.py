#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare.py
Medida de similitud entre cursos en [0,1] usando Jaccard sobre vocabulario de cada curso.
Se reconstruye el vocabulario del curso a partir del índice invertido (index.csv).

Jaccard(A,B) = |A ∩ B| / |A ∪ B|
"""

import os
from collections import defaultdict
from typing import Dict, Set, Tuple

def _load_index(index_csv: str) -> Dict[str, Set[str]]:
    """
    Retorna curso_id -> set(palabras)
    A partir de líneas 'curso_id|palabra'
    """
    course_vocab: Dict[str, Set[str]] = defaultdict(set)
    if not os.path.exists(index_csv):
        raise FileNotFoundError(f"No existe {index_csv}")
    with open(index_csv, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            cid, w = line.split("|", 1)
            cid = cid.strip()
            w = w.strip()
            if cid and w:
                course_vocab[cid].add(w)
    return course_vocab


def compare(curso1: str, curso2: str, index_csv: str = "index.csv") -> float:
    """
    Retorna similitud Jaccard en [0,1] entre los vocabularios de curso1 y curso2.
    curso1/curso2 son IDs (p.ej. 'propiedad-horizontal')
    """
    course_vocab = _load_index(index_csv)
    v1 = course_vocab.get(curso1, set())
    v2 = course_vocab.get(curso2, set())
    if not v1 and not v2:
        return 0.0
    inter = len(v1 & v2)
    union = len(v1 | v2)
    return inter / union if union > 0 else 0.0


if __name__ == "__main__":
    # Ejemplo:
    s = compare("propiedad-horizontal", "fotografia-basica", index_csv="index.csv")
    print(f"similaridad = {s:.3f}")
