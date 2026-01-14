"""
skills/sql_leyes
================
Skill para consultas SQL estructuradas a la base de datos de leyes.

Esta skill permite realizar consultas específicas sobre la base de datos
sin usar RAG, ideal para preguntas que requieren datos estructurados
como contar leyes, buscar por diputado, etc.
"""

from .skill import SQLLeyesSkill
from .schemas import SQLLeyesInput, SQLLeyesOutput, QueryType

__all__ = ["SQLLeyesSkill", "SQLLeyesInput", "SQLLeyesOutput", "QueryType"]
