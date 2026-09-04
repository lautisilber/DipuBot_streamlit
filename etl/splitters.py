"""
Splitters Module
----------------
Módulo para dividir textos en chunks para procesamiento de embeddings.
Incluye un dummy_splitter (1 doc = 1 chunk), un splitter por caracteres y un
LegalSplitter optimizado para textos legales (token-aware).
"""

from typing import List, Dict, Any
from dataclasses import dataclass

try:
    import tiktoken
    _ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - fallback si tiktoken no está disponible
    _ENCODING = None


def count_tokens(text: str) -> int:
    """Cuenta tokens con tiktoken; si no está disponible, estima ~4 chars/token."""
    if _ENCODING is not None:
        return len(_ENCODING.encode(text))
    return max(1, len(text) // 4)


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
    Splitter optimizado para textos legales, token-aware.

    Divide el texto en chunks de un tamaño objetivo medido en TOKENS (no en
    caracteres) para que el retrieval sea granular (un chunk ≈ un artículo o
    sección) y para no exceder nunca el límite de 8192 tokens del modelo de
    embeddings. Intenta cortar en límites naturales: artículos, capítulos,
    títulos, párrafos y oraciones, en ese orden de preferencia.

    Parámetros:
        chunk_size:    tamaño objetivo de cada chunk, EN TOKENS (default 1000).
        chunk_overlap: solapamiento entre chunks consecutivos, EN TOKENS
                       (default 100). Debe ser < chunk_size.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) debe ser menor que "
                f"chunk_size ({chunk_size})"
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.name = "legal_splitter"
        # Separadores en orden de preferencia (de mayor a menor jerarquía legal)
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

    def _find_split_char(self, text: str, target_char: int) -> int:
        """
        Devuelve el índice de carácter donde conviene cortar, buscando un
        separador natural en una ventana alrededor de `target_char`.

        El valor devuelto es un índice absoluto dentro de `text` (longitud del
        primer chunk). Si no hay separador en la ventana, corta en target_char.
        """
        search_start = max(1, int(target_char * 0.8))
        search_end = min(len(text), int(target_char * 1.2))
        if search_start >= search_end:
            return min(target_char, len(text))

        search_zone = text[search_start:search_end]
        for separator in self.separators:
            pos = search_zone.rfind(separator)
            if pos != -1:
                # Cortar justo después del separador para no partir la palabra clave
                return search_start + pos + len(separator)

        return min(target_char, len(text))

    def split(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Divide el texto en chunks respetando estructura legal (token-aware)."""
        if not text or not text.strip():
            return []

        text = text.strip()

        # Si el texto entero cabe en un chunk, devolverlo tal cual.
        if count_tokens(text) <= self.chunk_size:
            return [TextChunk(
                text=text,
                metadata=metadata,
                chunk_index=0,
                total_chunks=1,
            )]

        # Estimación chars/token de ESTE texto, para traducir el objetivo de
        # tokens a un objetivo de caracteres (más barato que tokenizar en cada
        # iteración). El punto de corte fino igual se valida contra separadores.
        chars_per_token = len(text) / max(1, count_tokens(text))
        target_char = max(1, int(self.chunk_size * chars_per_token))
        overlap_char = int(self.chunk_overlap * chars_per_token)

        chunks: List[TextChunk] = []
        start = 0
        chunk_index = 0

        while start < len(text):
            remaining = text[start:]

            # Último chunk: el resto entra en un solo chunk por tokens.
            if count_tokens(remaining) <= self.chunk_size:
                chunk_text = remaining
                chunks.append(TextChunk(
                    text=chunk_text.strip(),
                    metadata=metadata.copy(),
                    chunk_index=chunk_index,
                    total_chunks=-1,
                ))
                break  # <-- FIX CLAVE: consumimos el resto y salimos del loop.

            # Corte intermedio en un separador natural.
            cut = self._find_split_char(remaining, target_char)
            chunk_text = remaining[:cut]

            chunks.append(TextChunk(
                text=chunk_text.strip(),
                metadata=metadata.copy(),
                chunk_index=chunk_index,
                total_chunks=-1,
            ))

            # Avanzar el cursor aplicando overlap.
            next_start = start + len(chunk_text) - overlap_char

            # GARANTÍA ANTI-LOOP: el cursor SIEMPRE debe avanzar al menos 1 char.
            # Antes, si el overlap era >= al chunk producido, `start` no avanzaba
            # y se generaban miles de chunks idénticos hasta un tope de seguridad.
            if next_start <= start:
                next_start = start + max(1, len(chunk_text) - overlap_char, len(chunk_text) // 2)

            start = next_start
            chunk_index += 1

        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total

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