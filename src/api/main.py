import os
import shutil
import urllib.parse
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager

from ..config import settings
from ..embedding import Embedder, VectorStore, MetadataStore, Indexer
from ..ingestion import Ingestor
from ..processing import TextChunker
from ..retrieval import Retriever, AnswerEngine
from ..retrieval.models import QueryRequest
from ..update_engine import DirectoryScanner, KnowledgeBaseUpdater, UpdateScheduler

class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4
    api_key: Optional[str] = None
    provider: Optional[str] = "local"

# Global components registry
components = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure directories exist
    settings.create_directories()
    
    # Initialize components
    embedder = Embedder(model_name=settings.embedding_model_name)
    vector_store = VectorStore(persist_directory=settings.chroma_db_dir)
    metadata_store = MetadataStore(db_path=settings.metadata_db_path)
    
    indexer = Indexer(embedder, vector_store, metadata_store)
    ingestor = Ingestor()
    chunker = TextChunker()
    
    retriever = Retriever(embedder, vector_store)
    answer_engine = AnswerEngine(embedder=embedder)
    
    scanner = DirectoryScanner(settings.upload_dir)
    updater = KnowledgeBaseUpdater(scanner, metadata_store, indexer, ingestor, chunker)
    
    scheduler = UpdateScheduler(updater, interval_minutes=settings.scheduler_interval_minutes)
    
    components['updater'] = updater
    components['retriever'] = retriever
    components['answer_engine'] = answer_engine
    components['scheduler'] = scheduler
    
    # Start the continuous update scheduler
    scheduler.start()
    
    yield
    
    # Clean up on shutdown
    scheduler.stop()

app = FastAPI(title="Smart Knowledge Base Agent API", lifespan=lifespan)

@app.get("/health")
def health_check():
    """Health check endpoint for deployment platforms."""
    return {"status": "ok"}

@app.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a document to the watched directory and trigger an index update."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    file_path = os.path.join(settings.upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Trigger an update cycle in the background
    updater = components.get('updater')
    if updater:
        background_tasks.add_task(updater.run_update)
    
    return {"filename": file.filename, "message": "File uploaded and indexing started."}

@app.post("/resync")
async def resync_knowledge_base(background_tasks: BackgroundTasks):
    """Trigger an immediate manual resynchronization of all files."""
    updater = components.get('updater')
    if updater:
        background_tasks.add_task(updater.run_update)
        return {"status": "started", "message": "Knowledge base resync initiated."}
    raise HTTPException(status_code=500, detail="Updater not available")

@app.post("/search")
def search(request: QueryRequest):
    """Raw vector semantic search."""
    retriever = components.get('retriever')
    if not retriever:
        raise HTTPException(status_code=500, detail="Retriever not initialized")
        
    return retriever.search(request.query, top_k=request.top_k)

@app.post("/chat")
def chat(request: ChatRequest):
    """Intelligent conversational & QA synthesis endpoint."""
    retriever = components.get('retriever')
    answer_engine = components.get('answer_engine')
    updater = components.get('updater')
    if not retriever or not answer_engine:
        raise HTTPException(status_code=500, detail="Retrieval components not initialized")
        
    docs = []
    if updater and updater.metadata_store:
        docs = updater.metadata_store.get_all_files()

    top_k = request.top_k if request.top_k else 4
    
    # 1. Check for quick conversational greetings first
    if answer_engine.is_greeting_or_chitchat(request.query):
        return answer_engine.handle_greeting(request.query, docs)

    # 2. Retrieve semantic context from vector store
    search_resp = retriever.search(request.query, top_k=top_k)
    
    # 3. Synthesize natural language answer
    return answer_engine.synthesize(
        request.query, 
        search_resp.results, 
        docs,
        api_key=request.api_key,
        provider=request.provider
    )

@app.get("/documents")
def list_documents():
    """List all indexed documents with enriched metadata (sizes, status)."""
    updater = components.get('updater')
    if not updater or not updater.metadata_store:
        return {"documents": []}
    records = updater.metadata_store.get_all_files()
    
    # Enrich with file size information if exists on disk
    enriched = []
    for r in records:
        rec = dict(r)
        src_id = rec.get("source_id", "")
        rec["filename"] = os.path.basename(src_id)
        disk_path = src_id if os.path.isabs(src_id) else os.path.join(settings.upload_dir, rec["filename"])
        if os.path.exists(disk_path):
            rec["file_size_bytes"] = os.path.getsize(disk_path)
            rec["exists_on_disk"] = True
        else:
            rec["file_size_bytes"] = 0
            rec["exists_on_disk"] = False
        enriched.append(rec)
        
    return {"documents": enriched}

@app.delete("/documents/{filename:path}")
def delete_document(filename: str):
    """Delete a document from vector store, SQLite metadata, and uploads directory."""
    clean_filename = urllib.parse.unquote(filename).strip()
    updater = components.get('updater')
    if not updater:
        raise HTTPException(status_code=500, detail="System updater not initialized")
        
    records = updater.metadata_store.get_all_files()
    matched_source_id = None
    for r in records:
        r_src = r.get("source_id", "")
        if os.path.basename(r_src) == clean_filename or r_src == clean_filename:
            matched_source_id = r_src
            break
            
    source_to_delete = matched_source_id if matched_source_id else os.path.join(settings.upload_dir, clean_filename)
    
    # 1. Delete vectors from ChromaDB
    try:
        updater.indexer.vector_store.delete_by_source_id(source_to_delete)
    except Exception as e:
        print(f"Error deleting vectors for {source_to_delete}: {e}")
        
    # 2. Delete record from SQLite
    try:
        updater.metadata_store.delete_file_record(source_to_delete)
    except Exception as e:
        print(f"Error deleting metadata for {source_to_delete}: {e}")
        
    # 3. Delete physical file from uploads folder
    paths_to_try = [
        source_to_delete,
        os.path.join(settings.upload_dir, clean_filename),
        os.path.join(settings.upload_dir, os.path.basename(clean_filename))
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception as e:
                print(f"Error removing file {p}: {e}")
            
    return {"message": f"Successfully deleted '{clean_filename}' from knowledge base."}
