from pydantic import BaseModel
from typing import Dict, Any, List

class SearchResult(BaseModel):
    chunk_id: str
    content: str
    source_id: str
    score: float
    chunk_index: int
    custom_metadata: Dict[str, Any] = {}
    
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    
class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
