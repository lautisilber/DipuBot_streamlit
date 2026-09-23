"""Búsqueda exacta local: un número de ley no depende de similitud semántica."""

import re
import sqlite3
from pathlib import Path


def law_numbers(question: str) -> list[str]:
    return list(dict.fromkeys(
        number.replace(".", "") for number in re.findall(
            r"\bley\s*(?:n[°ºo.]?\s*)?(\d{1,3}\.\d{3}|\d{4,6})\b",
            question, re.IGNORECASE,
        )
    ))


def lookup_laws(question: str, db_path: Path) -> list[dict]:
    numbers = law_numbers(question)
    if not numbers or not db_path.exists():
        return []
    conn = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        placeholders = ",".join("?" for _ in numbers)
        rows = conn.execute(
            f"SELECT * FROM leyes WHERE UPPER(tipo_norma) = 'LEY' "
            f"AND REPLACE(CAST(numero_norma AS TEXT), '.', '') IN ({placeholders})",
            numbers,
        ).fetchall()
        chunks = []
        for row in rows:
            data = dict(row)
            # Texto original: no presentar silenciosamente una versión posterior
            # como si fuera el texto sancionado.
            text = data.get("texto_original") or data.get("texto_actualizado")
            if not text or not text.strip():
                continue
            version = "original" if data.get("texto_original") else "actualizado"
            # Cota conservadora para normas excepcionalmente largas.
            excerpt = text[:120_000]
            if len(text) > len(excerpt):
                excerpt += "\n[Texto parcial: no inferir que los artículos omitidos no existen.]"
            chunks.append({
                **data, "text": f"Versión: texto {version}.\n{excerpt}",
                "doc_id": str(data["id"]), "chunk_index": 0,
                "similarity": 1.0, "exact_match": True,
            })
        return chunks
    finally:
        conn.close()
