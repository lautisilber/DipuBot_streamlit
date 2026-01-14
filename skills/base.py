"""
skills/base.py
==============
Clase base abstracta para todas las skills.

Define la interfaz común que todas las skills deben implementar.
Compatible con LlamaIndex para futura integración como tools/functions.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class SkillInput(BaseModel):
    """
    Clase base para inputs de skills.
    
    Todas las skills deben definir su propio schema de input
    heredando de esta clase.
    """
    pass


class SkillOutput(BaseModel):
    """
    Clase base para outputs de skills.
    
    Todas las skills deben definir su propio schema de output
    heredando de esta clase.
    """
    success: bool
    error: Optional[str] = None


class BaseSkill(ABC):
    """
    Clase base abstracta para todas las skills.
    
    Las skills son herramientas especializadas que el chatbot puede usar
    para realizar tareas específicas que van más allá del RAG tradicional.
    
    Cada skill debe:
    1. Definir sus propios schemas de input/output usando Pydantic
    2. Implementar el método execute()
    3. Ser stateless (no mantener estado entre ejecuciones)
    4. Ser thread-safe
    
    Ejemplo:
        class MySkill(BaseSkill):
            def execute(self, input_data: MySkillInput) -> MySkillOutput:
                # Lógica de la skill
                return MySkillOutput(success=True, data=result)
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre único de la skill."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción de qué hace la skill."""
        pass
    
    @abstractmethod
    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Ejecuta la skill con los datos de entrada proporcionados.
        
        Args:
            input_data: Datos de entrada validados por Pydantic
        
        Returns:
            Resultado de la ejecución con success=True/False
        
        Raises:
            No debe lanzar excepciones, debe capturarlas y retornar
            SkillOutput con success=False y error descriptivo.
        """
        pass
    
    def to_llamaindex_tool(self) -> Dict[str, Any]:
        """
        Convierte la skill a un formato compatible con LlamaIndex tools.
        
        Este método será útil cuando se integre con LlamaIndex.
        Por ahora retorna un diccionario con metadata básica.
        
        Returns:
            Diccionario con metadata de la tool
        """
        return {
            "name": self.name,
            "description": self.description,
            "execute": self.execute,
        }
