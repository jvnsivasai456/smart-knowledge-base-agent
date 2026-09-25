import os
import logging
import time
from src.config import settings
from src.update_engine import DirectoryScanner, KnowledgeBaseUpdater
from src.embedding import Embedder, VectorStore, MetadataStore, Indexer
from src.ingestion import Ingestor
from src.processing import TextChunker

logging.basicConfig(level=logging.INFO)

def test_update_engine():
    # 1. Ensure upload dir exists
    settings.create_directories()
    
    # 2. Create a test file
    test_file_path = os.path.join(settings.upload_dir, "doc1.txt")
    with open(test_file_path, "w") as f:
        f.write("Version 1 of the document.")
        
    # 3. Setup dependencies
    scanner = DirectoryScanner(settings.upload_dir)
    metadata_store = MetadataStore(db_path=settings.metadata_db_path)
    
    # Normally we need all embedding components, but for this test we can
    # just see if it detects new/modified/deleted properly.
    # To run this fully, uncomment the real dependencies:
    
    # embedder = Embedder(model_name=settings.embedding_model_name)
    # vector_store = VectorStore(persist_directory=settings.chroma_db_dir)
    # indexer = Indexer(embedder, vector_store, metadata_store)
    # ingestor = Ingestor()
    # chunker = TextChunker()
    # updater = KnowledgeBaseUpdater(scanner, metadata_store, indexer, ingestor, chunker)
    
    print("\n--- Test: Detect New Files ---")
    current_files = scanner.scan()
    print(f"Scanned files: {current_files}")
    
    db_records = {r['source_id']: r['file_hash'] for r in metadata_store.get_all_files()}
    print(f"DB records: {db_records}")
    
    print("\n--- Test: File Modification ---")
    with open(test_file_path, "w") as f:
        f.write("Version 2 of the document. Changed!")
    
    modified_scan = scanner.scan()
    print(f"Hash changed from {current_files[test_file_path]} to {modified_scan[test_file_path]}")
    
    print("\n--- Test: File Deletion ---")
    os.remove(test_file_path)
    deleted_scan = scanner.scan()
    print(f"Remaining files: {deleted_scan}")

if __name__ == "__main__":
    test_update_engine()
