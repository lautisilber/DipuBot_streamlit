"""
chat/config.py
==============
Configuración centralizada para el módulo de chat/RAG.
Define paths al índice FAISS y parámetros del modelo.
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# === Paths ===
# Directorio raíz del proyecto (relativo a este archivo)
PROJECT_ROOT = Path(__file__).parent.parent
INDEXED_DIR = PROJECT_ROOT / "data" / "indexed"

# === Modelos ===
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.2")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# === RAG Settings ===
SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "5"))


def find_latest_index() -> Tuple[Optional[Path], Optional[Path]]:
    """
    Encuentra el índice FAISS más reciente en data/indexed/.
    
    Returns:
        Tuple de (index_path, metadata_path) o (None, None) si no existe
    """
    if not INDEXED_DIR.exists():
        return None, None
    
    # Buscar archivos .faiss ordenados por nombre (tienen timestamp)
    faiss_files = sorted(INDEXED_DIR.glob("*.faiss"), reverse=True)
    
    if not faiss_files:
        return None, None
    
    latest_index = faiss_files[0]
    # El metadata tiene el mismo timestamp pero con _metadata_ en lugar de _index_
    latest_metadata = INDEXED_DIR / latest_index.name.replace("_index_", "_metadata_").replace(".faiss", ".json")
    
    if not latest_metadata.exists():
        return None, None
    
    return latest_index, latest_metadata


def validate_index_exists() -> bool:
    """Verifica que exista al menos un índice FAISS."""
    index_path, metadata_path = find_latest_index()
    return index_path is not None and metadata_path is not None
