"""
etl/eval/run_eval.py
====================
Evalúa la calidad del RETRIEVAL de un índice contra el dataset de evaluación.

Para cada pregunta del dataset, busca en el índice y comprueba si el fragmento
de la ley correcta aparece entre los primeros K resultados. Reporta dos métricas
estándar de retrieval:

  - Hit@K : porcentaje de preguntas donde la ley correcta apareció en el top-K.
            (¿la encontró?)  -> más alto es mejor.
  - MRR   : Mean Reciprocal Rank. Premia que la ley correcta aparezca ARRIBA.
            Si sale 1º -> 1.0 ; 2º -> 0.5 ; 3º -> 0.33 ; no aparece -> 0.
            (¿qué tan arriba la puso?) -> más alto es mejor.

Guarda el resultado en JSON para poder comparar ANTES vs DESPUÉS de reconstruir
el índice (fases 1-3).

Uso:
    cd DipuBot/etl
    # Evalúa el índice más reciente:
    python -m eval.run_eval
    # Evalúa un índice específico (para comparar):
    python -m eval.run_eval --index ../data/indexed/llama_index_20260112_203029
    # Cambiar K o guardar con etiqueta:
    python -m eval.run_eval --k 5 --label baseline
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

# Permitir importar el paquete chat del proyecto (../.. respecto de este archivo).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore

load_dotenv()

DEFAULT_DATASET = Path(__file__).resolve().parent / "eval_dataset.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
EMBED_MODEL = os.getenv("EMBED_MODEL", os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
INDEXED_DIR = PROJECT_ROOT / "data" / "indexed"


def find_latest_index() -> Optional[Path]:
    """Encuentra el índice LlamaIndex más reciente (misma lógica que chat/config)."""
    if not INDEXED_DIR.exists():
        return None
    dirs = sorted(
        [d for d in INDEXED_DIR.iterdir() if d.is_dir() and d.name.startswith("llama_index_")],
        reverse=True,
    )
    for d in dirs:
        required = ["default__vector_store.json", "docstore.json", "index_store.json"]
        if all((d / f).exists() for f in required):
            return d
    return None


def load_index(index_dir: Path):
    """Carga un índice LlamaIndex desde un directorio (con FAISS)."""
    embed_model = OpenAIEmbedding(model=EMBED_MODEL, api_key=os.getenv("OPENAI_API_KEY"))
    Settings.embed_model = embed_model
    vector_store = FaissVectorStore.from_persist_dir(persist_dir=str(index_dir))
    storage_context = StorageContext.from_defaults(
        persist_dir=str(index_dir), vector_store=vector_store
    )
    return load_index_from_storage(storage_context)


def retrieved_doc_ids(index, question: str, k: int) -> List[str]:
    """Devuelve los doc_id (ids de ley) recuperados para una pregunta, en orden."""
    retriever = index.as_retriever(similarity_top_k=k)
    nodes = retriever.retrieve(question)
    ids = []
    for nws in nodes:
        node = nws.node
        meta = node.metadata or {}
        doc_id = meta.get("doc_id") or node.ref_doc_id
        ids.append(str(doc_id) if doc_id is not None else None)
    return ids


def evaluate(index, cases: List[Dict[str, Any]], k: int) -> Dict[str, Any]:
    """Corre la evaluación y calcula Hit@K y MRR."""
    hits = 0
    reciprocal_ranks = 0.0
    per_case = []

    for i, case in enumerate(cases, 1):
        q = case["question"]
        expected = str(case["expected_doc_id"])
        got = retrieved_doc_ids(index, q, k)

        rank = None
        for pos, doc_id in enumerate(got, 1):
            if doc_id == expected:
                rank = pos
                break

        if rank is not None:
            hits += 1
            reciprocal_ranks += 1.0 / rank

        per_case.append({
            "question": q,
            "numero_norma": case.get("numero_norma"),
            "kind": case.get("kind"),
            "expected_doc_id": expected,
            "retrieved_doc_ids": got,
            "rank": rank,  # None = no apareció en el top-K
        })

        # Progreso simple en consola.
        status = f"rank={rank}" if rank else "MISS"
        print(f"  [{i}/{len(cases)}] ley {case.get('numero_norma')}: {status}")

    n = len(cases)
    return {
        "n_cases": n,
        "k": k,
        "hit_at_k": hits / n if n else 0.0,
        "mrr": reciprocal_ranks / n if n else 0.0,
        "hits": hits,
        "per_case": per_case,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalúa el retrieval de un índice.")
    parser.add_argument("--index", default=None,
                        help="Directorio del índice a evaluar. Por defecto: el más reciente.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET),
                        help="Dataset de evaluación (JSON).")
    parser.add_argument("--k", type=int, default=5, help="Top-K a evaluar (default 5).")
    parser.add_argument("--label", default=None,
                        help="Etiqueta para el archivo de resultados (ej: baseline / mejorado).")
    args = parser.parse_args()

    if not os.path.exists(args.dataset):
        raise FileNotFoundError(
            f"No se encontró el dataset: {args.dataset}. "
            f"Generalo primero con: python -m eval.build_dataset"
        )

    index_dir = Path(args.index) if args.index else find_latest_index()
    if index_dir is None or not index_dir.exists():
        raise FileNotFoundError(
            "No se encontró un índice para evaluar. "
            "Construí uno con: python run_etl.py"
        )

    with open(args.dataset, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print("=" * 60)
    print("EVALUACIÓN DE RETRIEVAL")
    print("=" * 60)
    print(f"Índice:  {index_dir.name}")
    print(f"Dataset: {len(cases)} preguntas | K={args.k} | embeddings={EMBED_MODEL}")
    print("-" * 60)

    index = load_index(index_dir)
    result = evaluate(index, cases, args.k)

    print("-" * 60)
    print(f"Hit@{args.k}: {result['hit_at_k']:.1%}  ({result['hits']}/{result['n_cases']})")
    print(f"MRR:     {result['mrr']:.3f}")
    print("=" * 60)

    # Guardar resultados.
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = f"_{args.label}" if args.label else ""
    out = RESULTS_DIR / f"eval{label}_{ts}.json"
    payload = {
        "index_dir": str(index_dir),
        "index_name": index_dir.name,
        "embed_model": EMBED_MODEL,
        "created_at": datetime.now().isoformat(),
        "hit_at_k": result["hit_at_k"],
        "mrr": result["mrr"],
        "k": result["k"],
        "n_cases": result["n_cases"],
        "hits": result["hits"],
        "per_case": result["per_case"],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Resultados guardados en: {out}")


if __name__ == "__main__":
    main()
