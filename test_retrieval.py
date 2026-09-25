import os
from src.config import settings
from src.embedding import Embedder, VectorStore
from src.retrieval import Retriever

def test_retrieval():
    # Note: This assumes test_embedding.py has already populated the vector store.
    print("Loading embedding model and vector store...")
    embedder = Embedder(model_name=settings.embedding_model_name)
    vector_store = VectorStore(persist_directory=settings.chroma_db_dir)
    retriever = Retriever(embedder, vector_store)
    
    query = "What is machine learning?"
    print(f"Querying for: '{query}'")
    
    response = retriever.search(query, top_k=2)
    
    print("\n--- Top Results ---")
    if not response.results:
        print("No results found. (Did you run the embedding test?)")
    
    for i, res in enumerate(response.results):
        print(f"Result {i+1} (Score/Distance: {res.score:.4f})")
        print(f"Source: {res.source_id}")
        print(f"Content: {res.content}\n")

if __name__ == "__main__":
    print("This script requires sentence-transformers and chromadb to run.")
    # test_retrieval()
