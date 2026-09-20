"""
chat/skills/sql_skill.py
========================
Text-to-SQL skill for querying the leyes database.
Uses an LLM to generate SQL queries from natural language.
"""

import os
import json
import sqlite3
from typing import List, Dict, Any, Optional

from openai import OpenAI
from dotenv import load_dotenv

from chat.skills.base import BaseSkill, SkillResult
from chat.config import DB_PATH, LLM_MODEL
from chat.response_policy import RESPONSE_POLICY
from chat.parliamentary import PARLIAMENTARY_SCHEMA
from pathlib import Path

load_dotenv()


# Schema description for the LLM
LEYES_SCHEMA = """
=== TABLA PRINCIPAL ===

Tabla: leyes
- id (INTEGER, PRIMARY KEY): ID interno
- id_norma (INTEGER): ID oficial de la norma
- tipo_norma (TEXT): Tipo de norma (LEY, DECRETO, RESOLUCIÓN, etc.)
- numero_norma (TEXT): Número de la norma
- clase_norma (TEXT): Clasificación de la norma
- organismo_origen (TEXT): Organismo que emitió la norma
- fecha_sancion (TEXT): Fecha de sanción (YYYY-MM-DD)
- numero_boletin (INTEGER): Número del Boletín Oficial
- fecha_boletin (TEXT): Fecha del Boletín (YYYY-MM-DD)
- pagina_boletin (INTEGER): Página del Boletín
- titulo_resumido (TEXT): Título corto
- titulo_sumario (TEXT): Título del sumario
- texto_resumido (TEXT): Resumen del contenido
- observaciones (TEXT): Observaciones adicionales
- texto_original (TEXT): Texto completo original (campo largo)
- texto_actualizado (TEXT): Texto consolidado actual (campo largo)
- texto_original_link (TEXT): URL al texto original
- texto_actualizado_link (TEXT): URL al texto actualizado
- numero_ley_original (INTEGER): Número de ley original
- numero_ley_actualizado (INTEGER): Número de ley actualizado
- year (INTEGER): Año de la norma

"""

LEYES_SCHEMA += PARLIAMENTARY_SCHEMA


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
            "Consultas estructuradas sobre leyes: buscar por firmante/diputado, "
            "filtrar por bloque/partido político, contar leyes, filtrar por fecha/año/tipo, "
            "listar leyes por organismo, buscar por número de ley, estadísticas agregadas. "
            "Usar cuando se piden datos numéricos, listados, filtros, o información sobre firmantes/bloques."
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
4. Para búsquedas de texto usá LIKE con % (case insensitive en SQLite)
5. Las fechas están en formato 'YYYY-MM-DD' como texto
6. Si la consulta no es clara, hacé tu mejor interpretación
7. NÚMEROS DE LEY: normalizar formatos (27.771 = 27771). Buscar en numero_norma o numero_ley_original
8. Si piden el TEXTO de una ley específica por número, SÍ incluir texto_original o texto_actualizado
9. Para consultas generales (no de texto), evitar campos largos como texto_original/texto_actualizado
10. BÚSQUEDA POR FIRMANTE: Los nombres están en formato "APELLIDO, NOMBRE" en mayúsculas.
    Para buscar por nombre, usar LIKE '%APELLIDO%' o LIKE '%NOMBRE%' (fuzzy matching).
    Consultar directamente la vista autorias_leyes y su columna firmante.
11. BÚSQUEDA POR BLOQUE: Usar autorias_leyes.bloque. Para PRO usar
    UPPER(bloque) IN ('PRO', 'FRENTE PRO', 'PRO - PROPUESTA REPUBLICANA').
    No buscar '%PRO%': también coincide con PRODUCCION Y TRABAJO y otros bloques.
12. NOMBRES DE COLUMNAS: Usar exactamente los nombres documentados. 
13. Siempre usar SELECT DISTINCT cuando hay JOINs para evitar duplicados
14. Ordenar resultados por año DESC cuando sea relevante
15. Si pregunta quién propuso o presentó una ley, devolver rol='autor'. Si pide
    firmantes, incluir ambos roles. Incluir rol, bloque, fuente_url y fuente_autor_url en listados.
16. Los conteos de leyes usan COUNT(DISTINCT ley_id), nunca COUNT(*) sobre firmas.
17. No inventar tablas, columnas ni afiliaciones partidarias ausentes del esquema."""

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
        conn = sqlite3.connect(Path(self._db_path).resolve().as_uri() + "?mode=ro", uri=True)
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
            if "autorias_leyes" in sql.lower():
                return ("No encontré coincidencias en los datos de autoría disponibles. "
                        "La cobertura de proyectos vinculados a leyes de 2008 a 2025 es parcial; "
                        "esto no demuestra que una persona o bloque no haya presentado proyectos.")
            return "No encontré resultados para esa consulta en los datos disponibles."
        
        results_str = json.dumps(results, ensure_ascii=False, default=str)
        system_prompt = RESPONSE_POLICY + """
Presentá los resultados de la consulta usando solo los datos recuperados.
Incluí todas las filas recibidas cuando se solicita un listado.
Las consultas devuelven como máximo 20 filas: si recibís 20, indicá que se
muestran hasta 20 resultados, sin afirmar que son el total de coincidencias.
La base contiene leyes aprobadas, no todos los proyectos presentados.
Una búsqueda sin coincidencias no demuestra que nunca se presentó un proyecto.
No hay datos de votaciones. No atribuyas autoría exclusiva a un firmante si
no hay un campo que identifique expresamente su rol.
En autorías, rol='autor' identifica al autor del proyecto cabecera según HCDN;
rol='firmante' no identifica necesariamente al autor principal. Una ley puede
tener antecedentes adicionales: no atribuyas autoría exclusiva de toda la ley.
Indicá que los conteos corresponden a los registros disponibles y que la
cobertura 2008–2025 es parcial. No describas estos datos como todos los proyectos
presentados. Un bloque es histórico; PODER EJECUTIVO no es un partido.
Cuando haya fuente_url o fuente_autor_url, citá los enlaces oficiales relevantes.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "sql_results", "type": "function", "function": {"name": "consulta_leyes", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "sql_results", "content": results_str}
        ]
        
        client = self._get_openai_client()
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.3,
            max_completion_tokens=4000,
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
            # Permite ejecutar el código también sobre una base aún no enriquecida.
            details = str(e)
            if "no such table" in details.lower():
                return SkillResult(
                    response=(
                        "Los datos necesarios para esa consulta no están disponibles "
                        "en esta instalación. No puedo confirmar la autoría o el bloque "
                        "sin consultar los registros correspondientes."
                    ),
                    sources=[],
                    metadata={"error": "missing_parliamentary_tables", "details": details}
                )
            return SkillResult(
                response=(
                    "No pude completar esa consulta sobre la base de datos. "
                    "Probá reformularla o preguntarme directamente por el contenido de una ley."
                ),
                sources=[],
                metadata={"error": "db_error", "details": details}
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
