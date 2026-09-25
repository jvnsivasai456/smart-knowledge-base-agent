from typing import List
from .models import DocumentChunk, ChunkMetadata
from ..ingestion.document import RawDocument
from .cleaner import clean_text

class TextChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize the chunker.
        chunk_size: approximate number of words per chunk
        chunk_overlap: number of words to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: RawDocument) -> List[DocumentChunk]:
        """Split a raw document into overlapping chunks after cleaning."""
        cleaned_text = clean_text(document.content)
        words = cleaned_text.split()
        chunks = []
        
        if not words:
            return chunks

        i = 0
        chunk_index = 0
        while i < len(words):
            end = min(i + self.chunk_size, len(words))
            chunk_words = words[i:end]
            chunk_text = " ".join(chunk_words)
            
            chunk_id = f"{document.metadata.file_hash}_{chunk_index}"
            
            metadata = ChunkMetadata(
                source_id=document.metadata.source_id,
                chunk_index=chunk_index,
                file_hash=document.metadata.file_hash,
                custom_metadata=document.metadata.custom_metadata
            )
            
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                content=chunk_text,
                metadata=metadata
            ))
            
            chunk_index += 1
            i += (self.chunk_size - self.chunk_overlap)
            
        return chunks
