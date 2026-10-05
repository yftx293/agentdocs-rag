"""数据契约（单一事实源）。

本模块是整条 RAG 链路的唯一数据结构定义来源。S0 冻结后，任何字段的
增删改都必须先走文档变更流程（docs/DEVELOPMENT_PLAN.md）。

chunk_id 生成规则（S3 实现）：sha1(parent_id + "\\x00" + text)，不用顺序号，
以保证增量索引与重跑时 id 稳定。
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Intent(str, Enum):
    """查询意图（V0 规则版识别，V1 升级为 LLM）。"""

    EXPLAIN = "explain"                # 技术解释
    COMPARE = "compare"                # 项目对比
    ARCHITECTURE = "architecture"      # 架构理解
    IMPLEMENTATION = "implementation"  # 实现参考


class SourceType(str, Enum):
    README = "readme"
    DOCS = "docs"
    DESIGN = "design"
    OTHER = "other"


class DocumentMetadata(BaseModel):
    """一个 Parent Document 的元数据（PRD §8）。必填字段缺一不可。"""

    project: str = Field(description="项目名，如 pi / tau")
    repo: str = Field(description="仓库地址")
    branch: str = Field(default="main")
    commit_sha: str = Field(description="语料快照的 commit，保证可复现")
    source_path: str = Field(description="仓库内相对路径，如 docs/context.md")
    source_url: str = Field(description="可点击的原始来源 URL")
    heading_path: list[str] = Field(
        default_factory=list,
        description="完整标题路径，如 ['Context Management', 'Context Compression']",
    )
    source_type: SourceType = Field(default=SourceType.DOCS)
    language: str = Field(default="en")
    # 建议字段（PRD §8）
    indexed_at: datetime | None = Field(default=None)
    content_hash: str | None = Field(default=None, description="normalized_text 的 SHA256")
    start_line: int | None = Field(default=None)
    end_line: int | None = Field(default=None)


class Document(BaseModel):
    """Parent Document：一个语义自洽的 Markdown Section（约 800–2000 tokens）。"""

    parent_id: str = Field(
        description="稳定 ID，如 pi:docs/context.md:context-compression"
    )
    text: str = Field(description="原始正文（不做标题注入）")
    metadata: DocumentMetadata


class Chunk(BaseModel):
    """Child Chunk：用于检索的小块（300–500 tokens）。小块负责找，大块负责答。"""

    chunk_id: str = Field(description="稳定 ID，sha1(parent_id + text)")
    parent_id: str
    text: str = Field(description="原始文本，展示给用户/模型")
    embedding_text: str = Field(description="标题+项目名注入后的文本，仅用于向量化")
    metadata: DocumentMetadata
    start_line: int | None = None
    end_line: int | None = None
    token_count: int | None = Field(default=None, description="按 embedding tokenizer 计数")


class QueryPlan(BaseModel):
    """查询计划。V0 由规则生成，V1 由 LLM 生成。"""

    intent: Intent
    projects: list[str] = Field(default_factory=list, description="涉及的项目名，用于 metadata filter")
    topic: str | None = Field(default=None, description="主题，如 context_management")
    query: str = Field(description="改写后的检索 query")
    keywords: list[str] = Field(default_factory=list, description="BM25 关键词")


class Citation(BaseModel):
    """最终答案的引用来源（PRD §20）。"""

    project: str
    source_path: str
    source_url: str
    section: str | None = Field(default=None, description="标题路径，如 Context Management > Compression")
    start_line: int | None = None
    end_line: int | None = None
    commit_sha: str | None = None


class RetrievalResult(BaseModel):
    """单条检索结果（含来源阶段与分数，供 trace 与 context builder 使用）。"""

    chunk_id: str
    parent_id: str
    text: str
    metadata: DocumentMetadata
    score: float
    source: str = Field(description="来自哪个检索器：vector / bm25 / rrf / rerank")
    rank: int | None = None


class Answer(BaseModel):
    """最终生成结果。"""

    answer: str
    citations: list[Citation] = Field(default_factory=list)


class TraceStage(BaseModel):
    """链路中单个阶段的观测记录。"""

    name: str
    elapsed_ms: float | None = None
    results: list[RetrievalResult] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class Trace(BaseModel):
    """一次完整 Query 的观测记录（PRD §23）。"""

    trace_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    query: str
    query_plan: QueryPlan | None = None
    stages: list[TraceStage] = Field(default_factory=list)
    final_context: str | None = None
    answer: Answer | None = None
    retrieval_latency_ms: float | None = None
    generation_latency_ms: float | None = None
    total_latency_ms: float | None = None
    token_usage: dict[str, int] = Field(default_factory=dict)
