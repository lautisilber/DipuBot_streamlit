"""
chat/config.py
==============
Configuración centralizada para el módulo de chat/RAG.
Define paths al índice FAISS y parámetros del modelo.
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

# === Modelos ===
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.2")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# === RAG Settings ===
SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "5"))

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
