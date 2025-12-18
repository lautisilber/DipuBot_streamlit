"""
chat/config.py
==============
Configuración centralizada para el módulo de chat/RAG.
Define INDEX_VERSION y parámetros del modelo.

Importante: INDEX_VERSION determina qué índice carga el chat.
Debe coincidir con una carpeta existente en data/stories/.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === Paths ===
STORIES_DIR = Path("data/stories")

# === Index Version ===
# Esta es la versión del índice que usará el chat.
# Modificar manualmente o vía .env según el índice deseado.
INDEX_VERSION = os.getenv("INDEX_VERSION", "v1.0")

# === Modelos ===
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# === RAG Settings ===
SIMILARITY_TOP_K = 5  # chunks a recuperar


def get_index_path() -> Path:
    """Retorna path al índice según INDEX_VERSION."""
    return STORIES_DIR / INDEX_VERSION


def validate_index_exists() -> bool:
    """Verifica que el índice configurado exista."""
    path = get_index_path()
    return path.exists() and path.is_dir()
