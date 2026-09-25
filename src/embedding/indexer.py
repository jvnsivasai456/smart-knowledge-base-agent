from typing import List
from ..processing.models import DocumentChunk
from .embedder import Embedder
from .vector_store import VectorStore
from .metadata_store import MetadataStore

class Indexer:
    def __init__(self, embedder: Embedder, vector_store: VectorStore, metadata_store: MetadataStore):
        """Orchestrates embedding generation, vector storage, and SQLite metadata."""
        self.embedder = embedder
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        
    def index_document_chunks(self, chunks: List[DocumentChunk], source_type: str):
        """Embed chunks and save them to the vector and metadata stores."""
        if not chunks:
            return
            
        # We assume all chunks in the list belong to the same source document
        source_id = chunks[0].metadata.source_id
        file_hash = chunks[0].metadata.file_hash
        
        # 1. Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedder.embed_batch(texts)
        
        # 2. Upsert vectors to ChromaDB
        self.vector_store.upsert_chunks(chunks, embeddings)
        
        # 3. Update the SQLite tracking database
        self.metadata_store.upsert_file_record(source_id, source_type, file_hash)
        
    def remove_document(self, source_id: str):
        """Remove a document entirely from both stores."""
        self.vector_store.delete_by_source_id(source_id)
        self.metadata_store.delete_file_record(source_id)
