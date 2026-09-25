import os
from src.ingestion import Ingestor

def test_ingestion():
    ingestor = Ingestor()
    
    # 1. Test TXT Ingestion
    test_file = "test.txt"
    with open(test_file, "w") as f:
        f.write("Hello, world! This is a test document.")
        
    print("Testing TXT ingestion...")
    doc = ingestor.ingest_file(test_file)
    print(f"Content: {doc.content}")
    print(f"Metadata Hash: {doc.metadata.file_hash}")
    print(f"Source Type: {doc.metadata.source_type}\n")
    
    # 2. Test HTML Ingestion
    print("Testing HTML ingestion (example.com)...")
    url_doc = ingestor.ingest_url("http://example.com")
    print(f"Content preview: {url_doc.content[:100]}...")
    print(f"Metadata Hash: {url_doc.metadata.file_hash}")
    print(f"Source Type: {url_doc.metadata.source_type}\n")

    os.remove(test_file)

if __name__ == "__main__":
    test_ingestion()
