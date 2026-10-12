import re
from typing import List
from .models import DocumentChunk, ChunkMetadata
from ..ingestion.document import RawDocument
from .cleaner import clean_text

class TextChunker:
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 40):
        """
        Initialize the chunker.
        chunk_size: approximate number of words per chunk
        chunk_overlap: approximate number of words to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: RawDocument) -> List[DocumentChunk]:
        """
        Split a raw document into chunks while preserving paragraph breaks,
        headers, equations, and numbered items.
        """
        cleaned_text = clean_text(document.content)
        if not cleaned_text.strip():
            return []

        # Split text into paragraphs / structural blocks
        raw_paras = cleaned_text.split('\n')
        paras = [p.strip() for p in raw_paras if p.strip()]

        if not paras:
            return []

        chunks = []
        current_chunk_paras = []
        current_word_count = 0
        chunk_index = 0

        for para in paras:
            para_words = len(para.split())
            if current_word_count + para_words > self.chunk_size and current_chunk_paras:
                # Flush current chunk
                chunk_text = "\n\n".join(current_chunk_paras)
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

                # Overlap: keep the last 1-2 paragraphs if within overlap word budget
                overlap_paras = []
                overlap_words = 0
                for p in reversed(current_chunk_paras):
                    pw = len(p.split())
                    if overlap_words + pw <= self.chunk_overlap:
                        overlap_paras.insert(0, p)
                        overlap_words += pw
                    else:
                        break
                
                current_chunk_paras = overlap_paras + [para]
                current_word_count = overlap_words + para_words
            else:
                current_chunk_paras.append(para)
                current_word_count += para_words

        # Flush any remaining paragraphs
        if current_chunk_paras:
            chunk_text = "\n\n".join(current_chunk_paras)
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

        return chunks
