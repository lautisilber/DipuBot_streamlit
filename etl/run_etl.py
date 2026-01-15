"""
ETL: Leyes Argentinas -> LlamaIndex VectorStore
------------------------------------------------
Pipeline para:
1. Leer base de datos SQLite de leyes
2. Generar embeddings con OpenAI
3. Almacenar en índice vectorial FAISS con LlamaIndex
4. Persistir para uso posterior en el módulo "chat"
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
from tqdm import tqdm

from llama_index.core import VectorStoreIndex, Document, StorageContext, Settings
from llama_index.core.schema import TextNode
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
import faiss

from splitters import get_splitter


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", "../data/raw/leyes-2023-2025_12_20.sqlite3")
FAISS_OUTPUT_DIR = os.getenv("FAISS_OUTPUT_DIR", "../data/indexed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

# Columnas que van como metadata (todas menos texto_original que es el contenido)
METADATA_COLUMNS = [
    "id", "id_norma", "tipo_norma", "numero_norma", "clase_norma",
    "organismo_origen", "fecha_sancion", "numero_boletin", "fecha_boletin",
    "pagina_boletin", "titulo_resumido", "titulo_sumario", "texto_resumido",
    "observaciones", "texto_actualizado", "texto_original_link",
    "texto_actualizado_link", "numero_ley_original", "numero_ley_actualizado", "year"
]

TEXT_COLUMN = "texto_original"


# ============================================================================
# FUNCIONES DE CHUNKING (usando nuestro LegalSplitter)
# ============================================================================

def documents_to_nodes(documents: List[Document], splitter_type: str = "legal") -> List[TextNode]:
    """
    Convierte Documents de LlamaIndex a TextNodes usando nuestro splitter legal.
    Mantiene el chunking inteligente por artículos/secciones legales.
    """
    splitter = get_splitter(splitter_type)
    all_nodes = []
    
    for doc in tqdm(documents, desc="Aplicando chunking legal"):
        text = doc.get_content()
        metadata = doc.metadata.copy()
        
        # Usar nuestro splitter
        chunks = splitter.split(text, metadata)
        
        for chunk in chunks:
            text_node = TextNode(
                text=chunk.text,
                metadata={
                    **chunk.metadata,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "doc_id": doc.doc_id,
                }
            )
            all_nodes.append(text_node)
    
    return all_nodes





# ============================================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================================

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Abre conexión a la base de datos SQLite."""
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    
    conn = sqlite3.Connection(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all_documents(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Obtiene todos los documentos de la tabla leyes."""
    cursor = conn.cursor()
    
    all_columns = METADATA_COLUMNS + [TEXT_COLUMN]
    columns_str = ", ".join(all_columns)
    
    query = f"SELECT {columns_str} FROM leyes WHERE {TEXT_COLUMN} IS NOT NULL AND {TEXT_COLUMN} != ''"
    cursor.execute(query)
    
    documents = []
    for row in cursor.fetchall():
        doc = dict(row)
        documents.append(doc)
    
    return documents


def convert_to_llama_documents(db_documents: List[Dict[str, Any]]) -> List[Document]:
    """Convierte documentos de la BD a Documents de LlamaIndex."""
    llama_docs = []
    
    for doc in tqdm(db_documents, desc="Convirtiendo a Documents"):
        text = doc.get(TEXT_COLUMN, "")
        if not text or not text.strip():
            continue
        
        # Metadata: todas las columnas excepto texto_original
        metadata = {col: doc.get(col) for col in METADATA_COLUMNS}
        # Convertir valores None a string para evitar problemas
        metadata = {k: (str(v) if v is not None else "") for k, v in metadata.items()}
        
        llama_docs.append(Document(
            text=text,
            metadata=metadata,
            doc_id=str(doc["id"])
        ))
    
    return llama_docs


# ============================================================================
# MAIN
# ============================================================================

def run_etl(
    db_path: str = DATABASE_PATH,
    output_dir: str = FAISS_OUTPUT_DIR,
    splitter_type: str = "legal"
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline ETL completo usando LlamaIndex.
    """
    print("=" * 60)
    print("🚀 ETL: Leyes Argentinas -> LlamaIndex VectorStore")
    print("=" * 60)
    
    # Resolver paths relativos
    script_dir = Path(__file__).parent
    db_path_resolved = (script_dir / db_path).resolve()
    output_dir_resolved = (script_dir / output_dir).resolve()
    
    print(f"\n📂 Base de datos: {db_path_resolved}")
    print(f"📂 Output: {output_dir_resolved}")
    print(f"🔤 Modelo embeddings: {EMBEDDING_MODEL}")
    
    # Paso 1: Conectar a BD y obtener documentos
    print("\n[1/4] Conectando a base de datos...")
    conn = get_db_connection(str(db_path_resolved))
    db_documents = fetch_all_documents(conn)
    conn.close()
    print(f"✅ {len(db_documents)} documentos cargados")
    
    # Paso 2: Convertir a Documents de LlamaIndex
    print("\n[2/4] Preparando documentos...")
    llama_docs = convert_to_llama_documents(db_documents)
    print(f"✅ {len(llama_docs)} documentos válidos")
    
    # Paso 3: Configurar LlamaIndex
    print("\n[3/4] Configurando LlamaIndex y creando índice...")
    
    # Configurar embedding model globalmente
    embed_model = OpenAIEmbedding(
        model=EMBEDDING_MODEL,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    Settings.embed_model = embed_model
    
    # Crear FAISS vector store
    faiss_index = faiss.IndexFlatL2(EMBEDDING_DIMENSIONS)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # Convertir a nodes usando nuestro splitter legal
    nodes = documents_to_nodes(llama_docs, splitter_type=splitter_type)
    print(f"📊 Total chunks creados: {len(nodes)}")
    
    # Crear índice (esto genera los embeddings automáticamente)
    print("🔧 Generando embeddings y creando índice...")
    index = VectorStoreIndex(
        nodes=nodes,
        storage_context=storage_context,
        show_progress=True
    )
    
    # Paso 4: Persistir índice
    print("\n[4/4] Guardando índice...")
    output_dir_resolved.mkdir(parents=True, exist_ok=True)
    
    # Guardar con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    persist_dir = output_dir_resolved / f"llama_index_{timestamp}"
    
    index.storage_context.persist(persist_dir=str(persist_dir))
    
    print(f"💾 Índice guardado en: {persist_dir}")
    
    print("\n" + "=" * 60)
    print("✅ ETL completado exitosamente!")
    print("=" * 60)
    
    return {
        "documents_processed": len(db_documents),
        "chunks_created": len(nodes),
        "persist_dir": str(persist_dir)
    }


if __name__ == "__main__":
    result = run_etl()
    print(f"\n📊 Resumen:")
    print(f"   - Documentos procesados: {result['documents_processed']}")
    print(f"   - Chunks creados: {result['chunks_created']}")
    print(f"   - Índice guardado en: {result['persist_dir']}")