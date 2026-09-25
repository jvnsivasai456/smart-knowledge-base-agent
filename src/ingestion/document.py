from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime, timezone

class DocumentMetadata(BaseModel):
    source_id: str
    source_type: str
    file_hash: str
    upload_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

class RawDocument(BaseModel):
    content: str
    metadata: DocumentMetadata
