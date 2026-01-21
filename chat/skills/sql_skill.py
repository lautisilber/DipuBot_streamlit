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

=== TABLAS DE FIRMANTES Y BLOQUES ===

Tabla: firmantes
- id (INTEGER, PRIMARY KEY)
- nombre (TEXT, UNIQUE): Nombre completo del diputado/senador (ej: "FERNANDEZ, ALBERTO")

Tabla: bloques (partidos políticos)
- id (INTEGER, PRIMARY KEY)
- nombre (TEXT, UNIQUE): Nombre del bloque (ej: "PRO", "FRENTE DE TODOS", "UCR")

Tabla: afiliaciones (relación firmante ↔ bloque en un momento dado)
- id (INTEGER, PRIMARY KEY)
- firmante_id (INTEGER, FK → firmantes.id)
- bloque_id (INTEGER, FK → bloques.id)
- fecha (TEXT): Fecha de la afiliación (YYYY-MM-DD)
- distrito (TEXT): Distrito electoral

=== TABLA DE DATOS EXTENDIDOS DE LEYES ===

Tabla: leyes_data (metadata adicional de cada ley)
- id (INTEGER, PRIMARY KEY)
- ley_id (INTEGER, FK → leyes.id)
- iniciado_en (TEXT): Cámara donde se inició
- expediente_diputados (TEXT): Número de expediente en Diputados
- expediente_senado (TEXT): Número de expediente en Senado
- publicado_en (TEXT): Dónde fue publicado
- fecha_proyecto (TEXT): Fecha del proyecto (YYYY-MM-DD)

=== TABLAS DE RELACIÓN MANY-TO-MANY ===

Tabla: leyes_data_afiliaciones (vincula leyes con sus firmantes)
- ley_data_id (INTEGER, FK → leyes_data.id)
- afiliacion_id (INTEGER, FK → afiliaciones.id)

Tabla: leyes_data_comisiones_diputados
- ley_data_id (INTEGER, FK → leyes_data.id)
- comision_diputado_id (INTEGER, FK → comisiones_diputados.id)

=== TABLAS DE COMISIONES ===

Tabla: comisiones_diputados
- id (INTEGER, PRIMARY KEY)
- name (TEXT): Nombre de la comisión

Tabla: comisiones_senado
- id (INTEGER, PRIMARY KEY)
- name (TEXT): Nombre de la comisión

=== TABLAS DE TRÁMITES Y DICTÁMENES ===

Tabla: dictamenes
- id (INTEGER, PRIMARY KEY)
- ley_data_id (INTEGER, FK → leyes_data.id)
- camara (TEXT): 'Diputados' o 'Senado'
- dictamen (TEXT): Contenido del dictamen
- fecha (TEXT): Fecha (YYYY-MM-DD)

Tabla: tramites
- id (INTEGER, PRIMARY KEY)
- ley_data_id (INTEGER, FK → leyes_data.id)
- camara (TEXT): 'Diputados' o 'Senado'
- fecha (TEXT): Fecha (YYYY-MM-DD)
- resultado (TEXT): Resultado del trámite

=== PATRONES DE JOIN COMUNES ===

Para buscar leyes por nombre de firmante (usar LIKE para fuzzy matching):
SELECT DISTINCT l.numero_norma, l.titulo_resumido, l.year, f.nombre
FROM leyes l
JOIN leyes_data ld ON ld.ley_id = l.id
JOIN leyes_data_afiliaciones lda ON lda.ley_data_id = ld.id
JOIN afiliaciones a ON a.id = lda.afiliacion_id
JOIN firmantes f ON f.id = a.firmante_id
WHERE f.nombre LIKE '%APELLIDO%'
ORDER BY l.year DESC;

Para buscar leyes por bloque/partido político:
SELECT DISTINCT l.numero_norma, l.titulo_resumido, l.year, b.nombre as bloque
FROM leyes l
JOIN leyes_data ld ON ld.ley_id = l.id
JOIN leyes_data_afiliaciones lda ON lda.ley_data_id = ld.id
JOIN afiliaciones a ON a.id = lda.afiliacion_id
JOIN bloques b ON b.id = a.bloque_id
WHERE b.nombre LIKE '%NOMBRE_BLOQUE%';

Para contar leyes por firmante:
SELECT f.nombre, COUNT(DISTINCT l.id) as cantidad_leyes
FROM firmantes f
JOIN afiliaciones a ON a.firmante_id = f.id
JOIN leyes_data_afiliaciones lda ON lda.afiliacion_id = a.id
JOIN leyes_data ld ON ld.id = lda.ley_data_id
JOIN leyes l ON l.id = ld.ley_id
GROUP BY f.id
ORDER BY cantidad_leyes DESC;
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
    Usar los JOINs documentados: leyes → leyes_data → leyes_data_afiliaciones → afiliaciones → firmantes
11. BÚSQUEDA POR BLOQUE/PARTIDO: Usar LIKE para buscar en bloques.nombre
    Ejemplos de bloques: "PRO", "FRENTE DE TODOS", "UCR", "JUNTOS POR EL CAMBIO"
12. Siempre usar SELECT DISTINCT cuando hay JOINs para evitar duplicados
13. Ordenar resultados por año DESC cuando sea relevante"""

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
