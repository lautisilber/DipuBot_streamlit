"""
skills/__init__.py
==================
Módulo de skills para DipuBot.

Este módulo contiene skills independientes que pueden ser utilizadas
por el chatbot para realizar tareas específicas más allá del RAG.

Compatible con LlamaIndex para futura integración.
"""

from typing import Dict, Type

from .base import BaseSkill

# Registry de skills disponibles
# Esto será útil cuando se integre con LlamaIndex
SKILLS_REGISTRY: Dict[str, Type[BaseSkill]] = {}

# Lazy import para evitar dependencias circulares
def get_skill(skill_name: str) -> BaseSkill:
    """
    Obtiene una instancia de una skill por nombre.
    
    Args:
        skill_name: Nombre de la skill (ej: "sql_leyes")
    
    Returns:
        Instancia de la skill
    
    Raises:
        ValueError: Si la skill no existe
    """
    if skill_name == "sql_leyes":
        from .sql_leyes.skill import SQLLeyesSkill
        return SQLLeyesSkill()
    
    raise ValueError(f"Skill '{skill_name}' no encontrada")


__all__ = ["BaseSkill", "SKILLS_REGISTRY", "get_skill"]
