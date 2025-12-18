"""
etl/index_registry.py
=====================
Gestión del registro de versiones de índices en data/stories/registry.yaml.

El registro almacena metadata de cada índice:
    - version: tag/nombre del índice
    - created_at: fecha de creación
    - splitter: tipo y parámetros de chunking
    - embed_model: modelo de embeddings usado
    - notes: descripción corta

Uso:
    from etl.index_registry import register_index, get_registry

    # Registrar nuevo índice
    register_index(
        version="v1.0",
        splitter_type="SentenceSplitter",
        splitter_params={"chunk_size": 512},
        embed_model="text-embedding-3-small",
        notes="Primera versión con docs completos"
    )

    # Leer registro
    registry = get_registry()
"""

from pathlib import Path
from datetime import datetime

# TODO: import yaml
# import yaml

REGISTRY_PATH = Path("data/stories/registry.yaml")


def get_registry() -> dict:
    """
    Lee el registro actual de versiones.

    Returns:
        dict con versiones como keys
    """
    # TODO: implementar lectura YAML
    # if not REGISTRY_PATH.exists():
    #     return {}
    # with open(REGISTRY_PATH, "r") as f:
    #     return yaml.safe_load(f) or {}

    raise NotImplementedError("TODO: implementar get_registry")


def register_index(
    version: str,
    splitter_type: str,
    splitter_params: dict,
    embed_model: str,
    notes: str = ""
) -> None:
    """
    Agrega o actualiza una entrada en el registro.

    Args:
        version: identificador del índice (e.g. "v1.0", "2024-01-15")
        splitter_type: tipo de splitter usado
        splitter_params: parámetros del splitter
        embed_model: modelo de embeddings
        notes: descripción corta (1 línea)
    """
    # TODO: implementar escritura YAML
    # registry = get_registry()
    # registry[version] = {
    #     "created_at": datetime.now().isoformat(),
    #     "splitter": {
    #         "type": splitter_type,
    #         "params": splitter_params
    #     },
    #     "embed_model": embed_model,
    #     "notes": notes
    # }
    # REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    # with open(REGISTRY_PATH, "w") as f:
    #     yaml.dump(registry, f, default_flow_style=False)

    raise NotImplementedError("TODO: implementar register_index")


def list_versions() -> list:
    """Lista todas las versiones registradas."""
    # TODO: return list(get_registry().keys())
    raise NotImplementedError("TODO: implementar list_versions")
