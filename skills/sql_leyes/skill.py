"""
skills/sql_leyes/skill.py
==========================
Implementación de la skill de consultas SQL sobre leyes.

Esta skill permite realizar consultas estructuradas a la base de datos
de leyes, con soporte para fuzzy matching de nombres de diputados.
"""

import sqlite3
import re
from difflib import get_close_matches
from typing import List, Optional, Dict, Any

from skills.base import BaseSkill
from .schemas import SQLLeyesInput, SQLLeyesOutput, QueryType, LeyInfo
from .config import (
    DB_PATH,
    DEFAULT_FUZZY_THRESHOLD,
    ALLOWED_SQL_KEYWORDS,
    FORBIDDEN_SQL_KEYWORDS,
    PREDEFINED_QUERIES,
)


class SQLLeyesSkill(BaseSkill):
    """
    Skill para consultas SQL estructuradas sobre la base de datos de leyes.
    
    Características:
    - Fuzzy matching para nombres de diputados
    - Validación de queries read-only
    - Queries predefinidas optimizadas
    - Soporte para queries personalizadas seguras
    
    Uso:
        skill = SQLLeyesSkill()
        result = skill.execute(SQLLeyesInput(
            query_type=QueryType.COUNT,
            diputado_nombre="Juan Pérez"
        ))
    """
    
    @property
    def name(self) -> str:
        return "sql_leyes"
    
    @property
    def description(self) -> str:
        return (
            "Realiza consultas SQL estructuradas sobre la base de datos de leyes. "
            "Soporta contar leyes por diputado, obtener la última ley, listar leyes, "
            "y queries personalizadas. Incluye fuzzy matching para nombres de diputados."
        )
    
    def execute(self, input_data: SQLLeyesInput) -> SQLLeyesOutput:
        """
        Ejecuta una consulta SQL según el tipo especificado.
        
        Args:
            input_data: Parámetros de la consulta
        
        Returns:
            Resultado de la consulta con success=True/False
        """
        try:
            # Validar que la BD existe
            if not DB_PATH.exists():
                return SQLLeyesOutput(
                    success=False,
                    error=f"Base de datos no encontrada: {DB_PATH}"
                )
            
            # Ejecutar según tipo de query
            if input_data.query_type == QueryType.COUNT:
                return self._execute_count(input_data)
            elif input_data.query_type == QueryType.LAST:
                return self._execute_last(input_data)
            elif input_data.query_type == QueryType.LIST:
                return self._execute_list(input_data)
            elif input_data.query_type == QueryType.CUSTOM:
                return self._execute_custom(input_data)
            else:
                return SQLLeyesOutput(
                    success=False,
                    error=f"Tipo de query no soportado: {input_data.query_type}"
                )
        
        except Exception as e:
            return SQLLeyesOutput(
                success=False,
                error=f"Error inesperado: {str(e)}"
            )
    
    def _get_connection(self) -> sqlite3.Connection:
        """Crea una conexión a la base de datos."""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _find_diputado_name(
        self,
        search_name: str,
        threshold: float = DEFAULT_FUZZY_THRESHOLD
    ) -> Optional[str]:
        """
        Busca el nombre exacto de un diputado usando fuzzy matching.
        
        Args:
            search_name: Nombre a buscar (puede tener typos)
            threshold: Umbral de similitud (0.0 a 1.0)
        
        Returns:
            Nombre exacto encontrado o None si no hay match
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Obtener todos los nombres únicos de diputados
        cursor.execute("""
            SELECT DISTINCT diputados_firmantes
            FROM leyes
            WHERE diputados_firmantes IS NOT NULL
            AND diputados_firmantes != ''
        """)
        
        all_names = []
        for row in cursor.fetchall():
            firmantes = row[0]
            # Separar por coma si hay múltiples firmantes
            if firmantes:
                names = [name.strip() for name in firmantes.split(',')]
                all_names.extend(names)
        
        conn.close()
        
        # Eliminar duplicados
        unique_names = list(set(all_names))
        
        # Buscar matches
        matches = get_close_matches(
            search_name,
            unique_names,
            n=1,
            cutoff=threshold
        )
        
        return matches[0] if matches else None
    
    def _validate_readonly_query(self, query: str) -> bool:
        """
        Valida que una query sea read-only (solo SELECT).
        
        Args:
            query: Query SQL a validar
        
        Returns:
            True si es read-only, False si contiene operaciones de escritura
        """
        # Normalizar query (uppercase, sin comentarios)
        normalized = query.upper()
        normalized = re.sub(r'--.*$', '', normalized, flags=re.MULTILINE)
        normalized = re.sub(r'/\*.*?\*/', '', normalized, flags=re.DOTALL)
        
        # Verificar que no contenga keywords prohibidas
        for keyword in FORBIDDEN_SQL_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', normalized):
                return False
        
        # Verificar que comience con SELECT
        normalized_stripped = normalized.strip()
        if not normalized_stripped.startswith('SELECT'):
            return False
        
        return True
    
    def _execute_count(self, input_data: SQLLeyesInput) -> SQLLeyesOutput:
        """Ejecuta una query COUNT para contar leyes de un diputado."""
        # Fuzzy matching del nombre
        matched_name = self._find_diputado_name(
            input_data.diputado_nombre,
            input_data.fuzzy_threshold
        )
        
        if not matched_name:
            return SQLLeyesOutput(
                success=False,
                error=f"No se encontró ningún diputado similar a '{input_data.diputado_nombre}'"
            )
        
        # Ejecutar query
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = PREDEFINED_QUERIES["count_by_diputado"]
        cursor.execute(query, (f"%{matched_name}%",))
        
        result = cursor.fetchone()
        count = result[0] if result else 0
        
        conn.close()
        
        return SQLLeyesOutput(
            success=True,
            data={
                "count": count,
                "diputado": matched_name
            },
            matched_name=matched_name,
            query_executed=query
        )
    
    def _execute_last(self, input_data: SQLLeyesInput) -> SQLLeyesOutput:
        """Ejecuta una query para obtener la última ley de un diputado."""
        # Fuzzy matching del nombre
        matched_name = self._find_diputado_name(
            input_data.diputado_nombre,
            input_data.fuzzy_threshold
        )
        
        if not matched_name:
            return SQLLeyesOutput(
                success=False,
                error=f"No se encontró ningún diputado similar a '{input_data.diputado_nombre}'"
            )
        
        # Ejecutar query
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = PREDEFINED_QUERIES["last_by_diputado"]
        cursor.execute(query, (f"%{matched_name}%",))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return SQLLeyesOutput(
                success=True,
                data={
                    "ley": None,
                    "diputado": matched_name
                },
                matched_name=matched_name,
                query_executed=query
            )
        
        ley = LeyInfo(
            id=result["id"],
            tipo_norma=result["tipo_norma"],
            numero_norma=result["numero_norma"],
            titulo_resumido=result["titulo_resumido"],
            fecha_sancion=result["fecha_sancion"],
            year=result["year"],
            diputados_firmantes=result["diputados_firmantes"]
        )
        
        return SQLLeyesOutput(
            success=True,
            data={
                "ley": ley.model_dump(),
                "diputado": matched_name
            },
            matched_name=matched_name,
            query_executed=query
        )
    
    def _execute_list(self, input_data: SQLLeyesInput) -> SQLLeyesOutput:
        """Ejecuta una query para listar leyes de un diputado."""
        # Fuzzy matching del nombre
        matched_name = self._find_diputado_name(
            input_data.diputado_nombre,
            input_data.fuzzy_threshold
        )
        
        if not matched_name:
            return SQLLeyesOutput(
                success=False,
                error=f"No se encontró ningún diputado similar a '{input_data.diputado_nombre}'"
            )
        
        # Ejecutar query
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = PREDEFINED_QUERIES["list_by_diputado"]
        cursor.execute(query, (f"%{matched_name}%", input_data.limit))
        
        results = cursor.fetchall()
        conn.close()
        
        leyes = [
            LeyInfo(
                id=row["id"],
                tipo_norma=row["tipo_norma"],
                numero_norma=row["numero_norma"],
                titulo_resumido=row["titulo_resumido"],
                fecha_sancion=row["fecha_sancion"],
                year=row["year"],
                diputados_firmantes=row["diputados_firmantes"]
            )
            for row in results
        ]
        
        return SQLLeyesOutput(
            success=True,
            data={
                "leyes": [ley.model_dump() for ley in leyes],
                "count": len(leyes),
                "diputado": matched_name
            },
            matched_name=matched_name,
            query_executed=query
        )
    
    def _execute_custom(self, input_data: SQLLeyesInput) -> SQLLeyesOutput:
        """Ejecuta una query SQL personalizada (con validación)."""
        query = input_data.custom_query
        
        # Validar que sea read-only
        if not self._validate_readonly_query(query):
            return SQLLeyesOutput(
                success=False,
                error="Query no permitida. Solo se permiten queries SELECT read-only."
            )
        
        # Ejecutar query
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            conn.close()
            
            # Convertir resultados a lista de diccionarios
            rows = [dict(row) for row in results]
            
            return SQLLeyesOutput(
                success=True,
                data={
                    "rows": rows,
                    "count": len(rows)
                },
                query_executed=query
            )
        
        except sqlite3.Error as e:
            return SQLLeyesOutput(
                success=False,
                error=f"Error SQL: {str(e)}",
                query_executed=query
            )
