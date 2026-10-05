"""配置加载：config/default.yaml + 环境变量覆盖（AGENTDOCS_PROXY 优先级最高）。"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default.yaml"


class DataConfig(BaseModel):
    root: str = "data"
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    eval_dir: str = "data/eval"


class NetworkConfig(BaseModel):
    proxy: str | None = None


class CorpusProject(BaseModel):
    repo: str
    branch: str = "main"
    include: list[str] = Field(default_factory=list, description="要抽取的文档 glob（仓库内相对路径）")
    exclude: list[str] = Field(default_factory=list, description="排除的 glob（优先级高于 include）")


class CorpusConfig(BaseModel):
    projects: dict[str, CorpusProject] = Field(default_factory=dict)


class ChunkingConfig(BaseModel):
    strategy: str = "heading_aware_parent_child"
    parent_min_tokens: int = 800
    parent_max_tokens: int = 2000
    child_target_tokens: int = 400
    child_min_tokens: int = 300
    child_max_tokens: int = 500
    overlap_tokens: int = 50
    max_overlap_ratio: float = 0.15
    heading_only: bool = False


class EmbeddingConfig(BaseModel):
    model: str = "BAAI/bge-m3"
    device: str = "cuda"
    normalize: bool = True
    max_seq_length: int = 8192


class VectorIndexConfig(BaseModel):
    backend: str = "faiss"
    top_n: int = 50


class BM25Config(BaseModel):
    top_n: int = 50
    tokenizer: str = "jieba"


class FusionConfig(BaseModel):
    method: str = "rrf"
    rrf_k: int = 60
    final_top_k: int = 8


class IndexingConfig(BaseModel):
    vector: VectorIndexConfig = Field(default_factory=VectorIndexConfig)
    bm25: BM25Config = Field(default_factory=BM25Config)
    fusion: FusionConfig = Field(default_factory=FusionConfig)


class RetrievalConfig(BaseModel):
    reranker: str = "none"


class GenerationConfig(BaseModel):
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    temperature: float = 0.0


class EvaluationConfig(BaseModel):
    metrics: list[str] = Field(default_factory=lambda: ["hit_at_k", "recall_at_k", "mrr"])
    k_values: list[int] = Field(default_factory=lambda: [3, 5])


class ObservabilityConfig(BaseModel):
    trace_dir: str = "traces"
    format: str = "jsonl"


class Settings(BaseModel):
    data: DataConfig = Field(default_factory=DataConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    corpus: CorpusConfig = Field(default_factory=CorpusConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)


def load_settings(path: Path | None = None) -> Settings:
    cfg_path = path or DEFAULT_CONFIG_PATH
    raw: dict = {}
    if cfg_path.exists():
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    settings = Settings.model_validate(raw)

    # 环境变量覆盖（优先级最高）
    proxy = os.environ.get("AGENTDOCS_PROXY")
    if proxy:
        settings.network.proxy = proxy

    return settings


_settings: Settings | None = None


def get_settings() -> Settings:
    """获取全局单例配置。"""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings
