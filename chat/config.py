"""
chat/config.py
==============
Configuración centralizada para el módulo de chat/RAG.
Define paths al índice LlamaIndex y parámetros del modelo.
"""

import os
from pathlib import Path
from typing import Optional, Tuple, Dict
from dotenv import load_dotenv

load_dotenv()

# === Paths ===
# Directorio raíz del proyecto (relativo a este archivo)
PROJECT_ROOT = Path(__file__).parent.parent
INDEXED_DIR = PROJECT_ROOT / "data" / "indexed"
DB_PATH = PROJECT_ROOT / "data" / "raw" / "leyes-leyes-2023-2025_12_20-2026_01_19.sqlite3"

# === Modelos ===
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.2")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# === RAG Settings ===
SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "5"))

# === RAG Iterative Search Settings ===
RAG_MIN_CHUNKS = int(os.getenv("RAG_MIN_CHUNKS", "3"))
RAG_MIN_SIMILARITY_SCORE = float(os.getenv("RAG_MIN_SIMILARITY_SCORE", "0.7"))
RAG_WIDER_SEARCH_MULTIPLIER = int(os.getenv("RAG_WIDER_SEARCH_MULTIPLIER", "2"))
RAG_ENABLE_LLM_CHECK = os.getenv("RAG_ENABLE_LLM_CHECK", "true").lower() == "true"

# === RAG Query Rewriting Settings ===
RAG_ENABLE_QUERY_REWRITING = os.getenv("RAG_ENABLE_QUERY_REWRITING", "true").lower() == "true"
RAG_REWRITING_MIN_QUERY_LENGTH = int(os.getenv("RAG_REWRITING_MIN_QUERY_LENGTH", "20"))

# === Model Token Limits ===
# Límites por modelo (context window, TPM, tokens reservados)
# Estos valores se usan para calcular cuánto historial puede incluirse
MODEL_LIMITS = {
    "gpt-5.2": {
        "context_window": 128000,      # Tokens máximos en el contexto (asumiendo similar a gpt-4o)
        "tpm_limit": 10000000,         # Tokens por minuto (rate limit - chequear)
        "reserved_tokens": 5000,       # Reservados para system prompt, user prompt, respuesta
    },
    "gpt-4o-mini": {
        "context_window": 128000,
        "tpm_limit": 200000,
        "reserved_tokens": 5000,
    },
    "gpt-4o": {
        "context_window": 128000,
        "tpm_limit": 10000000,
        "reserved_tokens": 5000,
    },
    "gpt-4-turbo": {
        "context_window": 128000,
        "tpm_limit": 10000000,
        "reserved_tokens": 5000,
    },
    "gpt-3.5-turbo": {
        "context_window": 16385,
        "tpm_limit": 90000,
        "reserved_tokens": 2000,
    },
    "gpt-4": {
        "context_window": 8192,
        "tpm_limit": 40000,
        "reserved_tokens": 2000,
    },
}

# Obtener límites del modelo actual
_current_limits = MODEL_LIMITS.get(LLM_MODEL, MODEL_LIMITS["gpt-5.2"])

# === Conversation History Settings ===
# Máximo de tokens para historial (se calcula dinámicamente considerando chunks)
# Este es un valor por defecto que se ajusta según el tamaño de los chunks
MAX_HISTORY_TOKENS = int(os.getenv("MAX_HISTORY_TOKENS", "0"))  # 0 = calcular automáticamente
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))  # Fallback si no se puede contar tokens


def get_model_limits(model_name: Optional[str] = None) -> Dict[str, int]:
    """
    Obtiene los límites de tokens para un modelo específico.
    
    Args:
        model_name: Nombre del modelo. Si es None, usa LLM_MODEL actual.
    
    Returns:
        Diccionario con context_window, tpm_limit, reserved_tokens
    """
    if model_name is None:
        model_name = LLM_MODEL
    return MODEL_LIMITS.get(model_name, MODEL_LIMITS["gpt-5.2"])


def find_latest_index() -> Optional[Path]:
    """
    Encuentra el directorio del índice LlamaIndex más reciente en data/indexed/.
    
    Returns:
        Path al directorio del índice (ej: llama_index_20260112_203029) o None si no existe
    """
    if not INDEXED_DIR.exists():
        return None
    
    # Buscar directorios llama_index_* ordenados por nombre (tienen timestamp)
    llama_index_dirs = sorted(
        [d for d in INDEXED_DIR.iterdir() if d.is_dir() and d.name.startswith("llama_index_")],
        reverse=True
    )
    
    if not llama_index_dirs:
        return None
    
    latest_dir = llama_index_dirs[0]
    
    # Verificar que el directorio tenga los archivos necesarios
    required_files = ["default__vector_store.json", "docstore.json", "index_store.json"]
    if not all((latest_dir / f).exists() for f in required_files):
        return None
    
    return latest_dir


def validate_index_exists() -> bool:
    """Verifica que exista al menos un índice LlamaIndex."""
    index_dir = find_latest_index()
    return index_dir is not None
