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


class LegalSplitter(BaseSplitter):
    """
    Splitter optimizado para textos legales largos.
    Usa chunks grandes (~6000 tokens ≈ 24000 chars) para respetar límite de 8192 tokens.
    Intenta cortar en límites naturales: artículos, párrafos, oraciones.
    """
    
    def __init__(self, chunk_size: int = 24000, chunk_overlap: int = 500):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.name = "legal_splitter"
        # Separadores en orden de preferencia
        self.separators = [
            "\nARTÍCULO ",
            "\nArtículo ",
            "\nArt. ",
            "\nART. ",
            "\nCAPITULO ",
            "\nCapítulo ",
            "\nTITULO ",
            "\nTítulo ",
            "\n\n",
            "\n",
            ". ",
            " ",
        ]
    
    def _find_best_split_point(self, text: str, target: int) -> int:
        """Encuentra el mejor punto de corte cerca del target."""
        # Buscar separadores cerca del target (±20%)
        search_start = int(target * 0.8)
        search_end = min(len(text), int(target * 1.1))
        search_zone = text[search_start:search_end]
        
        for separator in self.separators:
            # Buscar última ocurrencia del separador en la zona
            pos = search_zone.rfind(separator)
            if pos != -1:
                return search_start + pos + len(separator)
        
        # Si no encuentra separador, cortar en target
        return min(target, len(text))
    
    def split(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Divide el texto en chunks respetando estructura legal."""
        if not text or not text.strip():
            return []
        
        text = text.strip()
        
        # Si el texto es menor al chunk_size, retornar como único chunk
        if len(text) <= self.chunk_size:
            return [TextChunk(
                text=text,
                metadata=metadata,
                chunk_index=0,
                total_chunks=1
            )]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calcular fin tentativo
            end = start + self.chunk_size
            
            if end >= len(text):
                # Último chunk
                chunk_text = text[start:]
            else:
                # Buscar mejor punto de corte
                end = self._find_best_split_point(text[start:], self.chunk_size)
                chunk_text = text[start:start + end]
            
            chunks.append(TextChunk(
                text=chunk_text.strip(),
                metadata=metadata.copy(),
                chunk_index=chunk_index,
                total_chunks=-1
            ))
            
            # Mover inicio con overlap
            start = start + len(chunk_text) - self.chunk_overlap
            if start < 0:
                start = 0
            chunk_index += 1
            
            # Seguridad: evitar loop infinito
            if chunk_index > 1000:
                break
        
        # Actualizar total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks


def get_splitter(splitter_type: str = "dummy", **kwargs) -> BaseSplitter:
    """Factory para obtener el splitter deseado."""
    splitters = {
        "dummy": DummySplitter,
        "character": CharacterSplitter,
        "legal": LegalSplitter,
    }
    
    if splitter_type not in splitters:
        raise ValueError(f"Splitter '{splitter_type}' no disponible. Opciones: {list(splitters.keys())}")
    
    return splitters[splitter_type](**kwargs)