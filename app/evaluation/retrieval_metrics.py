"""检索指标：Hit@K、Recall@K、MRR。

relevance 判定：检索结果条目用 `project:source_path` 表示，与评测集的
expected_sources（同格式）做集合匹配（文件级 golden，PRD §21.1）。
"""

from __future__ import annotations

from collections.abc import Sequence


def _top(ranked: Sequence[str], k: int) -> list[str]:
    return list(ranked[:k])


def hit_at_k(ranked: Sequence[str], expected: set[str], k: int) -> int:
    """Top-K 中是否至少命中一个 golden source（0/1）。"""
    return 1 if any(s in expected for s in _top(ranked, k)) else 0


def recall_at_k(ranked: Sequence[str], expected: set[str], k: int) -> float:
    """Top-K 命中的 golden source 占全部 golden 的比例。"""
    if not expected:
        return 0.0
    return len(set(_top(ranked, k)) & expected) / len(expected)


def reciprocal_rank(ranked: Sequence[str], expected: set[str], k: int) -> float:
    """第一个命中 golden 的排名的倒数（1-indexed），未命中为 0。"""
    for i, s in enumerate(_top(ranked, k)):
        if s in expected:
            return 1.0 / (i + 1)
    return 0.0


def mrr(ranked_list: Sequence[Sequence[str]], expected_list: Sequence[set[str]], k: int) -> float:
    """Mean Reciprocal Rank。"""
    if not ranked_list:
        return 0.0
    total = sum(reciprocal_rank(r, e, k) for r, e in zip(ranked_list, expected_list))
    return total / len(ranked_list)


def evaluate(
    ranked_list: Sequence[Sequence[str]],
    expected_list: Sequence[set[str]],
    k_values: Sequence[int],
) -> dict[str, float]:
    """聚合多个查询的指标，返回 {metric@k: 值}。"""
    n = len(ranked_list) or 1
    out: dict[str, float] = {}
    for k in k_values:
        out[f"hit@{k}"] = sum(hit_at_k(r, e, k) for r, e in zip(ranked_list, expected_list)) / n
        out[f"recall@{k}"] = sum(recall_at_k(r, e, k) for r, e in zip(ranked_list, expected_list)) / n
        out[f"mrr@{k}"] = mrr(ranked_list, expected_list, k)
    return out
