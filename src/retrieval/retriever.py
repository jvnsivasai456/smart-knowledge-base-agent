import math
import re
from typing import List, Dict, Any, Optional
from .models import SearchResult, SearchResponse
from ..embedding.embedder import Embedder
from ..embedding.vector_store import VectorStore

class PureBM25:
    """Pure-Python implementation of Okapi BM25 relevance framework (Robertson et al., 2009)."""
    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lens = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_lens) / max(1, self.corpus_size)
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        
        for doc in corpus:
            seen = set()
            for word in doc:
                if word not in seen:
                    self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1
                    seen.add(word)
                    
        for word, freq in self.doc_freqs.items():
            self.idf[word] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query_tokens: List[str], doc_tokens: List[str], doc_len: int) -> float:
        score = 0.0
        doc_freq = {}
        for token in doc_tokens:
            doc_freq[token] = doc_freq.get(token, 0) + 1
            
        for q in query_tokens:
            if q in doc_freq and q in self.idf:
                freq = doc_freq[q]
                denom = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avgdl)))
                score += self.idf[q] * ((freq * (self.k1 + 1.0)) / max(1e-5, denom))
        return score

class HybridRetriever:
    """
    Hybrid Dual-Index Retriever combining:
    1. Dense semantic vector embeddings in ChromaDB (SentenceTransformers)
    2. Sparse lexical Okapi BM25 scoring
    Fused via Reciprocal Rank Fusion (RRF, k=60) with 0.62 confidence threshold gating.
    """
    def __init__(self, embedder: Embedder, vector_store: VectorStore, rrf_k: int = 60, threshold: float = 0.62):
        self.embedder = embedder
        self.vector_store = vector_store
        self.rrf_k = rrf_k
        self.score_threshold = threshold

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r'\b[a-zA-Z0-9_\-\.]+\b', text) if len(w) > 1]

    def _bm25_search(self, query: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Perform sparse lexical search across indexed chunks using Okapi BM25."""
        try:
            coll_data = self.vector_store.collection.get()
            docs = coll_data.get("documents", [])
            ids = coll_data.get("ids", [])
            metas = coll_data.get("metadatas", [])
            if not docs:
                return []
        except Exception:
            return []

        tokenized_corpus = [self._tokenize(doc) for doc in docs]
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Try rank_bm25 if installed, otherwise use pure Python BM25
        try:
            from rank_bm25 import BM25Plus
            bm25 = BM25Plus(tokenized_corpus, k1=1.5, b=0.75)
            scores = bm25.get_scores(query_tokens)
        except Exception:
            bm25 = PureBM25(tokenized_corpus, k1=1.5, b=0.75)
            scores = [bm25.get_scores(query_tokens, doc_tok, len(doc_tok)) for doc_tok in tokenized_corpus]

        scored_candidates = []
        for i, score in enumerate(scores):
            if score > 0.05:
                meta = metas[i] if i < len(metas) and metas[i] else {}
                scored_candidates.append({
                    "id": ids[i],
                    "content": docs[i],
                    "source_id": str(meta.get("source_id", "unknown")),
                    "chunk_index": int(meta.get("chunk_index", 0)),
                    "score": float(score)
                })

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_n]

    def search(self, query: str, top_k: int = 5) -> SearchResponse:
        """
        Execute Hybrid Dual-Index Search combining Dense Vector Search and Sparse BM25
        unified via Reciprocal Rank Fusion (RRF, k=60).
        """
        # 1. Dense Semantic Vector Search
        query_embedding = self.embedder.embed_text(query)
        dense_results = self.vector_store.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2
        )

        dense_hits = []
        if dense_results.get('ids') and len(dense_results['ids']) > 0:
            ids = dense_results['ids'][0]
            documents = dense_results['documents'][0]
            metadatas = dense_results['metadatas'][0]
            distances = dense_results['distances'][0]
            for i in range(len(ids)):
                meta = metadatas[i] or {}
                # In ChromaDB with Euclidean distance, similarity is roughly max(0, 1 - dist/2)
                sim = max(0.0, min(1.0, 1.0 - (float(distances[i]) / 2.0)))
                dense_hits.append({
                    "id": ids[i],
                    "content": documents[i],
                    "source_id": str(meta.get("source_id", "unknown")),
                    "chunk_index": int(meta.get("chunk_index", 0)),
                    "distance": float(distances[i]),
                    "similarity": sim
                })

        # 2. Sparse Lexical Search (Okapi BM25)
        bm25_hits = self._bm25_search(query, top_n=top_k * 2)

        # 3. Reciprocal Rank Fusion (RRF with k=60)
        fused_scores: Dict[str, float] = {}
        hit_records: Dict[str, Dict[str, Any]] = {}

        for rank, hit in enumerate(dense_hits, start=1):
            hid = hit["id"]
            hit_records[hid] = hit
            fused_scores[hid] = fused_scores.get(hid, 0.0) + (1.0 / (self.rrf_k + rank))

        for rank, hit in enumerate(bm25_hits, start=1):
            hid = hit["id"]
            if hid not in hit_records:
                hit_records[hid] = hit
            fused_scores[hid] = fused_scores.get(hid, 0.0) + (1.0 / (self.rrf_k + rank))

        # 4. Check confidence against empirical threshold (0.62)
        max_similarity = max([h.get("similarity", 0.0) for h in dense_hits], default=0.0)
        is_confident = (max_similarity >= self.score_threshold)

        # 5. Rank candidates by fused RRF score
        ranked_ids = sorted(fused_scores.keys(), key=lambda hid: fused_scores[hid], reverse=True)[:top_k]

        final_results = []
        for hid in ranked_ids:
            item = hit_records[hid]
            dist = item.get("distance", 1.0)
            final_results.append(SearchResult(
                chunk_id=item["id"],
                content=item["content"],
                source_id=item.get("source_id", "unknown"),
                score=dist,
                chunk_index=item.get("chunk_index", 0),
                custom_metadata={"rrf_score": fused_scores[hid], "confident": is_confident}
            ))

        return SearchResponse(query=query, results=final_results)

# Backwards compatible alias
Retriever = HybridRetriever
