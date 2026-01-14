"""
skills/sql_leyes/test_sql_skill.py
===================================
Tests unitarios para la skill de consultas SQL.

Ejecutar con: pytest test_sql_skill.py -v
"""

import pytest
from pathlib import Path

from skills.sql_leyes import SQLLeyesSkill, SQLLeyesInput, QueryType
from skills.sql_leyes.config import DB_PATH


class TestSQLLeyesSkill:
    """Tests para SQLLeyesSkill."""
    
    @pytest.fixture
    def skill(self):
        """Fixture que retorna una instancia de la skill."""
        return SQLLeyesSkill()
    
    def test_skill_metadata(self, skill):
        """Test que verifica metadata de la skill."""
        assert skill.name == "sql_leyes"
        assert len(skill.description) > 0
        assert "SQL" in skill.description or "sql" in skill.description
    
    def test_database_exists(self):
        """Test que verifica que la base de datos existe."""
        assert DB_PATH.exists(), f"Base de datos no encontrada: {DB_PATH}"
    
    def test_validate_readonly_query_select(self, skill):
        """Test que valida queries SELECT válidas."""
        valid_queries = [
            "SELECT * FROM leyes",
            "SELECT COUNT(*) FROM leyes WHERE year = 2024",
            "select id, tipo_norma from leyes limit 10",
            "SELECT * FROM leyes WHERE diputados_firmantes LIKE '%test%'",
        ]
        
        for query in valid_queries:
            assert skill._validate_readonly_query(query), f"Query debería ser válida: {query}"
    
    def test_validate_readonly_query_forbidden(self, skill):
        """Test que rechaza queries con operaciones de escritura."""
        forbidden_queries = [
            "DROP TABLE leyes",
            "DELETE FROM leyes WHERE id = 1",
            "UPDATE leyes SET year = 2025",
            "INSERT INTO leyes VALUES (...)",
            "ALTER TABLE leyes ADD COLUMN test TEXT",
            "TRUNCATE TABLE leyes",
        ]
        
        for query in forbidden_queries:
            assert not skill._validate_readonly_query(query), f"Query debería ser rechazada: {query}"
    
    def test_validate_readonly_query_with_comments(self, skill):
        """Test que valida queries con comentarios."""
        # Query válida con comentario que contiene keyword prohibida
        query = """
        -- This is a comment with DROP keyword
        SELECT * FROM leyes
        /* Another comment with DELETE */
        WHERE year = 2024
        """
        assert skill._validate_readonly_query(query)
    
    def test_custom_query_valid(self, skill):
        """Test de query personalizada válida."""
        result = skill.execute(SQLLeyesInput(
            query_type=QueryType.CUSTOM,
            custom_query="SELECT COUNT(*) as total FROM leyes"
        ))
        
        assert result.success
        assert "rows" in result.data
        assert len(result.data["rows"]) > 0
        assert "total" in result.data["rows"][0]
    
    def test_custom_query_invalid(self, skill):
        """Test de query personalizada inválida (no read-only)."""
        result = skill.execute(SQLLeyesInput(
            query_type=QueryType.CUSTOM,
            custom_query="DROP TABLE leyes"
        ))
        
        assert not result.success
        assert result.error is not None
        assert "read-only" in result.error.lower() or "no permitida" in result.error.lower()
    
    def test_custom_query_sql_error(self, skill):
        """Test de query con error SQL."""
        result = skill.execute(SQLLeyesInput(
            query_type=QueryType.CUSTOM,
            custom_query="SELECT * FROM tabla_que_no_existe"
        ))
        
        assert not result.success
        assert result.error is not None
    
    def test_count_query_no_match(self, skill):
        """Test de COUNT con nombre que no existe."""
        result = skill.execute(SQLLeyesInput(
            query_type=QueryType.COUNT,
            diputado_nombre="Nombre Que No Existe En La Base De Datos XYZ123"
        ))
        
        # Debería fallar porque no encuentra el nombre
        assert not result.success
        assert "no se encontró" in result.error.lower()
    
    def test_input_validation_count_without_name(self):
        """Test que valida que COUNT requiere diputado_nombre."""
        with pytest.raises(ValueError):
            SQLLeyesInput(
                query_type=QueryType.COUNT,
                diputado_nombre=""  # Vacío
            )
    
    def test_input_validation_custom_without_query(self):
        """Test que valida que CUSTOM requiere custom_query."""
        with pytest.raises(ValueError):
            SQLLeyesInput(
                query_type=QueryType.CUSTOM,
                custom_query=""  # Vacío
            )
    
    def test_input_validation_fuzzy_threshold(self):
        """Test que valida el rango de fuzzy_threshold."""
        # Válido
        input_valid = SQLLeyesInput(
            query_type=QueryType.COUNT,
            diputado_nombre="Test",
            fuzzy_threshold=0.5
        )
        assert input_valid.fuzzy_threshold == 0.5
        
        # Inválido (fuera de rango)
        with pytest.raises(ValueError):
            SQLLeyesInput(
                query_type=QueryType.COUNT,
                diputado_nombre="Test",
                fuzzy_threshold=1.5  # > 1.0
            )
    
    def test_input_validation_limit(self):
        """Test que valida el rango de limit."""
        # Válido
        input_valid = SQLLeyesInput(
            query_type=QueryType.LIST,
            diputado_nombre="Test",
            limit=50
        )
        assert input_valid.limit == 50
        
        # Inválido (fuera de rango)
        with pytest.raises(ValueError):
            SQLLeyesInput(
                query_type=QueryType.LIST,
                diputado_nombre="Test",
                limit=0  # < 1
            )
        
        with pytest.raises(ValueError):
            SQLLeyesInput(
                query_type=QueryType.LIST,
                diputado_nombre="Test",
                limit=200  # > 100
            )
    
    def test_to_llamaindex_tool(self, skill):
        """Test de conversión a formato LlamaIndex."""
        tool_dict = skill.to_llamaindex_tool()
        
        assert "name" in tool_dict
        assert "description" in tool_dict
        assert "execute" in tool_dict
        assert tool_dict["name"] == skill.name
        assert callable(tool_dict["execute"])


class TestFuzzyMatching:
    """Tests específicos para fuzzy matching."""
    
    @pytest.fixture
    def skill(self):
        return SQLLeyesSkill()
    
    def test_fuzzy_matching_exact(self, skill):
        """Test de fuzzy matching con nombre exacto."""
        # Este test requiere que exista al menos un diputado en la BD
        # Si la BD está vacía, el test se saltará
        
        # Primero obtener un nombre real de la BD
        conn = skill._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT diputados_firmantes 
            FROM leyes 
            WHERE diputados_firmantes IS NOT NULL 
            AND diputados_firmantes != ''
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            pytest.skip("No hay diputados en la base de datos")
        
        # Tomar el primer nombre
        first_name = result[0].split(',')[0].strip()
        
        # Buscar con nombre exacto
        matched = skill._find_diputado_name(first_name, threshold=0.9)
        assert matched is not None
        assert matched == first_name
    
    def test_fuzzy_matching_threshold(self, skill):
        """Test de diferentes thresholds de fuzzy matching."""
        # Con threshold muy alto (0.95), nombres diferentes no deberían matchear
        matched = skill._find_diputado_name(
            "Nombre Completamente Diferente XYZ",
            threshold=0.95
        )
        assert matched is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
