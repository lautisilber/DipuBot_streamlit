"""
etl/eval/run_eval_rerank.py
===========================
Igual que `run_eval.py`, pero aplicando el RERANKING real del RAG (Fase 8)
antes de calcular las métricas. Sirve para medir el efecto del cross-encoder
sobre el corpus, de forma consistente con lo que corre en producción
(`chat/skills/rag_skill.py::rerank`).

Pipeline por pregunta:
  1. FAISS trae `RAG_RERANK_CANDIDATES` candidatos (más que K).
  2. Se rerankean con el cross-encoder (BAAI/bge-reranker-base) usando
     título + comienzo del texto, igual que en el chat.
  3. Se toman los top-K y se calcula Hit@K y MRR contra el doc_id esperado.

Uso:
    cd DipuBot/etl
    python -m eval.run_eval_rerank --k 5 --label grande_2952_rerank
    python -m eval.run_eval_rerank --index ../data/indexed/llama_index_YYYYMMDD_HHMMSS
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Reutilizamos toda la maquinaria de run_eval (carga de índice, dataset, etc.).
from eval.run_eval import (
    load_index, find_latest_index, DEFAULT_DATASET, RESULTS_DIR, EMBED_MODEL,
)

# La función de reranking REAL del RAG y sus parámetros de configuración.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
from chat.skills.rag_skill import rerank  # noqa: E402
from chat.config import RAG_RERANK_CANDIDATES  # noqa: E402


def retrieve_candidates(index, question: str, n: int) -> List[Dict[str, Any]]:
    """Trae `n` candidatos de FAISS como dicts compatibles con rerank()."""
    retriever = index.as_retriever(similarity_top_k=n)
    nodes = retriever.retrieve(question)
    chunks: List[Dict[str, Any]] = []
    for nws in nodes:
        node = nws.node
        meta = node.metadata or {}
        doc_id = meta.get("doc_id") or node.ref_doc_id
        chunks.append({
            "doc_id": str(doc_id) if doc_id is not None else None,
            "text": node.get_content() if hasattr(node, "get_content") else "",
            "titulo_resumido": meta.get("titulo_resumido", ""),
            "titulo_sumario": meta.get("titulo_sumario", ""),
            "score": nws.score,
        })
    return chunks


def evaluate_reranked(index, cases: List[Dict[str, Any]], k: int,
                      candidates: int) -> Dict[str, Any]:
    """Corre la evaluación aplicando reranking; calcula Hit@K y MRR."""
    hits = 0
    reciprocal_ranks = 0.0
    per_case = []

    for i, case in enumerate(cases, 1):
        q = case["question"]
        expected = str(case["expected_doc_id"])

        cands = retrieve_candidates(index, q, candidates)
        reranked = rerank(q, cands, top_k=k)
        got = [c.get("doc_id") for c in reranked]

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
            "rank": rank,
        })

        status = f"rank={rank}" if rank else "MISS"
        print(f"  [{i}/{len(cases)}] ley {case.get('numero_norma')}: {status}")

    n = len(cases)
    return {
        "n_cases": n,
        "k": k,
        "candidates": candidates,
        "reranked": True,
        "hit_at_k": hits / n if n else 0.0,
        "mrr": reciprocal_ranks / n if n else 0.0,
        "hits": hits,
        "per_case": per_case,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalúa el retrieval CON reranking.")
    parser.add_argument("--index", default=None)
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--candidates", type=int, default=RAG_RERANK_CANDIDATES,
                        help="Candidatos de FAISS a rerankear (default: config del RAG).")
    parser.add_argument("--label", default="rerank")
    args = parser.parse_args()

    if not os.path.exists(args.dataset):
        raise FileNotFoundError(f"No se encontró el dataset: {args.dataset}")

    index_dir = Path(args.index) if args.index else find_latest_index()
    if index_dir is None or not index_dir.exists():
        raise FileNotFoundError("No se encontró un índice para evaluar.")

    with open(args.dataset, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print("=" * 60)
    print("EVALUACIÓN DE RETRIEVAL (con reranking)")
    print("=" * 60)
    print(f"Índice:  {index_dir.name}")
    print(f"Dataset: {len(cases)} preguntas | K={args.k} | "
          f"candidatos={args.candidates} | embeddings={EMBED_MODEL}")
    print("-" * 60)

    index = load_index(index_dir)
    result = evaluate_reranked(index, cases, args.k, args.candidates)

    print("-" * 60)
    print(f"Hit@{args.k}: {result['hit_at_k']:.1%}  ({result['hits']}/{result['n_cases']})")
    print(f"MRR:     {result['mrr']:.3f}")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = RESULTS_DIR / f"eval_{args.label}_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Resultados guardados en: {out}")


if __name__ == "__main__":
    main()
