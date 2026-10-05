"""评测数据集：加载与校验。

红线：本模块只读 data/eval，绝不写入或覆盖 golden 数据。
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from app.core.schemas import Intent


class EvalSample(BaseModel):
    id: str
    intent: Intent
    question: str
    target_projects: list[str] = Field(default_factory=list)
    target_topics: list[str] = Field(default_factory=list)
    expected_sources: list[str] = Field(default_factory=list)

    def expected_source_set(self) -> set[str]:
        return set(self.expected_sources)


def load_dataset(path: Path) -> list[EvalSample]:
    """从 JSONL 加载评测集（只读）。"""
    samples: list[EvalSample] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            samples.append(EvalSample.model_validate_json(line))
    return samples
