"""
chat/rag.py
===========
Lógica de RAG usando FAISS: carga índice, busca chunks similares,
y genera respuestas con OpenAI GPT.

Uso desde Streamlit:
    from chat.rag import initialize_rag, query
    initialize_rag()
    response, sources = query("¿Qué dice el artículo 14 bis?")
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv

from chat.config import (
    find_latest_index,
    validate_index_exists,
    SIMILARITY_TOP_K,
    LLM_MODEL,
    EMBED_MODEL,
    PROJECT_ROOT,
)

# Path a la base de datos SQLite con el texto completo
DB_PATH = PROJECT_ROOT / "data" / "raw" / "leyes-2023-2025_12_20.sqlite3"

load_dotenv()


def get_full_text(doc_id: int) -> str:
    """
    Obtiene el texto completo de una ley desde SQLite.
    
    Args:
        doc_id: ID del documento en la base de datos
    
    Returns:
        Texto completo de la ley
    """
    if not DB_PATH.exists():
        return ""
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT texto_original FROM leyes WHERE id = ?",
        (doc_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else ""


# === Cache global (singleton) ===
_faiss_index: Optional[faiss.IndexFlatL2] = None
_metadata: Optional[Dict] = None
_openai_client: Optional[OpenAI] = None


def _get_openai_client() -> OpenAI:
    """Obtiene cliente OpenAI (con cache)."""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY no configurada. "
                "Agregala a tu archivo .env"
            )
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def load_index() -> Tuple[faiss.IndexFlatL2, Dict]:
    """
    Carga índice FAISS y metadata desde disco.
    
    Returns:
        Tuple de (índice FAISS, diccionario de metadata)
    
    Raises:
        FileNotFoundError si no existe el índice
    """
    index_path, metadata_path = find_latest_index()
    
    if index_path is None or metadata_path is None:
        raise FileNotFoundError(
            "No se encontró ningún índice FAISS en data/indexed/. "
            "Ejecutá 'cd etl && python3 run_etl.py' primero."
        )
    
    # Cargar índice FAISS
    index = faiss.read_index(str(index_path))
    
    # Cargar metadata
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    return index, metadata


def initialize_rag() -> None:
    """
    Inicializa el RAG cargando el índice en memoria.
    Llamar una vez al inicio de la aplicación.
    """
    global _faiss_index, _metadata
    
    if _faiss_index is not None:
        return  # Ya inicializado
    
    _faiss_index, _metadata = load_index()


def search(question: str, top_k: int = SIMILARITY_TOP_K) -> List[Dict[str, Any]]:
    """
    Busca los chunks más similares a la pregunta.
    
    Args:
        question: pregunta del usuario
        top_k: cantidad de resultados a retornar
    
    Returns:
        Lista de diccionarios con info de cada chunk encontrado
    """
    global _faiss_index, _metadata
    
    if _faiss_index is None or _metadata is None:
        initialize_rag()
    
    client = _get_openai_client()
    
    # Generar embedding de la pregunta
    response = client.embeddings.create(
        input=[question],
        model=EMBED_MODEL
    )
    query_embedding = np.array([response.data[0].embedding], dtype=np.float32)
    
    # Buscar en FAISS
    distances, indices = _faiss_index.search(query_embedding, top_k)
    
    # Armar resultados
    results = []
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        if idx < 0:  # FAISS retorna -1 si no hay suficientes resultados
            continue
        
        doc_info = _metadata["documents"][idx]
        doc_id = doc_info["doc_id"]
        
        # Obtener texto completo desde SQLite (en lugar del preview truncado)
        full_text = get_full_text(doc_id)
        
        results.append({
            "rank": i + 1,
            "distance": float(dist),
            "doc_id": doc_id,
            "text": full_text if full_text else doc_info["text_preview"],
            "tipo_norma": doc_info["metadata"].get("tipo_norma"),
            "numero_norma": doc_info["metadata"].get("numero_norma"),
            "titulo_resumido": doc_info["metadata"].get("titulo_resumido"),
            "fecha_sancion": doc_info["metadata"].get("fecha_sancion"),
            "year": doc_info["metadata"].get("year"),
        })
    
    return results


def generate_response(question: str, context_chunks: List[Dict]) -> str:
    """
    Genera una respuesta usando GPT con el contexto de los chunks.
    
    Args:
        question: pregunta del usuario
        context_chunks: lista de chunks relevantes encontrados
    
    Returns:
        Respuesta generada por el LLM
    """
    client = _get_openai_client()
    
    # Armar el contexto con los chunks
    context_parts = []
    for chunk in context_chunks:
        source_info = f"{chunk['tipo_norma']} {chunk['numero_norma']}"
        if chunk.get('titulo_resumido'):
            source_info += f" - {chunk['titulo_resumido']}"
        context_parts.append(f"[{source_info}]\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # System prompt para el asistente legal
    system_prompt = """Sos un asistente legal especializado en legislación argentina. 
Tu rol es responder preguntas sobre leyes basándote ÚNICAMENTE en los fragmentos de texto legal que te proporciono como contexto.

Instrucciones:
- Respondé de manera clara y precisa
- Citá las leyes específicas cuando sea posible (ej: "Según la Ley 27.551...")
- Si la información en el contexto no es suficiente para responder, decilo claramente
- No inventes información que no esté en el contexto
- Usá un tono profesional pero accesible"""

    user_prompt = f"""Contexto legal:
{context}

---

Pregunta del usuario: {question}

Respondé basándote en el contexto proporcionado."""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,  # Bajo para respuestas más precisas
        #max_tokens=1000,
    )
    
    return response.choices[0].message.content


def query(question: str) -> Tuple[str, List[Dict]]:
    """
    Ejecuta el flujo completo de RAG: busca + genera respuesta.
    
    Args:
        question: pregunta del usuario
    
    Returns:
        Tuple de (respuesta generada, lista de fuentes usadas)
    """
    # Buscar chunks relevantes
    chunks = search(question)
    
    if not chunks:
        return "No encontré información relevante para tu consulta.", []
    
    # Generar respuesta con contexto
    response = generate_response(question, chunks)
    
    # Preparar fuentes para mostrar
    sources = [
        {
            "tipo": c["tipo_norma"],
            "numero": c["numero_norma"],
            "titulo": c.get("titulo_resumido", ""),
            "year": c.get("year"),
        }
        for c in chunks
    ]
    
    return response, sources


def reset_rag() -> None:
    """Resetea el cache del RAG (útil para recargar)."""
    global _faiss_index, _metadata, _openai_client
    _faiss_index = None
    _metadata = None
    _openai_client = None
