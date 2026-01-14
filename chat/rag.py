"""
chat/rag.py
===========
Lógica de RAG usando LlamaIndex: carga índice, busca chunks similares,
y genera respuestas con OpenAI GPT.

Uso desde Streamlit:
    from chat.rag import initialize_rag, query
    initialize_rag()
    response, sources = query("¿Qué dice el artículo 14 bis?")
"""

import os
import sys
# import sqlite3  # Comentado: ya no se usa SQLite, los nodes de LlamaIndex tienen el texto completo
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Configurar encoding UTF-8 explícitamente para evitar problemas de codificación
# Útil cuando LlamaIndex lee archivos JSON con caracteres especiales
if sys.getdefaultencoding() != 'utf-8':
    import io
    # Reconfigurar stdout/stderr para UTF-8
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from openai import OpenAI
from dotenv import load_dotenv
import tiktoken

from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage, Settings
from llama_index.embeddings.openai import OpenAIEmbedding

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
# DB_PATH = PROJECT_ROOT / "data" / "raw" / "leyes-2023-2025_12_20.sqlite3"

load_dotenv()


# def get_full_text(doc_id: int) -> str:
#     """
#     Obtiene el texto completo de una ley desde SQLite.
#     
#     Args:
#         doc_id: ID del documento en la base de datos
#     
#     Returns:
#         Texto completo de la ley
#     """
#     if not DB_PATH.exists():
#         return ""
#     
#     conn = sqlite3.connect(str(DB_PATH))
#     cursor = conn.cursor()
#     cursor.execute(
#         "SELECT texto_original FROM leyes WHERE id = ?",
#         (doc_id,)
#     )
#     result = cursor.fetchone()
#     conn.close()
#     
#     return result[0] if result else ""


# === Cache global (singleton) ===
_llama_index: Optional[VectorStoreIndex] = None
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


def load_index() -> VectorStoreIndex:
    """
    Carga índice LlamaIndex desde disco.
    
    Returns:
        VectorStoreIndex de LlamaIndex
    
    Raises:
        FileNotFoundError si no existe el índice
        UnicodeDecodeError si hay problemas de codificación
    """
    from llama_index.vector_stores.faiss import FaissVectorStore
    
    index_dir = find_latest_index()
    
    if index_dir is None:
        raise FileNotFoundError(
            "No se encontró ningún índice LlamaIndex en data/indexed/. "
            "Ejecutá 'cd etl && python3 run_etl.py' primero."
        )
    
    try:
        # Configurar embedding model (debe ser el mismo que se usó para crear el índice)
        embed_model = OpenAIEmbedding(
            model=EMBED_MODEL,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        Settings.embed_model = embed_model
        
        # SOLUCIÓN AL ERROR DE ENCODING:
        # El archivo default__vector_store.json contiene datos binarios de FAISS,
        # no JSON en formato UTF-8. Debemos usar FaissVectorStore.from_persist_dir()
        # que internamente usa faiss.read_index() para leer el archivo binario correctamente.
        
        # 1. Cargar FAISS vector store (maneja datos binarios correctamente)
        vector_store = FaissVectorStore.from_persist_dir(persist_dir=str(index_dir))
        
        # 2. Cargar otros componentes de storage (docstore, index_store)
        #    Pasamos el vector_store ya cargado para evitar que intente parsearlo como JSON
        storage_context = StorageContext.from_defaults(
            persist_dir=str(index_dir),
            vector_store=vector_store
        )
        
        # 3. Cargar índice desde storage
        index = load_index_from_storage(storage_context)
        
        return index
    
    except Exception as e:
        # Capturar otros errores y dar contexto
        raise RuntimeError(
            f"Error al cargar índice desde {index_dir}: {str(e)}\n"
            f"Tipo de error: {type(e).__name__}\n"
        ) from e


def initialize_rag() -> None:
    """
    Inicializa el RAG cargando el índice en memoria.
    Llamar una vez al inicio de la aplicación.
    """
    global _llama_index
    
    if _llama_index is not None:
        return  # Ya inicializado
    
    _llama_index = load_index()


def search(question: str, top_k: int = SIMILARITY_TOP_K) -> List[Dict[str, Any]]:
    """
    Busca los chunks más similares a la pregunta usando LlamaIndex.
    
    Args:
        question: pregunta del usuario
        top_k: cantidad de resultados a retornar
    
    Returns:
        Lista de diccionarios con info de cada chunk encontrado
    """
    global _llama_index
    
    if _llama_index is None:
        initialize_rag()
    
    # Usar retriever de LlamaIndex
    retriever = _llama_index.as_retriever(similarity_top_k=top_k)
    nodes_with_scores = retriever.retrieve(question)
    
    # Armar resultados en el formato esperado
    results = []
    for i, node_with_score in enumerate(nodes_with_scores):
        node = node_with_score.node
        score = node_with_score.score
        
        # Extraer metadata del node
        metadata = node.metadata or {}
        
        # Obtener doc_id (puede estar en metadata o en node.ref_doc_id)
        doc_id = metadata.get("doc_id") or node.ref_doc_id
        
        # Los nodes de LlamaIndex ya tienen el texto del chunk, no deberíamos necesitar SQLite
        text = node.text
        
        # Si en el futuro necesitamos el texto completo de la ley (no solo el chunk),
        # podemos descomentar esto
        # full_text = ""
        # if doc_id:
        #     try:
        #         doc_id_int = int(doc_id) if isinstance(doc_id, str) else doc_id
        #         full_text = get_full_text(doc_id_int)
        #     except (ValueError, TypeError):
        #         pass
        # text = full_text if full_text else node.text
        
        results.append({
            "rank": i + 1,
            "distance": float(score) if score is not None else None,
            "doc_id": doc_id,
            "text": text,
            "tipo_norma": metadata.get("tipo_norma"),
            "numero_norma": metadata.get("numero_norma"),
            "titulo_resumido": metadata.get("titulo_resumido"),
            "fecha_sancion": metadata.get("fecha_sancion"),
            "year": metadata.get("year"),
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
    global _llama_index, _openai_client
    _llama_index = None
    _openai_client = None
