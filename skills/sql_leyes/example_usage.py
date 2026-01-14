"""
skills/sql_leyes/example_usage.py
==================================
Ejemplos de uso de la skill de consultas SQL.

Este script demuestra cómo usar la skill en diferentes escenarios.
"""

from skills.sql_leyes import SQLLeyesSkill, SQLLeyesInput, QueryType


def main():
    """Ejecuta ejemplos de uso de la skill."""
    print("=" * 60)
    print("SQL Leyes Skill - Ejemplos de Uso")
    print("=" * 60)
    
    # Crear instancia de la skill
    skill = SQLLeyesSkill()
    
    # Ejemplo 1: Contar leyes de un diputado
    print("\n[Ejemplo 1] COUNT - Contar leyes de un diputado")
    print("-" * 60)
    
    # NOTA: Reemplazar con un nombre real de la base de datos
    result = skill.execute(SQLLeyesInput(
        query_type=QueryType.COUNT,
        diputado_nombre="Juan Pérez"  # Cambiar por nombre real
    ))
    
    print(f"Success: {result.success}")
    if result.success:
        print(f"Diputado: {result.data['diputado']}")
        print(f"Cantidad de leyes: {result.data['count']}")
        print(f"Nombre exacto encontrado: {result.matched_name}")
    else:
        print(f"Error: {result.error}")
    
    # Ejemplo 2: Última ley de un diputado
    print("\n[Ejemplo 2] LAST - Última ley de un diputado")
    print("-" * 60)
    
    result = skill.execute(SQLLeyesInput(
        query_type=QueryType.LAST,
        diputado_nombre="María González"  # Cambiar por nombre real
    ))
    
    print(f"Success: {result.success}")
    if result.success:
        ley = result.data.get('ley')
        if ley:
            print(f"Última ley: {ley['tipo_norma']} {ley['numero_norma']}")
            print(f"Título: {ley['titulo_resumido']}")
            print(f"Fecha: {ley['fecha_sancion']}")
        else:
            print("No se encontraron leyes para este diputado")
    else:
        print(f"Error: {result.error}")
    
    # Ejemplo 3: Listar leyes de un diputado
    print("\n[Ejemplo 3] LIST - Listar leyes de un diputado")
    print("-" * 60)
    
    result = skill.execute(SQLLeyesInput(
        query_type=QueryType.LIST,
        diputado_nombre="Pedro Martínez",  # Cambiar por nombre real
        limit=5
    ))
    
    print(f"Success: {result.success}")
    if result.success:
        leyes = result.data.get('leyes', [])
        print(f"Total de leyes encontradas: {result.data['count']}")
        for i, ley in enumerate(leyes, 1):
            print(f"  {i}. {ley['tipo_norma']} {ley['numero_norma']} - {ley['titulo_resumido']}")
    else:
        print(f"Error: {result.error}")
    
    # Ejemplo 4: Query personalizada
    print("\n[Ejemplo 4] CUSTOM - Query SQL personalizada")
    print("-" * 60)
    
    result = skill.execute(SQLLeyesInput(
        query_type=QueryType.CUSTOM,
        custom_query="SELECT year, COUNT(*) as total FROM leyes GROUP BY year ORDER BY year DESC LIMIT 5"
    ))
    
    print(f"Success: {result.success}")
    if result.success:
        rows = result.data.get('rows', [])
        print("Leyes por año:")
        for row in rows:
            print(f"  {row['year']}: {row['total']} leyes")
    else:
        print(f"Error: {result.error}")
    
    # Ejemplo 5: Fuzzy matching con typo
    print("\n[Ejemplo 5] Fuzzy matching con nombre mal escrito")
    print("-" * 60)
    
    result = skill.execute(SQLLeyesInput(
        query_type=QueryType.COUNT,
        diputado_nombre="Juan Perez",  # Sin tilde
        fuzzy_threshold=0.6
    ))
    
    print(f"Success: {result.success}")
    if result.success:
        print(f"Nombre buscado: 'Juan Perez'")
        print(f"Nombre encontrado: '{result.matched_name}'")
        print(f"Cantidad de leyes: {result.data['count']}")
    else:
        print(f"Error: {result.error}")
    
    # Ejemplo 6: Query no permitida (seguridad)
    print("\n[Ejemplo 6] Validación de seguridad - Query no permitida")
    print("-" * 60)
    
    result = skill.execute(SQLLeyesInput(
        query_type=QueryType.CUSTOM,
        custom_query="DROP TABLE leyes"
    ))
    
    print(f"Success: {result.success}")
    print(f"Error esperado: {result.error}")
    
    print("\n" + "=" * 60)
    print("Ejemplos completados")
    print("=" * 60)


if __name__ == "__main__":
    main()
