"""BM25 检索。"""

from __future__ import annotations

from app.indexing.bm25_index import BM25Index


class BM25Retriever:
    def __init__(self, index: BM25Index, top_n: int = 50):
        self.index = index
        self.top_n = top_n

    def retrieve(self, query: str) -> list[tuple[str, float]]:
        return self.index.search(query, self.top_n)
