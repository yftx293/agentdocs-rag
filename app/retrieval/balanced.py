"""平衡检索：compare 查询时对每个项目分别检索并 round-robin 合并（PRD §18）。

解决「Top-K 全部来自单个项目」的偏斜问题：先把 RRF 候选池放大，
按项目分组各取 Top-N，再 round-robin 交错，保证每个项目都有代表。
"""

from __future__ import annotations

from app.core.schemas import Chunk
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.fusion import rrf_fuse
from app.retrieval.vector import VectorRetriever


def retrieve_balanced(
    query: str,
    projects: list[str],
    vector_retriever: VectorRetriever,
    bm25_retriever: BM25Retriever,
    chunk_map: dict[str, Chunk],
    rrf_k: int = 60,
    candidate_top_k: int = 50,
    per_project_n: int = 8,
) -> list[str]:
    """返回按项目平衡后的 chunk_id 列表。"""
    if len(projects) <= 1:
        vh = vector_retriever.retrieve(query)
        bh = bm25_retriever.retrieve(query)
        return [cid for cid, _ in rrf_fuse(vh, bh, k=rrf_k, top_k=8)]

    vh = vector_retriever.retrieve(query)
    bh = bm25_retriever.retrieve(query)
    fused = rrf_fuse(vh, bh, k=rrf_k, top_k=candidate_top_k)

    buckets: dict[str, list[str]] = {p: [] for p in projects}
    for cid, _ in fused:
        c = chunk_map.get(cid)
        if c and c.metadata.project in buckets:
            buckets[c.metadata.project].append(cid)

    # 每项目上限，防止单项目霸屏
    for p in projects:
        buckets[p] = buckets[p][:per_project_n]

    merged: list[str] = []
    while any(buckets.values()):
        for p in projects:
            if buckets[p]:
                merged.append(buckets[p].pop(0))
    return merged
