"""
chat/rag.py
===========
Lógica de RAG: carga índice persistido y expone query engine.
Responsable de retrieval + generación de respuestas.

Uso desde Streamlit:
    from chat.rag import get_query_engine, query
    engine = get_query_engine()
    response = query(engine, "¿Qué dice el artículo 14 bis?")
"""

from pathlib import Path

# TODO: imports de LlamaIndex
# from llama_index.core import StorageContext, load_index_from_storage
# from llama_index.core.query_engine import RetrieverQueryEngine

from chat.config import (
    get_index_path,
    validate_index_exists,
    SIMILARITY_TOP_K,
    LLM_MODEL
)

# Cache del query engine (singleton simple)
_query_engine = None


def load_index(index_path: Path):
    """
    Carga índice LlamaIndex desde disco.

    Args:
        index_path: carpeta con índice persistido

    Returns:
        VectorStoreIndex cargado
    """
    # TODO: implementar carga
    # storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
    # index = load_index_from_storage(storage_context)
    # return index

    raise NotImplementedError("TODO: implementar load_index")


def get_query_engine():
    """
    Obtiene query engine (con cache singleton).

    Returns:
        QueryEngine configurado

    Raises:
        FileNotFoundError si el índice no existe
    """
    global _query_engine

    if _query_engine is not None:
        return _query_engine

    if not validate_index_exists():
        index_path = get_index_path()
        raise FileNotFoundError(
            f"Índice no encontrado en {index_path}. "
            f"Ejecutá 'python -m etl.run' primero."
        )

    # TODO: cargar índice y crear query engine
    # index = load_index(get_index_path())
    # _query_engine = index.as_query_engine(similarity_top_k=SIMILARITY_TOP_K)
    # return _query_engine

    raise NotImplementedError("TODO: implementar get_query_engine")


def query(engine, question: str) -> str:
    """
    Ejecuta query contra el RAG.

    Args:
        engine: query engine de LlamaIndex
        question: pregunta del usuario

    Returns:
        respuesta generada
    """
    # TODO: implementar query
    # response = engine.query(question)
    # return str(response)

    raise NotImplementedError("TODO: implementar query")


def reset_engine():
    """Resetea cache del engine (útil para reload)."""
    global _query_engine
    _query_engine = None
