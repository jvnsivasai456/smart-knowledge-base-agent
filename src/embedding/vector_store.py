import chromadb
from typing import List
from ..processing.models import DocumentChunk

class VectorStore:
    def __init__(self, persist_directory: str, collection_name: str = "knowledge_base"):
        """Initialize ChromaDB persistent client."""
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
    def upsert_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        """Upsert document chunks and their embeddings into ChromaDB."""
        if not chunks:
            return
            
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        # Flatten metadata to primitive types required by ChromaDB
        clean_metadatas = []
        for chunk in chunks:
            clean_metadatas.append({
                "source_id": str(chunk.metadata.source_id),
                "chunk_index": int(chunk.metadata.chunk_index),
                "file_hash": str(chunk.metadata.file_hash)
            })
        
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=clean_metadatas
        )
        
    def delete_by_source_id(self, source_id: str):
        """Delete all chunks belonging to a specific source document."""
        self.collection.delete(where={"source_id": source_id})
