from pydantic import BaseModel
from typing import Dict, Any

class ChunkMetadata(BaseModel):
    source_id: str
    chunk_index: int
    file_hash: str
    custom_metadata: Dict[str, Any] = {}

class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: ChunkMetadata
