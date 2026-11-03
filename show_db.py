import os
import sqlite3
import chromadb

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
METADATA_DB = os.path.join(DATA_DIR, "metadata.sqlite")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")

def print_separator(char="=", length=68):
    print(char * length)

def show_database():
    print_separator("=")
    print("        SMART KNOWLEDGE BASE - DATABASE AUDIT & INSPECTOR")
    print_separator("=")

    # 1. SQLite Relational Metadata Store
    print("\n[1] RELATIONAL METADATA STORE (SQLite)")
    print(f"    File: {os.path.relpath(METADATA_DB, PROJECT_DIR)}")
    
    if os.path.exists(METADATA_DB):
        conn = sqlite3.connect(METADATA_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT source_id, source_type, file_hash, upload_time, last_indexed FROM files")
        rows = cursor.fetchall()
        print(f"    Total Tracked Files: {len(rows)}")
        print("    " + "-" * 64)
        for i, row in enumerate(rows, 1):
            fname = os.path.basename(row[0])
            ftype = row[1].upper()
            fhash = row[2][:12] + "..."
            ftime = row[4][:19].replace("T", " ") if row[4] else "N/A"
            print(f"    {i}. {fname:<36} | {ftype:<4} | Hash: {fhash} | {ftime}")
        conn.close()
    else:
        print("    [!] metadata.sqlite not found.")

    # 2. ChromaDB Dense Vector Store
    print("\n[2] DENSE VECTOR STORE (ChromaDB)")
    print(f"    Directory: {os.path.relpath(CHROMA_DIR, PROJECT_DIR)}")
    
    if os.path.exists(CHROMA_DIR):
        try:
            client = chromadb.PersistentClient(path=CHROMA_DIR)
            collections = client.list_collections()
            print(f"    Active Collections: {[c.name for c in collections]}")
            
            for col in collections:
                count = col.count()
                print(f"    - Collection '{col.name}': {count} Dense Vector Embeddings (384-dim)")
                
                if count > 0:
                    sample = col.peek(limit=2)
                    print("      Sample Chunk Embeddings:")
                    for idx, (cid, meta) in enumerate(zip(sample["ids"], sample["metadatas"]), 1):
                        source_name = os.path.basename(meta.get("source_id", "Unknown"))
                        chunk_idx = meta.get("chunk_index", 0)
                        print(f"        Chunk {idx}: ID={cid[:24]}... | File: {source_name} (Chunk #{chunk_idx})")
        except Exception as e:
            print(f"    [!] Error inspecting ChromaDB: {e}")
    else:
        print("    [!] chroma_db directory not found.")

    print_separator("=")

if __name__ == "__main__":
    show_database()
