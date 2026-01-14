# SQL Leyes Skill

Skill para consultas SQL estructuradas sobre la base de datos de leyes argentinas.

## Descripción

Esta skill permite realizar consultas específicas a la base de datos SQLite de leyes sin usar RAG. Es ideal para preguntas que requieren datos estructurados como:

- ¿Cuántas leyes presentó el diputado X?
- ¿Cuál fue la última ley del diputado Y?
- Listar todas las leyes de un diputado

## Características

- ✅ **Fuzzy matching**: Encuentra nombres de diputados incluso con errores de escritura
- ✅ **Seguridad**: Solo permite queries read-only (SELECT)
- ✅ **Flexible**: Soporta múltiples tipos de consultas
- ✅ **Compatible con LlamaIndex**: Diseñada para futura integración como tool

## Uso

### Instalación

No requiere instalación adicional. La skill usa las dependencias existentes del proyecto.

### Ejemplo Básico

```python
from skills.sql_leyes import SQLLeyesSkill, SQLLeyesInput, QueryType

# Crear instancia de la skill
skill = SQLLeyesSkill()

# Contar leyes de un diputado
result = skill.execute(SQLLeyesInput(
    query_type=QueryType.COUNT,
    diputado_nombre="Juan Pérez"  # Soporta fuzzy matching
))

if result.success:
    print(f"Leyes encontradas: {result.data['count']}")
    print(f"Nombre exacto: {result.matched_name}")
else:
    print(f"Error: {result.error}")
```

## Tipos de Consultas

### 1. COUNT - Contar leyes

Cuenta cuántas leyes tiene un diputado como firmante.

```python
result = skill.execute(SQLLeyesInput(
    query_type=QueryType.COUNT,
    diputado_nombre="María González"
))

# Output:
# {
#     "success": True,
#     "data": {
#         "count": 15,
#         "diputado": "María González"
#     },
#     "matched_name": "María González"
# }
```

### 2. LAST - Última ley

Obtiene la última ley (más reciente) de un diputado.

```python
result = skill.execute(SQLLeyesInput(
    query_type=QueryType.LAST,
    diputado_nombre="Pedro Martínez"
))

# Output:
# {
#     "success": True,
#     "data": {
#         "ley": {
#             "id": 123,
#             "tipo_norma": "LEY",
#             "numero_norma": "27.742",
#             "titulo_resumido": "Presupuesto 2024",
#             "fecha_sancion": "2024-12-15",
#             "year": 2024,
#             "diputados_firmantes": "Pedro Martínez, Ana López"
#         },
#         "diputado": "Pedro Martínez"
#     },
#     "matched_name": "Pedro Martínez"
# }
```

### 3. LIST - Listar leyes

Lista todas las leyes de un diputado (con límite configurable).

```python
result = skill.execute(SQLLeyesInput(
    query_type=QueryType.LIST,
    diputado_nombre="Ana López",
    limit=5  # Máximo 5 leyes
))

# Output:
# {
#     "success": True,
#     "data": {
#         "leyes": [...],  # Lista de LeyInfo
#         "count": 5,
#         "diputado": "Ana López"
#     },
#     "matched_name": "Ana López"
# }
```

### 4. CUSTOM - Query personalizada

Ejecuta una query SQL personalizada (solo SELECT, validada).

```python
result = skill.execute(SQLLeyesInput(
    query_type=QueryType.CUSTOM,
    custom_query="SELECT COUNT(*) as total FROM leyes WHERE year = 2024"
))

# Output:
# {
#     "success": True,
#     "data": {
#         "rows": [{"total": 42}],
#         "count": 1
#     }
# }
```

## Fuzzy Matching

La skill usa fuzzy matching para encontrar nombres de diputados incluso con errores:

```python
# Estos nombres encontrarán el mismo diputado:
# - "Juan Perez" (sin tilde)
# - "Juan Pérez" (con tilde)
# - "juan perez" (minúsculas)
# - "J. Perez" (abreviado - si el threshold lo permite)

result = skill.execute(SQLLeyesInput(
    query_type=QueryType.COUNT,
    diputado_nombre="Juan Perez",  # Sin tilde
    fuzzy_threshold=0.6  # 0.0 = exacto, 1.0 = muy permisivo
))
```

## Seguridad

La skill valida que todas las queries sean read-only:

```python
# ❌ Esto fallará
result = skill.execute(SQLLeyesInput(
    query_type=QueryType.CUSTOM,
    custom_query="DROP TABLE leyes"
))
# Output: {"success": False, "error": "Query no permitida..."}

# ✅ Esto funcionará
result = skill.execute(SQLLeyesInput(
    query_type=QueryType.CUSTOM,
    custom_query="SELECT * FROM leyes LIMIT 10"
))
```

## Schemas

### Input: `SQLLeyesInput`

```python
class SQLLeyesInput(SkillInput):
    query_type: QueryType  # COUNT, LAST, LIST, CUSTOM
    diputado_nombre: Optional[str]  # Requerido para COUNT, LAST, LIST
    custom_query: Optional[str]  # Requerido para CUSTOM
    fuzzy_threshold: float = 0.6  # Umbral fuzzy matching (0.0-1.0)
    limit: int = 10  # Límite para LIST (1-100)
```

### Output: `SQLLeyesOutput`

```python
class SQLLeyesOutput(SkillOutput):
    success: bool  # True si la query se ejecutó correctamente
    data: Dict[str, Any]  # Datos resultantes (estructura varía por query_type)
    matched_name: Optional[str]  # Nombre exacto encontrado (fuzzy matching)
    error: Optional[str]  # Mensaje de error si success=False
    query_executed: Optional[str]  # Query SQL ejecutada (debugging)
```

## Integración con LlamaIndex

La skill está diseñada para ser compatible con LlamaIndex. Cuando se migre el chat:

```python
# Futuro uso con LlamaIndex
from llama_index.core.tools import FunctionTool

skill = SQLLeyesSkill()
tool = FunctionTool.from_defaults(
    fn=skill.execute,
    name=skill.name,
    description=skill.description
)
```

## Testing

Ejecutar tests:

```bash
cd skills/sql_leyes
python -m pytest test_sql_skill.py -v
```

O ejecutar el ejemplo de uso:

```bash
python example_usage.py
```

## Configuración

Editar `config.py` para cambiar:

- Path a la base de datos
- Threshold de fuzzy matching por defecto
- Queries predefinidas

## Limitaciones

- Solo consultas read-only (SELECT)
- Requiere que la columna `diputados_firmantes` exista en la tabla `leyes`
- Fuzzy matching puede fallar con nombres muy diferentes
- Límite máximo de 100 resultados para LIST

## Casos de Uso

### Chatbot

```python
# El chatbot decide usar esta skill cuando detecta preguntas sobre:
# - Conteo de leyes
# - Búsqueda por diputado
# - Queries estructuradas

user_query = "¿Cuántas leyes presentó el diputado Pérez?"
# → Usar SQLLeyesSkill con QueryType.COUNT

user_query = "¿Cuál fue la última ley de González?"
# → Usar SQLLeyesSkill con QueryType.LAST

user_query = "¿Qué dice el artículo 14 bis?"
# → Usar RAG (no esta skill)
```

## Estructura de Archivos

```
skills/sql_leyes/
├── __init__.py          # Exports
├── skill.py             # Implementación principal
├── schemas.py           # Pydantic schemas
├── config.py            # Configuración
├── README.md            # Esta documentación
├── test_sql_skill.py    # Tests unitarios
└── example_usage.py     # Ejemplos de uso
```
