"""
chat
====
Módulo de chat con arquitectura de skills para consulta de documentos legales.
Responsabilidades: routing de skills, RAG, y generación de respuestas.
"""

from chat.chat import Chat, initialize_chat, query, reset_chat, get_chat
from chat.skills.base import BaseSkill, SkillResult
from chat.skills.rag_skill import RAGSkill

# Backward compatibility: expose rag functions at module level
from chat.skills.rag_skill import initialize_rag, query as rag_query, reset_rag

__all__ = [
    # New API
    "Chat",
    "initialize_chat",
    "query",
    "reset_chat",
    "get_chat",
    "BaseSkill",
    "SkillResult",
    "RAGSkill",
    # Backward compatibility
    "initialize_rag",
    "rag_query",
    "reset_rag",
]
