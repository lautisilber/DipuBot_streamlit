"""
etl/eval/compare.py
==================
Compara dos archivos de resultados de evaluación (ANTES vs DESPUÉS) y muestra
la mejora en Hit@K y MRR, más qué preguntas pasaron de fallar a acertar (y
viceversa).

Uso:
    cd DipuBot/etl
    python -m eval.compare eval/results/eval_baseline_*.json eval/results/eval_mejorado_*.json
"""

import argparse
import glob
import json
from typing import Dict, Any


def _load(path_glob: str) -> Dict[str, Any]:
    matches = sorted(glob.glob(path_glob))
    if not matches:
        raise FileNotFoundError(f"No se encontró ningún archivo con: {path_glob}")
    with open(matches[-1], "r", encoding="utf-8") as f:
        data = json.load(f)
    data["_path"] = matches[-1]
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara dos resultados de evaluación.")
    parser.add_argument("before", help="Archivo (o glob) de resultados ANTES.")
    parser.add_argument("after", help="Archivo (o glob) de resultados DESPUÉS.")
    args = parser.parse_args()

    before = _load(args.before)
    after = _load(args.after)

    print("=" * 64)
    print("COMPARACIÓN DE EVALUACIÓN (retrieval)")
    print("=" * 64)
    print(f"ANTES:   {before['index_name']}  (K={before['k']}, n={before['n_cases']})")
    print(f"DESPUÉS: {after['index_name']}  (K={after['k']}, n={after['n_cases']})")
    print("-" * 64)

    d_hit = after["hit_at_k"] - before["hit_at_k"]
    d_mrr = after["mrr"] - before["mrr"]
    arrow = lambda d: "▲" if d > 0 else ("▼" if d < 0 else "=")
    print(f"Hit@{before['k']}:  {before['hit_at_k']:.1%}  ->  {after['hit_at_k']:.1%}   "
          f"{arrow(d_hit)} {d_hit:+.1%}")
    print(f"MRR:     {before['mrr']:.3f}  ->  {after['mrr']:.3f}   {arrow(d_mrr)} {d_mrr:+.3f}")
    print("-" * 64)

    # Alineamos por POSICIÓN (mismo dataset, mismo orden). No por texto de la
    # pregunta: puede haber preguntas repetidas y romper la cuenta.
    bc = before["per_case"]
    ac = after["per_case"]
    if len(bc) != len(ac):
        print("⚠️  Los dos resultados tienen distinta cantidad de casos; "
              "¿se corrieron con el mismo dataset?")

    fixed, broke, rank_up, rank_down = [], [], 0, 0
    for cb, ca in zip(bc, ac):
        rb, ra = cb["rank"], ca["rank"]
        if rb is None and ra is not None:
            fixed.append((cb, ca))
        elif rb is not None and ra is None:
            broke.append((cb, ca))
        elif rb is not None and ra is not None:
            if ra < rb:
                rank_up += 1
            elif ra > rb:
                rank_down += 1

    print(f"Preguntas que ANTES fallaban y ahora ACIERTAN: {len(fixed)}")
    for cb, ca in fixed[:10]:
        print(f"  + ley {cb['numero_norma']}: {cb['question'][:70]}  (ahora rank {ca['rank']})")
    print(f"Preguntas que ANTES acertaban y ahora FALLAN:  {len(broke)}")
    for cb, ca in broke[:10]:
        print(f"  - ley {cb['numero_norma']}: {cb['question'][:70]}  (antes rank {cb['rank']})")
    print(f"Entre las que aciertan en ambos: subieron de puesto {rank_up}, "
          f"bajaron {rank_down}.")
    print("=" * 64)


if __name__ == "__main__":
    main()
