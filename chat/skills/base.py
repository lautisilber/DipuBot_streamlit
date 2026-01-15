"""
chat/skills/base.py
===================
Base class for chatbot skills.
Defines the interface that all skills must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SkillResult:
    """Standard result format from skill execution.
    
    Attributes:
        response: The generated response text
        sources: List of sources used (format depends on skill)
        metadata: Optional additional data from skill execution
    """
    response: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class BaseSkill(ABC):
    """Abstract base class for chatbot skills.
    
    All skills must implement:
    - name: Unique identifier for the skill
    - description: Description for the router to understand when to use this skill
    - execute: Main logic to process a query and return a result
    
    Optional:
    - initialize: Setup code (load models, indices, etc.)
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique skill identifier.
        
        Returns:
            String identifier (e.g., 'rag', 'sql_query')
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description for the router to understand when to use this skill.
        
        This description is used by the LLM to decide which skill to invoke.
        Be specific about what types of queries this skill handles.
        
        Returns:
            Description string
        """
        pass
    
    @abstractmethod
    def execute(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> SkillResult:
        """Execute the skill on a query.
        
        Args:
            query: The user's question or request
            conversation_history: Optional list of previous messages
                Format: [{"role": "user"/"assistant", "content": "..."}]
        
        Returns:
            SkillResult with response, sources, and optional metadata
        """
        pass
    
    def initialize(self) -> None:
        """Optional initialization hook.
        
        Override this method to load models, indices, or other resources.
        Called once when the skill is registered with the Chat router.
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
