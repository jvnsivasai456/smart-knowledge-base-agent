import os
from src.config import settings
from src.embedding import Embedder, VectorStore, MetadataStore, Indexer
from src.processing import TextChunker
from src.ingestion import Ingestor

def test_embedding():
    # Setup test file
    test_file = "test_embed.txt"
    with open(test_file, "w") as f:
        f.write("Machine learning is a field of study that gives computers the ability to learn without being explicitly programmed.")

    # Initialize components
    settings.create_directories()
    ingestor = Ingestor()
    chunker = TextChunker(chunk_size=10, chunk_overlap=2)
    
    # Initialize embedding components (will download model if first time)
    print("Loading embedding model (this may take a moment)...")
    embedder = Embedder(model_name=settings.embedding_model_name)
    vector_store = VectorStore(persist_directory=settings.chroma_db_dir)
    metadata_store = MetadataStore(db_path=settings.metadata_db_path)
    indexer = Indexer(embedder, vector_store, metadata_store)

    # Process pipeline
    print("Ingesting and chunking...")
    doc = ingestor.ingest_file(test_file)
    chunks = chunker.chunk_document(doc)
    
    print(f"Indexing {len(chunks)} chunks...")
    indexer.index_document_chunks(chunks, doc.metadata.source_type)
    
    # Verify metadata store
    records = metadata_store.get_all_files()
    print(f"\nIndexed files in SQLite: {len(records)}")
    for r in records:
        print(f"- {r['source_id']} (Type: {r['source_type']})")
        
    # Cleanup
    os.remove(test_file)
    # We leave the DBs intact for future tests

if __name__ == "__main__":
    print("This script requires sentence-transformers and chromadb to run.")
    # test_embedding()  # Uncomment when dependencies are installed
