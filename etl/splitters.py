"""
Splitters Module
----------------
Módulo para dividir textos en chunks para procesamiento de embeddings.
Por ahora incluye un dummy_splitter que no divide nada (1 doc = 1 chunk).
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Representa un chunk de texto con su metadata."""
    text: str
    metadata: Dict[str, Any]
    chunk_index: int = 0
    total_chunks: int = 1


class BaseSplitter:
    """Clase base para splitters."""
    
    def split(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        raise NotImplementedError


class DummySplitter(BaseSplitter):
    """
    Splitter que no divide el texto.
    Útil para cuando queremos mantener el documento completo como un solo chunk.
    """
    
    def __init__(self):
        self.name = "dummy_splitter"
    
    def split(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Retorna el texto completo como un único chunk."""
        if not text or not text.strip():
            return []
        
        return [TextChunk(
            text=text.strip(),
            metadata=metadata,
            chunk_index=0,
            total_chunks=1
        )]


class CharacterSplitter(BaseSplitter):
    """
    Splitter por cantidad de caracteres con overlap.
    Preparado para uso futuro.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.name = "character_splitter"
    
    def split(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Divide el texto en chunks de tamaño fijo con overlap."""
        if not text or not text.strip():
            return []
        
        text = text.strip()
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            chunks.append(TextChunk(
                text=chunk_text,
                metadata=metadata.copy(),
                chunk_index=chunk_index,
                total_chunks=-1  # Se actualiza después
            ))
            
            start = end - self.chunk_overlap
            chunk_index += 1
        
        # Actualizar total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks


def get_splitter(splitter_type: str = "dummy", **kwargs) -> BaseSplitter:
    """Factory para obtener el splitter deseado."""
    splitters = {
        "dummy": DummySplitter,
        "character": CharacterSplitter,
    }
    
    if splitter_type not in splitters:
        raise ValueError(f"Splitter '{splitter_type}' no disponible. Opciones: {list(splitters.keys())}")
    
    return splitters[splitter_type](**kwargs)
