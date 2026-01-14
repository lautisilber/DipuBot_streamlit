"""
skills/sql_leyes/config.py
===========================
Configuración para la skill de consultas SQL.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Path a la base de datos SQLite
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "leyes-2023-2025_12_20.sqlite3"

# Configuración de fuzzy matching
DEFAULT_FUZZY_THRESHOLD = 0.6  # Umbral para considerar un match válido

# Configuración de seguridad
ALLOWED_SQL_KEYWORDS = {"SELECT", "FROM", "WHERE", "AND", "OR", "LIKE", "IN", "ORDER", "BY", "LIMIT", "GROUP", "HAVING", "AS", "JOIN", "ON", "COUNT", "MAX", "MIN", "AVG", "SUM"}
FORBIDDEN_SQL_KEYWORDS = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "REPLACE", "GRANT", "REVOKE"}

# Queries predefinidas
PREDEFINED_QUERIES = {
    "count_by_diputado": """
        SELECT COUNT(*) as count
        FROM leyes
        WHERE diputados_firmantes LIKE ?
    """,
    
    "last_by_diputado": """
        SELECT id, tipo_norma, numero_norma, titulo_resumido, 
               fecha_sancion, year, diputados_firmantes
        FROM leyes
        WHERE diputados_firmantes LIKE ?
        ORDER BY fecha_sancion DESC, id DESC
        LIMIT 1
    """,
    
    "list_by_diputado": """
        SELECT id, tipo_norma, numero_norma, titulo_resumido,
               fecha_sancion, year, diputados_firmantes
        FROM leyes
        WHERE diputados_firmantes LIKE ?
        ORDER BY fecha_sancion DESC, id DESC
        LIMIT ?
    """,
}
