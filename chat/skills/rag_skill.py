"""
chat/skills/rag_skill.py
========================
RAG skill for answering questions about Argentine legislation.
Lógica completa de RAG usando LlamaIndex: carga índice, busca chunks similares,
y genera respuestas con OpenAI GPT.
"""

import os
import sys
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Configurar encoding UTF-8 explícitamente para evitar problemas de codificación
if sys.getdefaultencoding() != 'utf-8':
    import io
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
    RAG_MIN_CHUNKS,
    RAG_MIN_SIMILARITY_SCORE,
    RAG_WIDER_SEARCH_MULTIPLIER,
    RAG_ENABLE_LLM_CHECK,
    RAG_ENABLE_QUERY_REWRITING,
    RAG_REWRITING_MIN_QUERY_LENGTH,
)
from chat.skills.base import BaseSkill, SkillResult

load_dotenv()


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
        embed_model = OpenAIEmbedding(
            model=EMBED_MODEL,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        Settings.embed_model = embed_model
        
        vector_store = FaissVectorStore.from_persist_dir(persist_dir=str(index_dir))
        
        storage_context = StorageContext.from_defaults(
            persist_dir=str(index_dir),
            vector_store=vector_store
        )
        
        index = load_index_from_storage(storage_context)
        
        return index
    
    except Exception as e:
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
    
    retriever = _llama_index.as_retriever(similarity_top_k=top_k)
    nodes_with_scores = retriever.retrieve(question)
    
    results = []
    for i, node_with_score in enumerate(nodes_with_scores):
        node = node_with_score.node
        score = node_with_score.score
        
        metadata = node.metadata or {}
        doc_id = metadata.get("doc_id") or node.ref_doc_id
        text = node.text
        
        results.append({
            "rank": i + 1,
            "distance": float(score) if score is not None else None,
            "doc_id": doc_id,
            "text": text,
            "tipo_norma": metadata.get("tipo_norma"),
            "numero_norma": metadata.get("numero_norma"),
            "titulo_resumido": metadata.get("titulo_resumido"),
            "titulo_sumario": metadata.get("titulo_sumario"),
            "organismo_origen": metadata.get("organismo_origen"),
            "fecha_sancion": metadata.get("fecha_sancion"),
            "year": metadata.get("year"),
            "chunk_index": metadata.get("chunk_index"),
        })
    
    return results


def format_conversation_history(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Convierte mensajes de Streamlit al formato de OpenAI Chat API.
    """
    openai_messages = []
    for msg in messages:
        role = msg.get("role")
        if role not in ["user", "assistant"]:
            continue
        content = msg.get("content", "")
        openai_messages.append({"role": role, "content": content})
    
    return openai_messages


def count_tokens(text: str, model: str = LLM_MODEL) -> int:
    """
    Cuenta tokens aproximados en un texto usando tiktoken.
    """
    try:
        if "gpt-4" in model or "gpt-3.5" in model or "gpt-5" in model or "o1" in model:
            encoding_name = "cl100k_base"
        else:
            encoding_name = "cl100k_base"
        
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception:
        return len(text) // 4


def estimate_chunks_tokens(context_chunks: List[Dict]) -> int:
    """
    Estima el número de tokens en los chunks de contexto.
    """
    total_text = ""
    for chunk in context_chunks:
        total_text += chunk.get("text", "")
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
    """
    if not messages or max_tokens <= 0:
        return []
    
    valid_messages = []
    message_map = []
    
    for i, msg in enumerate(messages):
        role = msg.get("role")
        if role in ["user", "assistant"]:
            valid_messages.append(msg)
            message_map.append(i)
    
    if not valid_messages:
        return []
    
    formatted = format_conversation_history(valid_messages)
    
    total_tokens = 0
    kept_indices = []
    
    for i in range(len(formatted) - 1, -1, -1):
        msg = formatted[i]
        msg_content = msg["content"]
        msg_tokens = count_tokens(msg_content, model)
        overhead = 10
        msg_total = msg_tokens + overhead
        
        if total_tokens + msg_total <= max_tokens:
            kept_indices.insert(0, i)
            total_tokens += msg_total
        else:
            break
    
    if not kept_indices:
        return []
    
    result = []
    for idx in kept_indices:
        original_idx = message_map[idx]
        result.append(messages[original_idx])
    
    return result


def truncate_history(messages: List[Dict[str, Any]], max_messages: int = MAX_HISTORY_MESSAGES) -> List[Dict[str, Any]]:
    """
    Trunca historial si es muy largo, manteniendo los mensajes más recientes.
    Función de fallback cuando no se puede contar tokens.
    """
    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages


def needs_query_rewriting(query: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, str]:
    """
    Detecta si una query necesita rewriting con contexto conversacional.
    
    Args:
        query: Query del usuario
        conversation_history: Historial conversacional (opcional)
    
    Returns:
        Tuple de (needs_rewriting: bool, reason: str)
    """
    if not conversation_history or not RAG_ENABLE_QUERY_REWRITING:
        return False, "no_history_or_disabled"
    
    query_lower = query.lower().strip()
    
    referential_patterns = [
        r'\b(ella|él|eso|esta|ese|esa|aquella|aquel)\b',
        r'\b(la|el|las|los)\s+(ley|norma|decreto|resolución|anterior|mencionada|citada)\b',
        r'\b(punto|artículo|sección|capítulo)\s+[a-z]\b',
        r'\b(ambas|otra|otras|mencionadas|anteriores)\b',
    ]
    
    for pattern in referential_patterns:
        if re.search(pattern, query_lower):
            return True, "referential_pronoun"
    
    vague_patterns = [
        r'\b(más\s+detalles?|dime\s+más|qué\s+más|información\s+adicional|más\s+información)\b',
        r'\b(sobre\s+ello|sobre\s+eso|acerca\s+de\s+ello)\b',
    ]
    
    for pattern in vague_patterns:
        if re.search(pattern, query_lower):
            return True, "vague_query"
    
    if len(query) < RAG_REWRITING_MIN_QUERY_LENGTH:
        return True, "short_query"
    
    referential_words = ["mencionada", "anterior", "citada", "referida", "esa", "este", "aquella"]
    for word in referential_words:
        if word in query_lower:
            return True, "referential_word"
    
    return False, "no_rewriting_needed"


def _clean_llm_response(text: str) -> str:
    """Limpia la respuesta del LLM removiendo comillas, markdown y caracteres innecesarios."""
    cleaned = text.strip()
    cleaned = cleaned.strip('"').strip("'").strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
    cleaned = cleaned.rstrip('.').strip()
    return cleaned


def rewrite_query_with_history(query: str, conversation_history: List[Dict[str, Any]]) -> str:
    """
    Reescribe la query incorporando información del historial conversacional.
    
    Args:
        query: Query original del usuario
        conversation_history: Historial conversacional
    
    Returns:
        Query reescrita con contexto del historial
    """
    if not conversation_history or len(conversation_history) == 0:
        return query
    
    client = _get_openai_client()
    
    history_text = ""
    valid_messages = 0
    for msg in conversation_history[-6:]:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role in ["user", "assistant"] and content:
            role_name = "Usuario" if role == "user" else "Asistente"
            history_text += f"{role_name}: {content[:300]}\n"
            valid_messages += 1
    
    if valid_messages == 0:
        return query
    
    prompt = f"""Reescribe esta consulta incorporando información relevante del historial conversacional para que sea más específica y útil para buscar en una base de datos de leyes argentinas.

Consulta original: {query}

Historial conversacional reciente:
{history_text}

Tu tarea:
1. Identificar a qué se refiere la consulta en el contexto del historial (ej: "ella" → "Ley 27.721", "el punto c" → el punto específico mencionado)
2. Reescribir la consulta para que sea específica y clara, incluyendo:
   - Números de ley mencionados en el historial
   - Conceptos o temas específicos discutidos
   - Términos legales relevantes
3. Si la consulta es vaga (ej: "más detalles"), convertirla en una búsqueda más específica basada en el contexto

IMPORTANTE:
- Responde SOLO con la query reescrita, sin explicaciones
- No uses comillas ni markdown
- Mantén la intención original pero hazla más específica
- Si no puedes determinar a qué se refiere, usa la query original pero expandida con términos relacionados"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Sos un experto en reescribir consultas para búsquedas legales, incorporando contexto conversacional de manera precisa."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_completion_tokens=150,
        )
        
        rewritten = _clean_llm_response(response.choices[0].message.content)
        return rewritten if rewritten else query
        
    except Exception as e:
        print(f"RAG: Error al reescribir query: {e}")
        return query


def evaluate_retrieval_quality(chunks: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Evalúa la calidad de la recuperación inicial sin usar LLM.
    
    Args:
        chunks: Lista de chunks encontrados con sus scores
    
    Returns:
        Tuple de (needs_more_context: bool, strategy: str)
        Estrategias: "wider", "expand", "both", "none"
    """
    if not chunks:
        return True, "wider"
    
    scores = [c.get("distance") for c in chunks if c.get("distance") is not None]
    if not scores:
        return True, "wider"
    
    avg_score = sum(scores) / len(scores)
    num_chunks = len(chunks)
    
    has_few_chunks = num_chunks < RAG_MIN_CHUNKS
    has_low_scores = avg_score < RAG_MIN_SIMILARITY_SCORE
    score_threshold_margin = RAG_MIN_SIMILARITY_SCORE + 0.1
    has_medium_scores = RAG_MIN_SIMILARITY_SCORE <= avg_score < score_threshold_margin
    
    if has_few_chunks and has_low_scores:
        return True, "both"
    elif has_few_chunks:
        return True, "wider"
    elif has_low_scores:
        return True, "expand"
    elif has_medium_scores:
        return True, "expand"
    else:
        return False, "none"


def evaluate_context_sufficiency(question: str, chunks: List[Dict[str, Any]]) -> bool:
    """
    Usa el LLM para evaluar si el contexto es suficiente para responder.
    
    Args:
        question: Pregunta del usuario
        chunks: Chunks encontrados
    
    Returns:
        True si el contexto es suficiente, False si necesita más
    """
    client = _get_openai_client()
    
    # Preparar contexto de chunks con información de metadata
    context_parts = []
    leyes_en_contexto = set()
    
    for c in chunks[:5]:
        text = c.get("text", "")[:500]
        tipo = c.get("tipo_norma", "")
        numero = c.get("numero_norma", "")
        if tipo and numero:
            ley_info = f"{tipo} {numero}"
            leyes_en_contexto.add(ley_info)
            context_parts.append(f"[{ley_info}]\n{text}")
        else:
            context_parts.append(text)
    
    context_text = "\n\n---\n\n".join(context_parts)
    leyes_str = ", ".join(sorted(leyes_en_contexto)) if leyes_en_contexto else "ninguna identificada"
    
    prompt = f"""Analizá si podés responder esta pregunta ESPECÍFICA con el contexto proporcionado.

Pregunta: {question}

Contexto disponible (leyes encontradas: {leyes_str}):
{context_text}

IMPORTANTE:
- Verificá si el contexto contiene información RELEVANTE y ESPECÍFICA para responder la pregunta
- Si la pregunta menciona una ley específica, verificá que esa ley esté en el contexto, si no lo está, es INSUFICIENTE
- Si la pregunta es sobre "ella", "esa ley", etc., verificá que el contexto tenga información sobre la ley referenciada
- Si el contexto tiene información de otras leyes pero NO de la que se pregunta, es INSUFICIENTE
- Solo considerá "suficiente" si realmente podés responder la pregunta completa con este contexto

¿El contexto es suficiente para responder esta pregunta de manera completa y precisa?
Responde SOLO "suficiente" o "insuficiente", sin explicaciones adicionales."""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Sos un evaluador estricto que determina si hay suficiente contexto RELEVANTE para responder preguntas específicas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_completion_tokens=10,
        )
        
        answer = response.choices[0].message.content.strip().lower()
        return "suficiente" in answer
        
    except Exception:
        # En caso de error, asumir que no es suficiente para ser conservador
        return False


def expand_query(query: str) -> str:
    """
    Expande la query usando el LLM para buscar información relacionada.
    
    Args:
        query: Query original del usuario
    
    Returns:
        Query expandida
    """
    client = _get_openai_client()
    
    prompt = f"""Expande esta consulta para buscar información relacionada que pueda ser relevante.

Consulta original: {query}

Generá una versión expandida de esta consulta que incluya:
- Sinónimos o términos relacionados
- Conceptos relacionados
- Variaciones de la pregunta

Responde SOLO con la query expandida, sin explicaciones ni texto adicional."""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Sos un asistente que expande consultas para mejorar búsquedas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_completion_tokens=100,
        )
        
        expanded = _clean_llm_response(response.choices[0].message.content)
        return expanded if expanded else query
        
    except Exception as e:
        print(f"RAG: Error al expandir query: {e}")
        return query


def combine_chunks(initial: List[Dict[str, Any]], additional: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Combina chunks iniciales y adicionales, eliminando duplicados.
    
    Args:
        initial: Chunks de la búsqueda inicial
        additional: Chunks de búsquedas adicionales
    
    Returns:
        Tuple de (lista combinada sin duplicados, cantidad agregados, cantidad duplicados)
    """
    # Crear set de identificadores únicos para deduplicar
    # Usamos doc_id + chunk_index para permitir múltiples chunks del mismo documento
    # Si no hay chunk_index, usamos hash del texto como fallback
    seen_ids = set()
    combined = []
    
    def get_chunk_id(chunk: Dict[str, Any]) -> str:
        """Genera un ID único para el chunk."""
        doc_id = chunk.get("doc_id")
        chunk_index = chunk.get("chunk_index")
        
        if doc_id and chunk_index is not None:
            # ID único: doc_id + chunk_index
            return f"{doc_id}_{chunk_index}"
        elif doc_id:
            # Fallback: usar hash del texto si no hay chunk_index
            text = chunk.get("text", "")[:100]  # Primeros 100 chars para hash
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            return f"{doc_id}_{text_hash}"
        else:
            # Último fallback: hash completo del texto
            text = chunk.get("text", "")
            return hashlib.md5(text.encode()).hexdigest()
    
    # Primero agregar chunks iniciales (ya están ordenados por relevancia)
    for chunk in initial:
        chunk_id = get_chunk_id(chunk)
        if chunk_id not in seen_ids:
            combined.append(chunk)
            seen_ids.add(chunk_id)
    
    # Luego agregar chunks adicionales que no estén duplicados
    added_count = 0
    duplicate_count = 0
    for chunk in additional:
        chunk_id = get_chunk_id(chunk)
        if chunk_id not in seen_ids:
            combined.append(chunk)
            seen_ids.add(chunk_id)
            added_count += 1
        else:
            duplicate_count += 1
    
    # Reordenar por score (distance) - menor es mejor si es distancia, mayor si es similitud
    # Asumimos que es similitud (mayor es mejor) y ordenamos descendente
    combined.sort(key=lambda x: x.get("distance", 0) or 0, reverse=True)
    
    return combined, added_count, duplicate_count


def generate_response(question: str, context_chunks: List[Dict], conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Genera una respuesta usando GPT con el contexto de los chunks y el historial conversacional.
    """
    client = _get_openai_client()
    
    model_limits = get_model_limits(LLM_MODEL)
    context_window = model_limits["context_window"]
    reserved_tokens = model_limits["reserved_tokens"]
    
    context_parts = []
    for chunk in context_chunks:
        source_info = f"{chunk['tipo_norma']} {chunk['numero_norma']}"
        if chunk.get('titulo_resumido'):
            source_info += f" - {chunk['titulo_resumido']}"
        context_parts.append(f"[{source_info}]\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    chunks_tokens = estimate_chunks_tokens(context_chunks)
    
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
- No menciones frases como "el contexto legal que me pegaste", pues el usuario no tiene acceso a qué fragmentos de ley te llegan, eso lo determina un RAG
- Si el usuario pregunta por las leyes de la conversación actual, fijate que haya un mensaje del historial donde el usuario o tú la mencionaron
- No inventes información legal que no esté en el contexto actual, es deccir, los fragmentos de texto legal proporcionados
- Usá un tono profesional pero accesible"""
    
    system_prompt_tokens = count_tokens(system_prompt, LLM_MODEL)
    
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
    
    response_tokens_estimate = 1000
    
    margin = 1000
    available_for_history = (
        context_window
        - reserved_tokens
        - chunks_tokens
        - system_prompt_tokens
        - user_prompt_base_tokens
        - response_tokens_estimate
        - margin
    )
    
    max_history_tokens = max(available_for_history, 500) if available_for_history > 0 else 0
    
    messages = [{"role": "system", "content": system_prompt}]
    
    has_history = False
    if conversation_history:
        if max_history_tokens > 0:
            truncated_history = truncate_history_by_tokens(
                conversation_history,
                max_tokens=max_history_tokens,
                model=LLM_MODEL
            )
        else:
            truncated_history = truncate_history(conversation_history, max_messages=MAX_HISTORY_MESSAGES)
        
        if truncated_history:
            formatted_history = format_conversation_history(truncated_history)
            messages.extend(formatted_history)
            has_history = True
    
    if has_history:
        history_note = "\n\nNOTA: Hay un historial conversacional disponible arriba. Usalo para entender referencias a leyes mencionadas previamente."
    else:
        history_note = ""
    
    user_prompt = user_prompt_template.format(context=context, question=question) + history_note
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,
    )
    
    return response.choices[0].message.content


def query(question: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, List[Dict]]:
    """
    Ejecuta el flujo completo de RAG con búsqueda iterativa adaptativa.
    
    Args:
        question: pregunta del usuario
        conversation_history: historial de mensajes previos (opcional)
    
    Returns:
        Tuple de (respuesta generada, lista de fuentes usadas)
    """
    search_query = question
    if conversation_history:
        needs_rewriting, reason = needs_query_rewriting(question, conversation_history)
        if needs_rewriting:
            print(f"RAG: Query rewriting activado (razon: {reason})")
            rewritten_query = rewrite_query_with_history(question, conversation_history)
            if rewritten_query != question:
                search_query = rewritten_query
                print(f"RAG: Query reescrita: {rewritten_query[:100]}...")
    
    chunks = search(search_query)
    initial_chunk_count = len(chunks)
    
    if not chunks:
        return "No encontré información relevante para tu consulta.", []
    
    needs_more, strategy = evaluate_retrieval_quality(chunks)
    
    if needs_more:
        avg_score = sum(c.get('distance', 0) or 0 for c in chunks) / len(chunks)
        print(f"RAG: Necesita mas contexto (estrategia: {strategy}, chunks: {initial_chunk_count}, score: {avg_score:.3f})")
    elif RAG_ENABLE_LLM_CHECK:
        print(f"RAG: Verificando suficiencia con LLM...")
    
    if not needs_more and RAG_ENABLE_LLM_CHECK:
        is_sufficient = evaluate_context_sufficiency(question, chunks)
        if not is_sufficient:
            needs_more = True
            strategy = "expand"
            print(f"RAG: Contexto insuficiente, activando expansion de query")
    
    if needs_more:
        additional_chunks = []
        
        if strategy in ["wider", "both"]:
            wider_top_k = SIMILARITY_TOP_K * RAG_WIDER_SEARCH_MULTIPLIER
            print(f"RAG: Busqueda amplia (top_k={wider_top_k})")
            wider_chunks = search(search_query, top_k=wider_top_k)
            additional_chunks.extend(wider_chunks)
            print(f"RAG: Encontrados {len(wider_chunks)} chunks adicionales (busqueda amplia)")
        
        if strategy in ["expand", "both"]:
            print(f"RAG: Expandiendo query...")
            expanded_query = expand_query(search_query)
            expanded_chunks = search(expanded_query, top_k=SIMILARITY_TOP_K)
            additional_chunks.extend(expanded_chunks)
            print(f"RAG: Encontrados {len(expanded_chunks)} chunks adicionales (query expandida)")
        
        if additional_chunks:
            chunks_before_combine = len(chunks)
            chunks, added_count, duplicate_count = combine_chunks(chunks, additional_chunks)
            chunks_after_combine = len(chunks)
            print(f"RAG: Combinados {chunks_before_combine} iniciales + {len(additional_chunks)} adicionales = {chunks_after_combine} unicos ({added_count} nuevos, {duplicate_count} duplicados)")
    else:
        print(f"RAG: Contexto inicial suficiente ({initial_chunk_count} chunks)")
    
    response = generate_response(question, chunks, conversation_history)
    sources = [
        {
            "tipo": c["tipo_norma"],
            "numero": c["numero_norma"],
            "titulo_resumido": c.get("titulo_resumido", ""),
            "titulo_sumario": c.get("titulo_sumario", ""),
            "organismo_origen": c.get("organismo_origen", ""),
            "fecha_sancion": c.get("fecha_sancion", ""),
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


class RAGSkill(BaseSkill):
    """Skill for answering questions about Argentine legislation using RAG.
    
    This skill searches through indexed Argentine laws and generates
    responses using retrieved context.
    """
    
    @property
    def name(self) -> str:
        return "rag"
    
    @property
    def description(self) -> str:
        return (
            "Busca y recupera información de leyes argentinas y legislación. "
            "Usá esta habilidad para preguntas sobre leyes, artículos legales, "
            "normativas, regulaciones y cualquier información legal. "
            "Ideal para: '¿Qué dice la ley de alquileres?', "
            "'¿Cuáles son los artículos sobre libertad de expresión?', "
            "'¿Qué leyes se sancionaron en 2024?'"
        )
    
    def initialize(self) -> None:
        """Load the LlamaIndex vector store."""
        initialize_rag()
    
    def execute(
        self, 
        query_text: str, 
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> SkillResult:
        """Execute RAG query and return result.
        
        Args:
            query_text: The user's question about legislation
            conversation_history: Previous conversation messages
        
        Returns:
            SkillResult with response and legal sources
        """
        response, sources = query(query_text, conversation_history)
        
        return SkillResult(
            response=response,
            sources=sources,
            metadata={"skill": self.name}
        )
