from sentence_transformers import SentenceTransformer
from typing import List

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the sentence-transformers model."""
        self.model = SentenceTransformer(model_name)
        
    def embed_text(self, text: str) -> List[float]:
        """Embed a single string into a vector."""
        return self.model.encode(text).tolist()
        
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of strings into vectors."""
        return self.model.encode(texts).tolist()
