"""
Utilidad para verificar y consultar el índice FAISS creado.
"""

import os
import json
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
FAISS_OUTPUT_DIR = os.getenv("FAISS_OUTPUT_DIR", "../data/indexed")


def find_latest_index(output_dir: str = FAISS_OUTPUT_DIR) -> tuple[Optional[Path], Optional[Path]]:
    """Encuentra el índice FAISS más reciente."""
    script_dir = Path(__file__).parent
    output_path = (script_dir / output_dir).resolve()
    
    if not output_path.exists():
        return None, None
    
    # Buscar archivos .faiss ordenados por nombre (tienen timestamp)
    faiss_files = sorted(output_path.glob("*.faiss"), reverse=True)
    
    if not faiss_files:
        return None, None
    
    latest_index = faiss_files[0]
    latest_metadata = latest_index.with_suffix(".json").with_name(
        latest_index.stem.replace("_index_", "_metadata_") + ".json"
    )
    
    return latest_index, latest_metadata


def load_index_and_metadata(
    index_path: Optional[Path] = None,
    metadata_path: Optional[Path] = None
) -> tuple[faiss.IndexFlatL2, Dict]:
    """Carga índice FAISS y metadata."""
    if index_path is None or metadata_path is None:
        index_path, metadata_path = find_latest_index()
    
    if index_path is None:
        raise FileNotFoundError("No se encontró ningún índice FAISS")
    
    print(f"📂 Cargando índice: {index_path}")
    index = faiss.read_index(str(index_path))
    
    print(f"📂 Cargando metadata: {metadata_path}")
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    return index, metadata


def search(
    query: str,
    index: faiss.IndexFlatL2,
    metadata: Dict,
    client: OpenAI,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Busca documentos similares a la query.
    """
    # Generar embedding de la query
    response = client.embeddings.create(
        input=[query],
        model=EMBEDDING_MODEL
    )
    query_embedding = np.array([response.data[0].embedding], dtype=np.float32)
    
    # Buscar en FAISS
    distances, indices = index.search(query_embedding, k)
    
    # Armar resultados
    results = []
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        if idx < 0:  # FAISS retorna -1 si no hay suficientes resultados
            continue
        
        doc_info = metadata["documents"][idx]
        results.append({
            "rank": i + 1,
            "distance": float(dist),
            "doc_id": doc_info["doc_id"],
            "text_preview": doc_info["text_preview"],
            "tipo_norma": doc_info["metadata"].get("tipo_norma"),
            "numero_norma": doc_info["metadata"].get("numero_norma"),
            "titulo_resumido": doc_info["metadata"].get("titulo_resumido"),
            "fecha_sancion": doc_info["metadata"].get("fecha_sancion"),
            "year": doc_info["metadata"].get("year"),
        })
    
    return results


def interactive_search():
    """Modo interactivo para buscar en el índice."""
    print("=" * 60)
    print("🔍 Búsqueda Interactiva en Índice de Leyes")
    print("=" * 60)
    
    # Cargar índice
    index, metadata = load_index_and_metadata()
    print(f"✅ Índice cargado: {index.ntotal} vectores")
    print(f"📅 Creado: {metadata['created_at']}")
    
    # Cliente OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("\nEscribe tu consulta (o 'salir' para terminar):\n")
    
    while True:
        query = input("🔎 Query: ").strip()
        
        if query.lower() in ["salir", "exit", "q"]:
            print("👋 ¡Hasta luego!")
            break
        
        if not query:
            continue
        
        results = search(query, index, metadata, client, k=5)
        
        print(f"\n📋 Top {len(results)} resultados:\n")
        for r in results:
            print(f"  [{r['rank']}] {r['tipo_norma']} {r['numero_norma']} (año {r['year']})")
            print(f"      📌 {r['titulo_resumido'][:80]}..." if r['titulo_resumido'] else "      📌 Sin título")
            print(f"      📏 Distancia: {r['distance']:.4f}")
            print()
        
        print("-" * 40)


def verify_index():
    """Verifica que el índice se creó correctamente."""
    print("=" * 60)
    print("🔧 Verificación de Índice FAISS")
    print("=" * 60)
    
    try:
        index, metadata = load_index_and_metadata()
        
        print(f"\n✅ Índice encontrado y cargado")
        print(f"   - Vectores: {index.ntotal}")
        print(f"   - Dimensiones: {index.d}")
        print(f"   - Creado: {metadata['created_at']}")
        print(f"   - Modelo: {metadata['embedding_model']}")
        print(f"   - Documentos: {metadata['total_documents']}")
        
        # Muestra algunos ejemplos
        print(f"\n📝 Primeros 3 documentos:")
        for doc in metadata["documents"][:3]:
            print(f"\n   ID: {doc['doc_id']}")
            print(f"   Tipo: {doc['metadata'].get('tipo_norma')}")
            print(f"   Número: {doc['metadata'].get('numero_norma')}")
            print(f"   Preview: {doc['text_preview'][:100]}...")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_index()
    else:
        interactive_search()
