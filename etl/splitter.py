"""
etl/splitter.py
===============
Configuración y factory de splitters/chunkers para documentos.
Centraliza la lógica de partición de texto para mantener consistencia.
"""

# TODO: imports de LlamaIndex
# from llama_index.core.node_parser import SentenceSplitter, TokenTextSplitter

# Defaults
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 50


def get_splitter(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    splitter_type: str = "sentence"
):
    """
    Factory para obtener un splitter configurado.

    Args:
        chunk_size: tamaño de chunk en tokens/chars
        chunk_overlap: overlap entre chunks
        splitter_type: "sentence" o "token"

    Returns:
        NodeParser configurado

    TODO: implementar lógica
    """
    # TODO: implementar factory
    # if splitter_type == "sentence":
    #     return SentenceSplitter(
    #         chunk_size=chunk_size,
    #         chunk_overlap=chunk_overlap
    #     )
    # elif splitter_type == "token":
    #     return TokenTextSplitter(
    #         chunk_size=chunk_size,
    #         chunk_overlap=chunk_overlap
    #     )
    # else:
    #     raise ValueError(f"Splitter desconocido: {splitter_type}")

    raise NotImplementedError("TODO: implementar get_splitter")


def get_splitter_metadata(splitter) -> dict:
    """
    Extrae metadata del splitter para registro.

    Returns:
        dict con tipo y parámetros principales
    """
    # TODO: extraer info del splitter
    return {
        "type": "SentenceSplitter",
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "chunk_overlap": DEFAULT_CHUNK_OVERLAP
    }
