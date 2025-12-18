"""
etl/run.py
==========
Entrypoint del ETL. Procesa documentos de data/raw/ y construye
un índice LlamaIndex persistido en data/stories/<INDEX_VERSION>/.

Uso:
    python -m etl.run

La versión del índice se obtiene de:
    1. Env var INDEX_VERSION (si existe)
    2. Fecha actual YYYY-MM-DD (fallback)
"""

import os
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

# TODO: imports de LlamaIndex
# from llama_index.core import SimpleDirectoryReader, VectorStoreIndex

from etl.splitter import get_splitter
from etl.index_registry import register_index

load_dotenv()

# Paths
RAW_DIR = Path("data/raw")
STORIES_DIR = Path("data/stories")


def get_index_version() -> str:
    """Obtiene versión desde env var o genera fecha."""
    return os.getenv("INDEX_VERSION", date.today().isoformat())


def run_etl():
    """Pipeline ETL principal."""
    version = get_index_version()
    output_dir = STORIES_DIR / version

    print(f"[ETL] Versión: {version}")
    print(f"[ETL] Input: {RAW_DIR}")
    print(f"[ETL] Output: {output_dir}")

    # TODO: 1. Cargar documentos
    # reader = SimpleDirectoryReader(input_dir=str(RAW_DIR))
    # documents = reader.load_data()

    # TODO: 2. Aplicar splitter/chunking
    # splitter = get_splitter()
    # nodes = splitter.get_nodes_from_documents(documents)

    # TODO: 3. Construir índice
    # index = VectorStoreIndex(nodes)

    # TODO: 4. Persistir índice
    # output_dir.mkdir(parents=True, exist_ok=True)
    # index.storage_context.persist(persist_dir=str(output_dir))

    # TODO: 5. Registrar en registry.yaml
    # register_index(
    #     version=version,
    #     splitter_type="SentenceSplitter",
    #     splitter_params={"chunk_size": 512, "chunk_overlap": 50},
    #     embed_model=os.getenv("EMBED_MODEL", "text-embedding-3-small"),
    #     notes="ETL automático"
    # )

    print(f"[ETL] ✓ Índice construido en {output_dir}")


if __name__ == "__main__":
    run_etl()
