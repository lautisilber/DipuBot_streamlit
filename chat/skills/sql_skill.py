"""
chat/skills/sql_skill.py
========================
Text-to-SQL skill for querying the leyes database.
Uses an LLM to generate SQL queries from natural language.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional

from openai import OpenAI
from dotenv import load_dotenv

from chat.skills.base import BaseSkill, SkillResult
from chat.config import DB_PATH, LLM_MODEL

load_dotenv()


# Schema description for the LLM
LEYES_SCHEMA = """
Tabla: leyes
Columnas:
- id (INTEGER, PRIMARY KEY): ID interno
- id_norma (TEXT): ID oficial de la norma
- tipo_norma (TEXT): Tipo de norma (ej: LEY, DECRETO, RESOLUCION)
- numero_norma (TEXT): Número de la norma
- clase_norma (TEXT): Clasificación de la norma
- organismo_origen (TEXT): Organismo que emitió la norma
- fecha_sancion (TEXT): Fecha de sanción (formato YYYY-MM-DD)
- numero_boletin (TEXT): Número del Boletín Oficial
- fecha_boletin (TEXT): Fecha de publicación en el Boletín
- pagina_boletin (TEXT): Página del Boletín
- titulo_resumido (TEXT): Título corto de la ley
- titulo_sumario (TEXT): Título del sumario
- texto_resumido (TEXT): Resumen del contenido
- observaciones (TEXT): Observaciones adicionales
- texto_actualizado (TEXT): Texto consolidado actual
- texto_original_link (TEXT): URL al texto original
- texto_actualizado_link (TEXT): URL al texto actualizado
- numero_ley_original (TEXT): Número de ley original
- numero_ley_actualizado (TEXT): Número de ley actualizado
- year (TEXT): Año de la norma
- texto_original (TEXT): Texto completo original de la ley
"""


class SQLSkill(BaseSkill):
    """Skill for querying the leyes database using natural language.
    
    Translates user questions into SQL queries and executes them
    against the SQLite database containing Argentine laws.
    """
    
    def __init__(self):
        self._openai_client: Optional[OpenAI] = None
        self._db_path = str(DB_PATH)
    
    @property
    def name(self) -> str:
        return "sql_query"
    
    @property
    def description(self) -> str:
        return (
            "Consultas estructuradas sobre metadatos de leyes: contar leyes, "
            "filtrar por fecha/año/tipo, listar leyes por organismo, "
            "buscar por número de ley, estadísticas agregadas. "
            "Usar cuando se piden datos numéricos, listados, o filtros específicos."
        )
    
    def _get_openai_client(self) -> OpenAI:
        """Get OpenAI client (cached)."""
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY no configurada.")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client
    
    def _generate_sql(self, query: str) -> str:
        """Use LLM to generate SQL from natural language query."""
        system_prompt = f"""Sos un experto en SQL que traduce consultas en lenguaje natural a SQL.

{LEYES_SCHEMA}

Reglas:
1. Generá SOLO la consulta SQL, sin explicaciones ni markdown
2. Usá SOLO SELECT (nunca INSERT, UPDATE, DELETE, DROP, etc.)
3. Limitá resultados a 20 filas máximo con LIMIT
4. Para búsquedas de texto usá LIKE con %
5. Los años están en la columna 'year' como texto
6. Las fechas están en formato 'YYYY-MM-DD' como texto
7. Si la consulta no es clara, hacé tu mejor interpretación
8. NÚMEROS DE LEY: normalizar formatos (27.771 = 27771). Buscar en numero_norma o numero_ley_original
   Ejemplo: para "ley 27.771" usar WHERE numero_norma LIKE '%27771%' OR numero_ley_original LIKE '%27771%'
9. Si piden el TEXTO de una ley específica por número, SÍ incluir texto_original o texto_actualizado
10. Para consultas generales (no de texto), evitar campos largos como texto_original"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Consulta: {query}"}
        ]
        
        client = self._get_openai_client()
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0,
            max_completion_tokens=500,
        )
        
        sql = response.choices[0].message.content.strip()
        
        # Clean up markdown code blocks if present
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        return sql.strip()
    
    def _validate_sql(self, sql: str) -> bool:
        """Validate that SQL is a safe SELECT query."""
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT
        if not sql_upper.startswith("SELECT"):
            return False
        
        # Block dangerous keywords
        dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", 
                     "TRUNCATE", "EXEC", "EXECUTE", "--", ";--"]
        for keyword in dangerous:
            if keyword in sql_upper:
                return False
        
        return True
    
    def _execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dicts."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def _format_results(self, results: List[Dict[str, Any]], query: str, sql: str) -> str:
        """Use LLM to format SQL results into natural language."""
        if not results:
            return "No se encontraron resultados para tu consulta."
        
        # Truncate results for the prompt
        results_str = str(results[:10])  # Limit for prompt size
        if len(results) > 10:
            results_str += f"\n... y {len(results) - 10} resultados más."
        
        system_prompt = """Sos un asistente que presenta resultados de consultas SQL de forma clara y natural en español.
Formateá los resultados de manera legible, usando listas o tablas si es apropiado.
Sé conciso pero informativo."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Consulta original: {query}\n\nResultados ({len(results)} filas):\n{results_str}"}
        ]
        
        client = self._get_openai_client()
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.3,
            max_completion_tokens=1000,
        )
        
        return response.choices[0].message.content.strip()
    
    def execute(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> SkillResult:
        """Execute SQL query skill.
        
        Args:
            query: Natural language question about laws
            conversation_history: Previous messages (not used for SQL)
        
        Returns:
            SkillResult with formatted response and metadata
        """
        try:
            # Generate SQL from natural language
            sql = self._generate_sql(query)
            
            # Validate SQL is safe
            if not self._validate_sql(sql):
                return SkillResult(
                    response="No pude generar una consulta SQL válida para tu pregunta. "
                             "Probá reformularla de otra manera.",
                    sources=[],
                    metadata={"error": "invalid_sql", "generated_sql": sql}
                )
            
            # Execute query
            results = self._execute_sql(sql)
            
            # Format results
            formatted = self._format_results(results, query, sql)
            
            return SkillResult(
                response=formatted,
                sources=[{"type": "sql_query", "query": sql, "row_count": len(results)}],
                metadata={
                    "sql": sql,
                    "row_count": len(results),
                    "raw_results": results[:5]  # First 5 for debugging
                }
            )
            
        except sqlite3.Error as e:
            return SkillResult(
                response=f"Error al ejecutar la consulta en la base de datos: {str(e)}",
                sources=[],
                metadata={"error": "db_error", "details": str(e)}
            )
        except Exception as e:
            return SkillResult(
                response=f"Ocurrió un error procesando tu consulta: {str(e)}",
                sources=[],
                metadata={"error": "general_error", "details": str(e)}
            )
    
    def initialize(self) -> None:
        """Verify database exists on initialization."""
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {DB_PATH}")
