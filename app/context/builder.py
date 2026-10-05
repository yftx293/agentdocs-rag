"""Context Builder（PRD §18）。

把检索结果组装成给 LLM 的 final_context：
1. 去重（按 chunk_id）
2. 项目平衡（compare 查询多项目时 round-robin 交错，避免 Top-K 全来自单个项目）
3. 贪心打包（整 chunk 纳入，不截断 → 保护代码块/表格）
4. Citation 保留（每个 chunk 带来源头 + 结构化 citation）

注意：S6 冻结 heading-only 后 chunk=section=parent，「Parent Expansion / 同父合并」
天然退化（chunk 已是完整语义单元，无 child 可展开），故本模块只做组装与平衡。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.schemas import Chunk
from app.ingestion.splitter import estimate_tokens


@dataclass
class ContextResult:
    text: str
    chunks: list[Chunk] = field(default_factory=list)
    tokens: int = 0
    project_distribution: dict[str, int] = field(default_factory=dict)
    citations: list[dict] = field(default_factory=list)


class ContextBuilder:
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def build(self, chunks: list[Chunk], projects: list[str] | None = None) -> ContextResult:
        # 1. 去重
        seen: set[str] = set()
        unique: list[Chunk] = []
        for c in chunks:
            if c.chunk_id not in seen:
                seen.add(c.chunk_id)
                unique.append(c)

        # 2. 项目平衡（仅多项目 compare 查询）
        if projects and len(projects) > 1:
            unique = self._balance_projects(unique, projects)

        # 3. 贪心打包（整 chunk，不截断）
        selected: list[Chunk] = []
        used = 0
        for c in unique:
            cost = estimate_tokens(self._header(c)) + estimate_tokens(c.text) + 4
            if selected and used + cost > self.max_tokens:
                break
            selected.append(c)
            used += cost

        # 4. 组装 + citation
        parts: list[str] = []
        citations: list[dict] = []
        for c in selected:
            parts.append(self._header(c) + "\n\n" + c.text)
            citations.append(self._citation(c))

        dist: dict[str, int] = {}
        for c in selected:
            dist[c.metadata.project] = dist.get(c.metadata.project, 0) + 1

        return ContextResult(
            text="\n\n---\n\n".join(parts),
            chunks=selected,
            tokens=used,
            project_distribution=dist,
            citations=citations,
        )

    def _header(self, c: Chunk) -> str:
        m = c.metadata
        section = " > ".join(m.heading_path) if m.heading_path else "(root)"
        lines = f"L{c.start_line}-{c.end_line}" if c.start_line else "L-"
        return f"[{m.project} | {m.source_path} | {section} | {lines}]"

    def _citation(self, c: Chunk) -> dict:
        m = c.metadata
        return {
            "project": m.project,
            "source_path": m.source_path,
            "source_url": m.source_url,
            "section": " > ".join(m.heading_path) if m.heading_path else None,
            "start_line": c.start_line,
            "end_line": c.end_line,
            "commit_sha": m.commit_sha,
        }

    def _balance_projects(self, chunks: list[Chunk], projects: list[str]) -> list[Chunk]:
        buckets: dict[str, list[Chunk]] = {p: [] for p in projects}
        other: list[Chunk] = []
        for c in chunks:
            if c.metadata.project in buckets:
                buckets[c.metadata.project].append(c)
            else:
                other.append(c)
        queues = [buckets[p] for p in projects]
        if other:
            queues.append(other)
        result: list[Chunk] = []
        while any(queues):
            for q in queues:
                if q:
                    result.append(q.pop(0))
        return result
