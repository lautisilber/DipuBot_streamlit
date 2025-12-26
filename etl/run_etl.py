"""
ETL: Leyes Argentinas -> Embeddings -> FAISS
---------------------------------------------
Pipeline para:
1. Leer base de datos SQLite de leyes
2. Generar embeddings con OpenAI
3. Almacenar metadata
4. Guardar índice FAISS con timestamp
"""

import os
import sqlite3
import json
import numpy as np
import faiss
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

from splitters import get_splitter, TextChunk


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", "../data/raw/leyes-2023-2025_12_20.sqlite3")
FAISS_OUTPUT_DIR = os.getenv("FAISS_OUTPUT_DIR", "../data/indexed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

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
# CLASES DE DATOS
# ============================================================================

@dataclass
class ProcessedDocument:
    """Documento procesado con su embedding y metadata."""
    doc_id: int
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]
    chunk_index: int = 0
    total_chunks: int = 1


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
    
    # Obtener todas las columnas
    all_columns = METADATA_COLUMNS + [TEXT_COLUMN]
    columns_str = ", ".join(all_columns)
    
    query = f"SELECT {columns_str} FROM leyes WHERE {TEXT_COLUMN} IS NOT NULL AND {TEXT_COLUMN} != ''"
    cursor.execute(query)
    
    documents = []
    for row in cursor.fetchall():
        doc = dict(row)
        documents.append(doc)
    
    return documents


# ============================================================================
# FUNCIONES DE EMBEDDINGS
# ============================================================================

def create_openai_client() -> OpenAI:
    """Crea cliente de OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY no configurada en .env")
    return OpenAI(api_key=api_key)


def generate_embeddings_batch(
    client: OpenAI, 
    texts: List[str], 
    model: str = EMBEDDING_MODEL
) -> List[List[float]]:
    """Genera embeddings para un batch de textos."""
    # Limpiar textos vacíos o None
    cleaned_texts = [t if t else "" for t in texts]
    
    response = client.embeddings.create(
        input=cleaned_texts,
        model=model
    )
    
    return [item.embedding for item in response.data]


# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

def process_documents(
    documents: List[Dict[str, Any]],
    client: OpenAI,
    splitter_type: str = "legal",
    batch_size: int = BATCH_SIZE
) -> List[ProcessedDocument]:
    """
    Procesa documentos: split -> embedding -> metadata.
    """
    splitter = get_splitter(splitter_type)
    processed_docs = []
    chunks_to_embed = []
    chunk_infos = []  # Para mantener referencia doc_id, metadata, etc.
    
    print(f"\n📄 Procesando {len(documents)} documentos con splitter: {splitter.name}")
    
    # Paso 1: Crear chunks de todos los documentos
    for doc in tqdm(documents, desc="Creando chunks"):
        text = doc.get(TEXT_COLUMN, "")
        if not text or not text.strip():
            continue
        
        # Metadata: todas las columnas excepto texto_original
        metadata = {col: doc.get(col) for col in METADATA_COLUMNS}
        
        # Aplicar splitter
        chunks = splitter.split(text, metadata)
        
        for chunk in chunks:
            chunks_to_embed.append(chunk.text)
            chunk_infos.append({
                "doc_id": doc["id"],
                "metadata": chunk.metadata,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks
            })
    
    print(f"📊 Total chunks a procesar: {len(chunks_to_embed)}")
    
    # Paso 2: Generar embeddings en batches
    all_embeddings = []
    
    for i in tqdm(range(0, len(chunks_to_embed), batch_size), desc="Generando embeddings"):
        batch_texts = chunks_to_embed[i:i + batch_size]
        batch_embeddings = generate_embeddings_batch(client, batch_texts)
        all_embeddings.extend(batch_embeddings)
    
    # Paso 3: Crear ProcessedDocuments
    for idx, (text, embedding, info) in enumerate(zip(chunks_to_embed, all_embeddings, chunk_infos)):
        processed_docs.append(ProcessedDocument(
            doc_id=info["doc_id"],
            text=text,
            embedding=embedding,
            metadata=info["metadata"],
            chunk_index=info["chunk_index"],
            total_chunks=info["total_chunks"]
        ))
    
    return processed_docs


def create_faiss_index(
    processed_docs: List[ProcessedDocument],
    dimensions: int = EMBEDDING_DIMENSIONS
) -> faiss.IndexFlatL2:
    """Crea índice FAISS con los embeddings."""
    print(f"\n🔧 Creando índice FAISS con {len(processed_docs)} vectores...")
    
    # Crear matriz de embeddings
    embeddings_matrix = np.array([doc.embedding for doc in processed_docs], dtype=np.float32)
    
    # Crear índice
    index = faiss.IndexFlatL2(dimensions)
    index.add(embeddings_matrix)
    
    print(f"✅ Índice creado con {index.ntotal} vectores")
    return index


def save_faiss_index(
    index: faiss.IndexFlatL2,
    processed_docs: List[ProcessedDocument],
    output_dir: str = FAISS_OUTPUT_DIR
) -> Dict[str, str]:
    """
    Guarda el índice FAISS y metadata en disco con timestamp.
    Retorna paths de los archivos creados.
    """
    # Crear directorio si no existe
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Timestamp para nombres únicos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Paths
    index_filename = f"leyes_index_{timestamp}.faiss"
    metadata_filename = f"leyes_metadata_{timestamp}.json"
    
    index_path = output_path / index_filename
    metadata_path = output_path / metadata_filename
    
    # Guardar índice FAISS
    faiss.write_index(index, str(index_path))
    print(f"💾 Índice guardado: {index_path}")
    
    # Preparar y guardar metadata
    metadata_store = {
        "created_at": timestamp,
        "total_documents": len(processed_docs),
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimensions": EMBEDDING_DIMENSIONS,
        "documents": []
    }
    
    for idx, doc in enumerate(processed_docs):
        metadata_store["documents"].append({
            "faiss_index": idx,
            "doc_id": doc.doc_id,
            "text_preview": doc.text[:500] + "..." if len(doc.text) > 500 else doc.text,
            "chunk_index": doc.chunk_index,
            "total_chunks": doc.total_chunks,
            "metadata": doc.metadata
        })
    
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_store, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"💾 Metadata guardada: {metadata_path}")
    
    return {
        "index_path": str(index_path),
        "metadata_path": str(metadata_path)
    }


# ============================================================================
# MAIN
# ============================================================================

def run_etl(
    db_path: str = DATABASE_PATH,
    output_dir: str = FAISS_OUTPUT_DIR,
    splitter_type: str = "legal",
    batch_size: int = BATCH_SIZE
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline ETL completo.
    """
    print("=" * 60)
    print("🚀 ETL: Leyes Argentinas -> Embeddings -> FAISS")
    print("=" * 60)
    
    # Resolver paths relativos
    script_dir = Path(__file__).parent
    db_path_resolved = (script_dir / db_path).resolve()
    output_dir_resolved = (script_dir / output_dir).resolve()
    
    print(f"\n📂 Base de datos: {db_path_resolved}")
    print(f"📂 Output: {output_dir_resolved}")
    print(f"🔤 Modelo embeddings: {EMBEDDING_MODEL}")
    print(f"📦 Batch size: {batch_size}")
    
    # Paso 1: Conectar a BD y obtener documentos
    print("\n[1/4] Conectando a base de datos...")
    conn = get_db_connection(str(db_path_resolved))
    documents = fetch_all_documents(conn)
    conn.close()
    print(f"✅ {len(documents)} documentos cargados")
    
    # Paso 2: Crear cliente OpenAI y procesar
    print("\n[2/4] Procesando documentos y generando embeddings...")
    client = create_openai_client()
    processed_docs = process_documents(
        documents, 
        client, 
        splitter_type=splitter_type,
        batch_size=batch_size
    )
    
    # Paso 3: Crear índice FAISS
    print("\n[3/4] Creando índice FAISS...")
    index = create_faiss_index(processed_docs)
    
    # Paso 4: Guardar en disco
    print("\n[4/4] Guardando en disco...")
    paths = save_faiss_index(index, processed_docs, str(output_dir_resolved))
    
    print("\n" + "=" * 60)
    print("✅ ETL completado exitosamente!")
    print("=" * 60)
    
    return {
        "documents_processed": len(documents),
        "chunks_created": len(processed_docs),
        "index_path": paths["index_path"],
        "metadata_path": paths["metadata_path"]
    }


if __name__ == "__main__":
    result = run_etl()
    print(f"\n📊 Resumen:")
    print(f"   - Documentos procesados: {result['documents_processed']}")
    print(f"   - Chunks creados: {result['chunks_created']}")
    print(f"   - Índice: {result['index_path']}")
    print(f"   - Metadata: {result['metadata_path']}")