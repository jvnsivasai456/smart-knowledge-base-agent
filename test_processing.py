from src.ingestion import Ingestor
from src.processing import TextChunker

def test_processing():
    # 1. Mock a document ingestion
    test_file = "test_process.txt"
    with open(test_file, "w") as f:
        # Create a document with ~20 words, extra spaces and newlines
        f.write("This   is a    test document.\n\n\nIt has multiple sentences. " * 5)
        
    ingestor = Ingestor()
    doc = ingestor.ingest_file(test_file)
    
    # 2. Process and chunk
    # We use a small chunk size to see the overlap in action
    chunker = TextChunker(chunk_size=10, chunk_overlap=3)
    chunks = chunker.chunk_document(doc)
    
    print(f"Original content length (chars): {len(doc.content)}")
    print(f"Number of chunks generated: {len(chunks)}\n")
    
    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i} ---")
        print(f"ID: {chunk.chunk_id}")
        print(f"Content: {chunk.content}")
        print(f"Metadata Hash: {chunk.metadata.file_hash}")
        print()

    import os
    os.remove(test_file)

if __name__ == "__main__":
    test_processing()
