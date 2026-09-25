import logging
from typing import List
from .scanner import DirectoryScanner
from ..embedding.metadata_store import MetadataStore
from ..embedding.indexer import Indexer
from ..ingestion.ingestor import Ingestor
from ..processing.chunker import TextChunker

logger = logging.getLogger(__name__)

class KnowledgeBaseUpdater:
    def __init__(
        self, 
        scanner: DirectoryScanner, 
        metadata_store: MetadataStore,
        indexer: Indexer,
        ingestor: Ingestor,
        chunker: TextChunker
    ):
        self.scanner = scanner
        self.metadata_store = metadata_store
        self.indexer = indexer
        self.ingestor = ingestor
        self.chunker = chunker

    def run_update(self):
        """Synchronizes the vector store with the current file system state."""
        logger.info("Starting Knowledge Base update cycle...")
        
        # 1. Get current file system state
        current_files = self.scanner.scan()
        
        # 2. Get previous state from DB (exclude html URLs)
        db_records = {
            r['source_id']: r['file_hash'] 
            for r in self.metadata_store.get_all_files() 
            if r['source_type'] != 'html'
        }
        
        # 3. Determine New, Modified, and Deleted files
        new_files = []
        modified_files = []
        deleted_files = []
        
        for file_path, file_hash in current_files.items():
            if file_path not in db_records:
                new_files.append(file_path)
            elif db_records[file_path] != file_hash:
                modified_files.append(file_path)
                
        for db_file in db_records:
            if db_file not in current_files:
                deleted_files.append(db_file)
                
        # 4. Process deletions
        for file_path in deleted_files:
            logger.info(f"Removing deleted file: {file_path}")
            self.indexer.remove_document(file_path)
            
        # 5. Process new and modified files
        files_to_index = new_files + modified_files
        for file_path in files_to_index:
            action = "new" if file_path in new_files else "modified"
            logger.info(f"Indexing {action} file: {file_path}")
            try:
                # If modified, remove old chunks first
                if action == "modified":
                    self.indexer.remove_document(file_path)
                    
                doc = self.ingestor.ingest_file(file_path)
                chunks = self.chunker.chunk_document(doc)
                self.indexer.index_document_chunks(chunks, doc.metadata.source_type)
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                
        logger.info(
            f"Update cycle complete. "
            f"Added: {len(new_files)}, "
            f"Modified: {len(modified_files)}, "
            f"Deleted: {len(deleted_files)}"
        )
