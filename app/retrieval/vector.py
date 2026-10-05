"""向量检索。"""

from __future__ import annotations

from app.indexing.embeddings import Embedder
from app.indexing.vector_store import VectorStore


class VectorRetriever:
    def __init__(self, store: VectorStore, embedder: Embedder, top_n: int = 50):
        self.store = store
        self.embedder = embedder
        self.top_n = top_n

    def retrieve(self, query: str) -> list[tuple[str, float]]:
        vec = self.embedder.embed_query(query)
        return self.store.search(vec, self.top_n)
