"""
etl/eval/build_dataset.py
=========================
Genera un dataset de evaluación de RETRIEVAL a partir de las leyes reales de la
base de datos. NO usa LLM: las preguntas se derivan de forma determinística de
los campos de cada ley, y la "respuesta correcta" es el id de esa ley.

Cada caso de evaluación es:
    {
        "question": "<pregunta en lenguaje natural>",
        "expected_doc_id": "<id de la ley que debería recuperarse>",
        "numero_norma": "<nº de ley, para leer el reporte>",
        "kind": "<de qué campo se derivó la pregunta>"
    }

Con esto podemos medir, para cada pregunta, si el buscador trae el fragmento de
la ley correcta entre los primeros K resultados (Hit@K) y en qué posición (MRR).

Uso:
    cd DipuBot/etl
    python -m eval.build_dataset            # usa la BD por defecto
    python -m eval.build_dataset --db <ruta_sqlite> --out eval/eval_dataset.json
"""

import argparse
import json
import os
import sqlite3
import unicodedata
from pathlib import Path
from typing import List, Dict, Any


# Base por defecto: la MISMA con la que se construye el índice RAG (ver
# etl/.env -> DATABASE_PATH). El dataset de evaluación debe salir de la misma
# base que el índice, o las métricas no tienen sentido.
DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "raw" / "leyes-2015-2025_12_20.sqlite3"
DEFAULT_OUT = Path(__file__).resolve().parent / "eval_dataset.json"


def _clean(text: str) -> str:
    """Normaliza espacios/acentos para armar una pregunta legible."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.split()).strip()


def _titlecase(text: str) -> str:
    """Pasa un texto EN MAYÚSCULAS a una forma más natural para una pregunta."""
    cleaned = _clean(text)
    # Muchos títulos vienen en MAYÚSCULAS; los bajamos para que la pregunta
    # se parezca a algo que escribiría un usuario real.
    if cleaned.isupper():
        return cleaned.capitalize()
    return cleaned


def build_cases(db_path: str) -> List[Dict[str, Any]]:
    """Construye los casos de evaluación desde la base de datos."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT id, numero_norma, titulo_sumario, titulo_resumido, texto_resumido "
        "FROM leyes "
        "WHERE texto_original IS NOT NULL AND texto_original != ''"
    )
    rows = cur.fetchall()
    conn.close()

    cases: List[Dict[str, Any]] = []
    for r in rows:
        doc_id = str(r["id"])
        numero = r["numero_norma"]
        sumario = _clean(r["titulo_sumario"] or "")
        resumen = _clean(r["texto_resumido"] or "")

        # Pregunta 1: temática, a partir del título del sumario (el "tema" de la ley).
        # Es la consulta más típica de un usuario: "¿qué dice la ley sobre X?".
        # OJO: solo si el sumario es lo bastante específico. Sumarios genéricos de
        # una sola palabra ("TRATADOS", "ACUERDOS") los comparten MUCHAS leyes
        # distintas, así que la pregunta sería AMBIGUA (imposible saber cuál se
        # pide) y ensuciaría la métrica. Esos casos se descartan más abajo.
        if sumario and len(sumario.split()) >= 2:
            tema = _titlecase(sumario)
            cases.append({
                "question": f"¿Qué dice la ley sobre {tema}?",
                "expected_doc_id": doc_id,
                "numero_norma": numero,
                "kind": "tema_sumario",
            })

        # Pregunta 2: por el objeto/resumen de la ley (parafraseo de qué hace).
        # Da una consulta distinta apuntando a la MISMA ley (robustez del retriever).
        if resumen and len(resumen) > 25:
            objeto = _titlecase(resumen)
            # Recortamos para que sea una consulta, no un párrafo entero.
            objeto_corto = objeto[:140].rsplit(" ", 1)[0]
            cases.append({
                "question": f"¿Existe alguna ley relacionada con: {objeto_corto}?",
                "expected_doc_id": doc_id,
                "numero_norma": numero,
                "kind": "objeto_resumen",
            })

    # Filtro final de AMBIGÜEDAD: si una misma pregunta quedó asociada a más de
    # una ley (distintas leyes con respuesta esperada distinta), es imposible de
    # contestar bien y NO mide calidad del buscador. La quitamos del dataset.
    from collections import Counter
    question_counts = Counter(c["question"] for c in cases)
    unambiguous = [c for c in cases if question_counts[c["question"]] == 1]

    removed = len(cases) - len(unambiguous)
    if removed:
        print(f"[filtro] Se descartaron {removed} preguntas ambiguas "
              f"(compartidas por varias leyes).")

    return unambiguous


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera dataset de evaluación de retrieval.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Ruta a la base SQLite de leyes.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Archivo JSON de salida.")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        raise FileNotFoundError(f"No se encontró la base de datos: {args.db}")

    cases = build_cases(args.db)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)

    n_leyes = len({c["expected_doc_id"] for c in cases})
    print(f"Dataset generado: {len(cases)} preguntas sobre {n_leyes} leyes")
    print(f"Guardado en: {out_path}")
    # Muestra un par de ejemplos.
    for c in cases[:4]:
        print(f"  [{c['kind']}] ley {c['numero_norma']}: {c['question']}")


if __name__ == "__main__":
    main()
