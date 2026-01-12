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
import tiktoken

from chat.config import (
    find_latest_index,
    validate_index_exists,
    SIMILARITY_TOP_K,
    LLM_MODEL,
    EMBED_MODEL,
    PROJECT_ROOT,
    MAX_HISTORY_TOKENS,
    MAX_HISTORY_MESSAGES,
    get_model_limits,
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


def format_conversation_history(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Convierte mensajes de Streamlit al formato de OpenAI Chat API.
    
    Args:
        messages: Lista de mensajes del historial con formato:
            [{"role": "user"/"assistant", "content": "...", "sources": [...]}]
    
    Returns:
        Lista de mensajes en formato OpenAI:
            [{"role": "user"/"assistant", "content": "..."}]
    
    Nota: Las fuentes no se incluyen en el historial para evitar confusión
    con leyes no relevantes. El LLM puede inferir las leyes mencionadas
    desde el contenido del texto de la respuesta.
    """
    openai_messages = []
    for msg in messages:
        role = msg.get("role")
        if role not in ["user", "assistant"]:
            continue
        
        # Solo incluir el contenido del mensaje, sin agregar fuentes
        # Las fuentes se muestran en la UI pero no se incluyen en el contexto
        # para evitar confusión con leyes no relevantes en preguntas de seguimiento
        content = msg.get("content", "")
        
        openai_messages.append({"role": role, "content": content})
    
    return openai_messages


def count_tokens(text: str, model: str = LLM_MODEL) -> int:
    """
    Cuenta tokens aproximados en un texto usando tiktoken.
    
    Args:
        text: Texto a contar
        model: Modelo de OpenAI (para usar el encoding correcto)
    
    Returns:
        Número aproximado de tokens
    """
    try:
        # Obtener encoding para el modelo
        # La mayoría de modelos recientes usan cl100k_base
        # gpt-5.2 y modelos nuevos también usan cl100k_base
        if "gpt-4" in model or "gpt-3.5" in model or "gpt-5" in model or "o1" in model:
            encoding_name = "cl100k_base"
        else:
            encoding_name = "cl100k_base"  # Default para modelos recientes
        
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: estimación aproximada (1 token ≈ 4 caracteres)
        return len(text) // 4


def estimate_chunks_tokens(context_chunks: List[Dict]) -> int:
    """
    Estima el número de tokens en los chunks de contexto.
    
    Args:
        context_chunks: Lista de chunks con texto completo
    
    Returns:
        Número estimado de tokens
    """
    total_text = ""
    for chunk in context_chunks:
        total_text += chunk.get("text", "")
        # También contar el formato del source_info
        source_info = f"{chunk.get('tipo_norma', '')} {chunk.get('numero_norma', '')}"
        if chunk.get('titulo_resumido'):
            source_info += f" - {chunk.get('titulo_resumido', '')}"
        total_text += f"[{source_info}]\n"
    
    return count_tokens(total_text)


def truncate_history_by_tokens(
    messages: List[Dict[str, Any]], 
    max_tokens: int,
    model: str = LLM_MODEL
) -> List[Dict[str, Any]]:
    """
    Trunca historial basándose en tokens reales, manteniendo los mensajes más recientes.
    
    Args:
        messages: Lista de mensajes del historial
        max_tokens: Número máximo de tokens para el historial
        model: Modelo de OpenAI (para contar tokens correctamente)
    
    Returns:
        Lista truncada de mensajes que no excede max_tokens
    """
    if not messages or max_tokens <= 0:
        return []
    
    # Filtrar mensajes válidos y crear mapeo
    valid_messages = []
    message_map = []  # Índice en valid_messages -> índice original en messages
    
    for i, msg in enumerate(messages):
        role = msg.get("role")
        if role in ["user", "assistant"]:
            valid_messages.append(msg)
            message_map.append(i)
    
    if not valid_messages:
        return []
    
    # Convertir a formato OpenAI para contar tokens
    formatted = format_conversation_history(valid_messages)
    
    # Contar tokens desde el final (mensajes más recientes)
    total_tokens = 0
    kept_indices = []
    
    # Iterar desde el final hacia atrás
    for i in range(len(formatted) - 1, -1, -1):
        msg = formatted[i]
        # Contar tokens del mensaje (incluyendo el overhead del formato)
        msg_content = msg["content"]
        msg_tokens = count_tokens(msg_content, model)
        # Agregar overhead aproximado por mensaje (role + formato)
        overhead = 10  # Aproximado para el formato del mensaje
        msg_total = msg_tokens + overhead
        
        if total_tokens + msg_total <= max_tokens:
            kept_indices.insert(0, i)  # Insertar al inicio para mantener orden
            total_tokens += msg_total
        else:
            break  # No caben más mensajes
    
    # Retornar los mensajes originales correspondientes a los índices mantenidos
    if not kept_indices:
        return []
    
    # Mapear de vuelta a los mensajes originales usando message_map
    result = []
    for idx in kept_indices:
        original_idx = message_map[idx]
        result.append(messages[original_idx])
    
    return result


def truncate_history(messages: List[Dict[str, Any]], max_messages: int = MAX_HISTORY_MESSAGES) -> List[Dict[str, Any]]:
    """
    Trunca historial si es muy largo, manteniendo los mensajes más recientes.
    Función de fallback cuando no se puede contar tokens.
    
    Args:
        messages: Lista de mensajes del historial
        max_messages: Número máximo de mensajes a mantener
    
    Returns:
        Lista truncada de mensajes (últimos N mensajes)
    """
    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages


def generate_response(question: str, context_chunks: List[Dict], conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Genera una respuesta usando GPT con el contexto de los chunks y el historial conversacional
    con truncamiento por tokens.
    
    Args:
        question: pregunta del usuario
        context_chunks: lista de chunks relevantes encontrados
        conversation_history: historial de mensajes previos (opcional)
    
    Returns:
        Respuesta generada por el LLM
    """
    client = _get_openai_client()
    
    # Obtener límites del modelo actual
    model_limits = get_model_limits(LLM_MODEL)
    context_window = model_limits["context_window"]
    reserved_tokens = model_limits["reserved_tokens"]
    
    # Armar el contexto con los chunks
    context_parts = []
    for chunk in context_chunks:
        source_info = f"{chunk['tipo_norma']} {chunk['numero_norma']}"
        if chunk.get('titulo_resumido'):
            source_info += f" - {chunk['titulo_resumido']}"
        context_parts.append(f"[{source_info}]\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # Estimar tokens de chunks
    chunks_tokens = estimate_chunks_tokens(context_chunks)
    
    # System prompt para el asistente legal
    system_prompt = """Sos un asistente legal especializado en legislación argentina. 
Tenés acceso a dos fuentes de información para responder:

1. CONTEXTO ACTUAL: Fragmentos de texto legal que te proporciono ahora (leyes encontradas para esta pregunta)
2. HISTORIAL CONVERSACIONAL: Mensajes previos de nuestra conversación (preguntas y respuestas anteriores)

CÓMO DECIDIR QUÉ USAR:

- Si la pregunta es NUEVA o busca información sobre leyes NO mencionadas antes:
  → Usá PRINCIPALMENTE el contexto actual (fragmentos de leyes proporcionados)
  → El historial puede ayudar para contexto general, pero el contexto actual tiene prioridad

- Si la pregunta es de SEGUIMIENTO o hace referencia a algo ya mencionado:
  → Usá el HISTORIAL para entender a qué se refiere (ej: "esa ley", "la ley anterior", "¿cuándo se sancionó?")
  → Combiná el historial con el contexto actual si es necesario
  → Si la pregunta es sobre detalles de una ley ya mencionada, el historial puede ser suficiente

Ejemplos de preguntas de seguimiento que requieren historial:
- "¿Y cuándo se sancionó?" (se refiere a una ley mencionada antes)
- "¿Qué dice el artículo 3 de esa ley?" (se refiere a una ley del historial)
- "Compará ambas leyes" (se refiere a leyes mencionadas previamente)
- "¿Y qué pasó con la otra?" (referencia a conversación previa)

Instrucciones generales:
- Respondé de manera clara y precisa
- Citá las leyes específicas cuando sea posible (ej: "Según la Ley 27.551...")
- El historial tiene prioridad para entender referencias y contexto conversacional
- Si la información disponible no es suficiente para responder, decilo claramente
- Se cuidadoso en decir que una ley no está en los documentos proporcionados, puede ser que no la encuentres nada más
- Si el usuario pregunta por las leyes de la conversación actual, fijate que haya un mensaje del historial donde el usuario o tú la mencionaron
- No inventes información legal que no esté en el contexto actual, es deccir, los fragmentos de texto legal proporcionados
- Usá un tono profesional pero accesible"""
    
    system_prompt_tokens = count_tokens(system_prompt, LLM_MODEL)
    
    # Preparar user prompt para estimar tokens
    # Nota: El historial se incluye como mensajes separados antes de este prompt
    user_prompt_template = """CONTEXTO LEGAL ACTUAL (leyes encontradas para esta pregunta):
{context}

---

Pregunta del usuario: {question}

Analizá la pregunta y decidí:
1. ¿Es una pregunta nueva o de seguimiento?
2. ¿Qué información necesitás del contexto actual vs del historial?
Al usuario solo le interesa que le respondas usando la información más relevante. No le digas al usuario si la pregunta es nueva o de seguimiento, solo responde."""
    
    user_prompt_base = user_prompt_template.format(context="", question=question)
    user_prompt_base_tokens = count_tokens(user_prompt_base, LLM_MODEL)
    
    # Estimar tokens de la respuesta (max_tokens que pediremos)
    response_tokens_estimate = 1000
    
    # Calcular tokens disponibles para historial
    # context_window - reserved - chunks - system - user_base - response_estimate - margen_seguridad
    margin = 1000  # Margen de seguridad para overhead y variaciones
    available_for_history = (
        context_window
        - reserved_tokens
        - chunks_tokens
        - system_prompt_tokens
        - user_prompt_base_tokens
        - response_tokens_estimate
        - margin
    )
    
    # Asegurar mínimo razonable (al menos espacio para 2-3 mensajes cortos)
    # Si no hay espacio, usar fallback por número de mensajes
    max_history_tokens = max(available_for_history, 500) if available_for_history > 0 else 0
    
    # Construir lista de mensajes para OpenAI
    messages = [{"role": "system", "content": system_prompt}]
    
    # Agregar historial conversacional si existe
    has_history = False
    if conversation_history:
        if max_history_tokens > 0:
            # Truncar por tokens reales
            truncated_history = truncate_history_by_tokens(
                conversation_history,
                max_tokens=max_history_tokens,
                model=LLM_MODEL
            )
        else:
            # Fallback: truncar por número de mensajes si no hay espacio
            truncated_history = truncate_history(conversation_history, max_messages=MAX_HISTORY_MESSAGES)
        
        if truncated_history:
            # Convertir al formato de OpenAI
            formatted_history = format_conversation_history(truncated_history)
            messages.extend(formatted_history)
            has_history = True
    
    # Agregar la pregunta actual con contexto de chunks
    # Si hay historial, agregar una nota para que el modelo sepa que está disponible
    if has_history:
        history_note = "\n\nNOTA: Hay un historial conversacional disponible arriba. Usalo para entender referencias a leyes mencionadas previamente."
    else:
        history_note = ""
    
    user_prompt = user_prompt_template.format(context=context, question=question) + history_note
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,  # Bajo para respuestas más precisas
        #max_completion_tokens=1000,
    )
    
    return response.choices[0].message.content


def query(question: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, List[Dict]]:
    """
    Ejecuta el flujo completo de RAG: busca + genera respuesta.
    
    Args:
        question: pregunta del usuario
        conversation_history: historial de mensajes previos (opcional)
            Formato: [{"role": "user"/"assistant", "content": "...", "sources": [...]}]
    
    Returns:
        Tuple de (respuesta generada, lista de fuentes usadas)
    """
    # Buscar chunks relevantes
    chunks = search(question)
    
    if not chunks:
        return "No encontré información relevante para tu consulta.", []
    
    # Generar respuesta con contexto e historial
    response = generate_response(question, chunks, conversation_history)
    
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
