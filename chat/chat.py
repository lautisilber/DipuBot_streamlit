"""
chat/chat.py
============
Main Chat router that manages skills and routes queries.
Uses an LLM to determine which skill to invoke based on the query.
"""

import os
from typing import List, Dict, Any, Tuple, Optional

from openai import OpenAI
from dotenv import load_dotenv

from chat.skills.base import BaseSkill, SkillResult
from chat.config import LLM_MODEL

load_dotenv()


class Chat:
    """Main chatbot that routes queries to appropriate skills.
    
    The Chat class:
    1. Manages registered skills
    2. Uses an LLM to determine which skill to use for each query
    3. Executes the selected skill and returns results
    
    Example:
        from chat.chat import Chat
        from chat.skills.rag_skill import RAGSkill
        
        chat = Chat()
        chat.register_skill(RAGSkill())
        chat.initialize()
        
        response, sources = chat.query("¿Qué dice la ley de alquileres?")
    """
    
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self._openai_client: Optional[OpenAI] = None
        self._default_skill: Optional[str] = None
    
    def _get_openai_client(self) -> OpenAI:
        """Get OpenAI client (cached)."""
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY no configurada. "
                    "Agregala a tu archivo .env"
                )
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client
    
    def register_skill(self, skill: BaseSkill, default: bool = False) -> None:
        """Register a skill for use.
        
        Args:
            skill: The skill instance to register
            default: If True, use this skill when routing fails
        """
        self.skills[skill.name] = skill
        if default or self._default_skill is None:
            self._default_skill = skill.name
    
    def initialize(self) -> None:
        """Initialize all registered skills."""
        for skill in self.skills.values():
            skill.initialize()
    
    def _determine_skill(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Use LLM to determine which skill to use.
        
        Args:
            query: The user's question
            conversation_history: Previous messages for context
        
        Returns:
            Name of the skill to use
        """
        # If only one skill, use it directly
        if len(self.skills) == 1:
            return list(self.skills.keys())[0]
        
        # Build skill descriptions for the LLM
        skill_info = "\n".join([
            f"- {name}: {skill.description}"
            for name, skill in self.skills.items()
        ])
        
        system_prompt = f"""Sos un router que decide qué habilidad usar para responder una consulta.

Habilidades disponibles:
{skill_info}

Respondé ÚNICAMENTE con el nombre de la habilidad más apropiada.
No agregues explicaciones ni texto adicional, solo el nombre exacto de la habilidad."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation context if available
        if conversation_history:
            # Add last few messages for context
            recent_history = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
            for msg in recent_history:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg.get("content", "")[:500]  # Truncate for efficiency
                    })
        
        messages.append({
            "role": "user",
            "content": f"¿Qué habilidad debo usar para esta consulta?\n\nConsulta: {query}"
        })
        
        try:
            client = self._get_openai_client()
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0,
                max_completion_tokens=50,
            )
            
            skill_name = response.choices[0].message.content.strip().lower()
            
            # Validate the response
            if skill_name in self.skills:
                return skill_name
            
            # Try to find a partial match
            for name in self.skills.keys():
                if name in skill_name or skill_name in name:
                    return name
            
            # Fallback to default
            return self._default_skill
            
        except Exception:
            # On error, use default skill
            return self._default_skill
    
    def query(
        self, 
        question: str, 
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Process a query, routing to the appropriate skill.
        
        Args:
            question: The user's question
            conversation_history: Previous conversation messages
        
        Returns:
            Tuple of (response text, list of sources)
        """
        if not self.skills:
            raise ValueError("No hay habilidades registradas. Usá register_skill() primero.")
        
        # Determine which skill to use
        skill_name = self._determine_skill(question, conversation_history)
        skill = self.skills[skill_name]
        
        # Execute the skill
        result = skill.execute(question, conversation_history)
        
        return result.response, result.sources
    
    def reset(self) -> None:
        """Reset all skills (e.g., to reload indices)."""
        for skill in self.skills.values():
            if hasattr(skill, 'reset'):
                skill.reset()


# === Convenience functions for backward compatibility ===
# These match the old rag.py interface

_chat_instance: Optional[Chat] = None


def get_chat() -> Chat:
    """Get or create the singleton Chat instance with default skills."""
    global _chat_instance
    if _chat_instance is None:
        from chat.skills.rag_skill import RAGSkill
        
        _chat_instance = Chat()
        _chat_instance.register_skill(RAGSkill(), default=True)
    return _chat_instance


def initialize_chat() -> None:
    """Initialize the chat (convenience function)."""
    chat = get_chat()
    chat.initialize()


def query(question: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, List[Dict[str, Any]]]:
    """Query the chat (convenience function matching old rag.query interface).
    
    Args:
        question: The user's question
        conversation_history: Previous conversation messages
    
    Returns:
        Tuple of (response text, list of sources)
    """
    chat = get_chat()
    return chat.query(question, conversation_history)


def reset_chat() -> None:
    """Reset the chat singleton."""
    global _chat_instance
    _chat_instance = None
