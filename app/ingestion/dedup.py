"""完全重复去重：按 content_hash 只保留一份，记录来源映射。"""

from __future__ import annotations

from collections.abc import Iterable

from app.core.schemas import Document


def deduplicate(documents: Iterable[Document]) -> tuple[list[Document], list[dict]]:
    """返回 (去重后文档列表, 重复映射报告)。首现者胜出，保持确定性。"""
    seen: dict[str, Document] = {}
    removed: list[dict] = []
    for doc in documents:
        h = doc.metadata.content_hash
        if h is None:
            continue
        if h in seen:
            removed.append(
                {
                    "content_hash": h,
                    "kept_parent_id": seen[h].parent_id,
                    "kept_source_path": seen[h].metadata.source_path,
                    "removed_parent_id": doc.parent_id,
                    "removed_source_path": doc.metadata.source_path,
                }
            )
        else:
            seen[h] = doc
    kept = sorted(seen.values(), key=lambda d: d.parent_id)
    return kept, removed
