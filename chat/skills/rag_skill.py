"""
chat/skills/rag_skill.py
========================
RAG skill for answering questions about Argentine legislation.
Wraps the existing rag.py functionality as a skill.
"""

from typing import List, Dict, Any, Optional

from chat.skills.base import BaseSkill, SkillResult
from chat import rag


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
        rag.initialize_rag()
    
    def execute(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> SkillResult:
        """Execute RAG query and return result.
        
        Args:
            query: The user's question about legislation
            conversation_history: Previous conversation messages
        
        Returns:
            SkillResult with response and legal sources
        """
        response, sources = rag.query(query, conversation_history)
        
        return SkillResult(
            response=response,
            sources=sources,
            metadata={"skill": self.name}
        )
