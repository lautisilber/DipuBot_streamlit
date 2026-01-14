"""
skills/sql_leyes/schemas.py
============================
Schemas de entrada y salida para la skill de consultas SQL.

Define los tipos de queries soportadas y la estructura de datos
usando Pydantic para validación automática.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from skills.base import SkillInput, SkillOutput


class QueryType(str, Enum):
    """Tipos de consultas soportadas por la skill."""
    COUNT = "count"  # Contar leyes de un diputado
    LAST = "last"  # Última ley de un diputado
    LIST = "list"  # Listar todas las leyes de un diputado
    CUSTOM = "custom"  # Query SQL personalizada (validada)


class SQLLeyesInput(SkillInput):
    """
    Input para la skill de consultas SQL sobre leyes.
    
    Ejemplos:
        # Contar leyes de un diputado
        SQLLeyesInput(
            query_type=QueryType.COUNT,
            diputado_nombre="Juan Pérez"
        )
        
        # Última ley de un diputado
        SQLLeyesInput(
            query_type=QueryType.LAST,
            diputado_nombre="María González"
        )
        
        # Query personalizada
        SQLLeyesInput(
            query_type=QueryType.CUSTOM,
            custom_query="SELECT COUNT(*) FROM leyes WHERE year = 2024"
        )
    """
    query_type: QueryType = Field(
        description="Tipo de consulta a realizar"
    )
    
    diputado_nombre: Optional[str] = Field(
        default=None,
        description="Nombre del diputado (para queries COUNT, LAST, LIST)"
    )
    
    custom_query: Optional[str] = Field(
        default=None,
        description="Query SQL personalizada (solo para CUSTOM)"
    )
    
    fuzzy_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Umbral para fuzzy matching de nombres (0.0 a 1.0)"
    )
    
    limit: Optional[int] = Field(
        default=10,
        ge=1,
        le=100,
        description="Límite de resultados para queries LIST"
    )
    
    @field_validator("diputado_nombre")
    @classmethod
    def validate_diputado_nombre(cls, v: Optional[str], info) -> Optional[str]:
        """Valida que diputado_nombre esté presente cuando es requerido."""
        query_type = info.data.get("query_type")
        if query_type in [QueryType.COUNT, QueryType.LAST, QueryType.LIST]:
            if not v or not v.strip():
                raise ValueError(
                    f"diputado_nombre es requerido para query_type={query_type}"
                )
        return v
    
    @field_validator("custom_query")
    @classmethod
    def validate_custom_query(cls, v: Optional[str], info) -> Optional[str]:
        """Valida que custom_query esté presente cuando es requerido."""
        query_type = info.data.get("query_type")
        if query_type == QueryType.CUSTOM:
            if not v or not v.strip():
                raise ValueError(
                    "custom_query es requerido para query_type=CUSTOM"
                )
        return v


class LeyInfo(BaseModel):
    """Información de una ley."""
    id: int
    tipo_norma: str
    numero_norma: str
    titulo_resumido: Optional[str]
    fecha_sancion: str
    year: int
    diputados_firmantes: Optional[str]


class SQLLeyesOutput(SkillOutput):
    """
    Output de la skill de consultas SQL.
    
    Estructura del campo 'data' según query_type:
    
    COUNT:
        {
            "count": int,
            "diputado": str
        }
    
    LAST:
        {
            "ley": LeyInfo,
            "diputado": str
        }
    
    LIST:
        {
            "leyes": List[LeyInfo],
            "count": int,
            "diputado": str
        }
    
    CUSTOM:
        {
            "rows": List[Dict],
            "count": int
        }
    """
    success: bool = Field(description="Si la query se ejecutó exitosamente")
    
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Datos resultantes de la query"
    )
    
    matched_name: Optional[str] = Field(
        default=None,
        description="Nombre exacto encontrado en la BD (si se usó fuzzy matching)"
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Mensaje de error si success=False"
    )
    
    query_executed: Optional[str] = Field(
        default=None,
        description="Query SQL ejecutada (para debugging)"
    )
