import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager

from ..config import settings
from ..embedding import Embedder, VectorStore, MetadataStore, Indexer
from ..ingestion import Ingestor
from ..processing import TextChunker
from ..retrieval import Retriever
from ..retrieval.models import QueryRequest
from ..update_engine import DirectoryScanner, KnowledgeBaseUpdater, UpdateScheduler

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
    
    scanner = DirectoryScanner(settings.upload_dir)
    updater = KnowledgeBaseUpdater(scanner, metadata_store, indexer, ingestor, chunker)
    
    scheduler = UpdateScheduler(updater, interval_minutes=settings.scheduler_interval_minutes)
    
    components['updater'] = updater
    components['retriever'] = retriever
    components['scheduler'] = scheduler
    
    # Start the continuous update scheduler
    scheduler.start()
    
    yield
    
    # Clean up on shutdown
    scheduler.stop()

app = FastAPI(title="Smart Knowledge Base API", lifespan=lifespan)

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

@app.post("/search")
def search(request: QueryRequest):
    """Search the knowledge base."""
    retriever = components.get('retriever')
    if not retriever:
        raise HTTPException(status_code=500, detail="Retriever not initialized")
        
    return retriever.search(request.query, top_k=request.top_k)
