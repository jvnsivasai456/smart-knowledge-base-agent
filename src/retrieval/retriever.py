from typing import List
from .models import SearchResult, SearchResponse
from ..embedding.embedder import Embedder
from ..embedding.vector_store import VectorStore

class Retriever:
    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        self.embedder = embedder
        self.vector_store = vector_store
        
    def search(self, query: str, top_k: int = 5) -> SearchResponse:
        """Search the vector store for chunks most similar to the query."""
        # 1. Embed query
        query_embedding = self.embedder.embed_text(query)
        
        # 2. Search ChromaDB
        # ChromaDB by default uses L2 distance for similarity.
        results = self.vector_store.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        search_results = []
        if results['ids'] and len(results['ids']) > 0:
            ids = results['ids'][0]
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            
            for i in range(len(ids)):
                meta = metadatas[i]
                # Safely parse nested custom_metadata if it was stringified by ChromaDB,
                # though here we assume a simple structure.
                search_results.append(SearchResult(
                    chunk_id=ids[i],
                    content=documents[i],
                    source_id=str(meta.get("source_id", "unknown")),
                    score=float(distances[i]),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    custom_metadata={}
                ))
                
        return SearchResponse(query=query, results=search_results)
