"""RRF（Reciprocal Rank Fusion）融合向量与 BM25 结果（PRD §14.3）。"""

from __future__ import annotations


def rrf_fuse(
    vector_hits: list[tuple[str, float]],
    bm25_hits: list[tuple[str, float]],
    k: int = 60,
    top_k: int = 8,
) -> list[tuple[str, float]]:
    """返回融合后按 RRF 分降序的 (chunk_id, rrf_score) 列表。"""
    scores: dict[str, float] = {}
    for rank, (cid, _) in enumerate(vector_hits, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    for rank, (cid, _) in enumerate(bm25_hits, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
    return [(cid, score) for cid, score in ranked]
