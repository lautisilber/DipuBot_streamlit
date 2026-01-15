# ETL - Leyes Argentinas con LlamaIndex

Pipeline ETL para crear un índice vectorial de leyes argentinas usando **LlamaIndex**.

## ¿Qué hace?

1. Lee leyes desde una base de datos SQLite
2. Aplica chunking inteligente respetando la estructura legal (artículos, capítulos, etc.)
3. Genera embeddings con OpenAI
4. Persiste el índice FAISS usando las abstracciones de LlamaIndex

## Requisitos

- Python 3.9+
- API Key de OpenAI
- Base de datos SQLite con las leyes

## Instalación

```bash
# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o en Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Crea un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```env
OPENAI_API_KEY=sk-tu-api-key-aqui
DATABASE_PATH=../data/raw/leyes-2023-2025_12_20.sqlite3
FAISS_OUTPUT_DIR=../data/indexed
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

## Ejecutar el ETL

```bash
python run_etl.py
```

El script:
- Conectará a la base de datos SQLite
- Chunkeará cada ley respetando artículos y secciones
- Generará embeddings para cada chunk
- Guardará el índice en `FAISS_OUTPUT_DIR/llama_index_YYYYMMDD_HHMMSS/`

## Estructura de salida

```
data/indexed/
└── llama_index_20260112_203500/
    ├── default__vector_store.json   # Índice FAISS
    ├── docstore.json                # Documentos/chunks
    ├── index_store.json             # Metadatos del índice
    └── graph_store.json             # Graph store (vacío para este caso)
```

## Uso posterior (módulo chat)

El índice persistido puede cargarse así:

```python
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.vector_stores.faiss import FaissVectorStore

# Cargar el índice
storage_context = StorageContext.from_defaults(
    persist_dir="./data/indexed/llama_index_YYYYMMDD_HHMMSS"
)
index = load_index_from_storage(storage_context)

# Crear query engine
query_engine = index.as_query_engine()
response = query_engine.query("¿Qué dice la ley sobre...?")
print(response)
```

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `run_etl.py` | Script principal del ETL |
| `splitters.py` | Chunking inteligente para textos legales |
| `search.py` | Utilidad de búsqueda (legacy, usar query_engine de LlamaIndex) |
| `requirements.txt` | Dependencias Python |

## Chunking de leyes

El `LegalSplitter` divide textos largos:
- Busca límites naturales: ARTÍCULO, Capítulo, Título
- Chunks de ~24000 caracteres (~6000 tokens)
- Overlap de 500 caracteres para contexto

**Nota**: Al recuperar información, la metadata de cada chunk incluye `chunk_index` y `total_chunks`, lo que permite reconstruir la ley completa si es necesario.
